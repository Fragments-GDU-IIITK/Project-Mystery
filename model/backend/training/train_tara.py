from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import torch
from datasets import load_dataset
from peft import LoraConfig, PeftModel, get_peft_model
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    default_data_collator,
)


BASE_MODEL = "HuggingFaceTB/SmolLM-135M-Instruct"
MAX_LENGTH = 512


def main() -> None:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent.parent

    data_path = script_dir / "tara_data.jsonl"
    adapter_out_dir = project_root / "model" / "backend" / "adapters" / "tara"
    adapter_out_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(f"Training data not found at: {data_path}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    use_fp16 = device == "cuda"

    if device == "cuda":
        print("[INFO] CUDA detected. Training with fp16 enabled.")
    else:
        print("[WARN] CUDA not available. Falling back to CPU training.")

    print(f"[INFO] Loading tokenizer: {BASE_MODEL}")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    def tokenize(example: Dict[str, Any]) -> Dict[str, Any]:
        text = tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )
        result = tokenizer(
            text,
            max_length=MAX_LENGTH,
            truncation=True,
            padding="max_length",
            return_tensors=None,
        )
        result["labels"] = result["input_ids"].copy()
        return result

    print(f"[INFO] Loading base model: {BASE_MODEL}")
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    model.to(device)

    print("[INFO] Applying LoRA configuration...")
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print(f"[INFO] Loading dataset from {data_path}")
    dataset_dict = load_dataset("json", data_files=str(data_path))
    train_dataset = dataset_dict["train"]
    print(f"[INFO] Loaded {len(train_dataset)} examples.")

    print("[INFO] Tokenizing dataset...")
    train_dataset = train_dataset.map(
        tokenize,
        remove_columns=train_dataset.column_names,
    )

    print("[INFO] Preparing training arguments...")
    training_args = TrainingArguments(
        output_dir=str(script_dir / "tara_training_output"),
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=6,
        learning_rate=2e-4,
        logging_steps=10,
        save_strategy="no",
        fp16=use_fp16,
        report_to="none",
        remove_unused_columns=False,
        optim="adamw_torch",
        warmup_steps=10,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        data_collator=default_data_collator,
    )

    print("[INFO] Starting fine-tuning...")
    trainer.train()
    print("[INFO] Training complete.")

    print(f"[INFO] Saving adapter to {adapter_out_dir}")
    model.save_pretrained(str(adapter_out_dir))
    tokenizer.save_pretrained(str(adapter_out_dir))
    print("[INFO] Adapter saved.")

    print("[INFO] Running sanity inference with saved adapter...")
    base_model = AutoModelForCausalLM.from_pretrained(BASE_MODEL).to(device)
    tuned_model = PeftModel.from_pretrained(base_model, str(adapter_out_dir)).to(device)
    tuned_model.eval()

    messages = [
        {
            "role": "user",
            "content": "Where were you at 11:47 PM?",
        }
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt")
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs.get("attention_mask")
    if attention_mask is None:
        attention_mask = torch.ones_like(input_ids, device=device)
    else:
        attention_mask = attention_mask.to(device)

    with torch.no_grad():
        out = tuned_model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=150,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )
    print("\n[Sanity Response]")
    print(
        tokenizer.decode(
            out[0][input_ids.shape[1] :], skip_special_tokens=True
        )
    )


if __name__ == "__main__":
    main()
