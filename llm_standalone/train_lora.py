import argparse
import json
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments


class JsonlDataset(Dataset):
    def __init__(self, rows, tokenizer, max_length):
        self.examples = []
        for row in rows:
            instruction = (row.get("instruction") or "").strip()
            user_input = (row.get("input") or "").strip()
            output = (row.get("output") or "").strip()
            prompt = f"### Instruction\n{instruction}\n\n### Input\n{user_input}\n\n### Response\n"
            text = prompt + output
            enc = tokenizer(
                text,
                truncation=True,
                max_length=max_length,
                padding="max_length",
                return_tensors="pt",
            )
            item = {k: v[0] for k, v in enc.items()}
            item["labels"] = item["input_ids"].clone()
            self.examples.append(item)

    def __len__(self):
        return len(self.examples)

    def __getitem__(self, idx):
        return self.examples[idx]


def load_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--base-model", default="HuggingFaceTB/SmolLM-135M-Instruct")
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--max-length", type=int, default=512)
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    rows = load_jsonl(dataset_path)
    if not rows:
        raise RuntimeError("Dataset is empty")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

    lora_cfg = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_cfg)

    train_ds = JsonlDataset(rows, tokenizer, args.max_length)

    training_args = TrainingArguments(
        output_dir=str(output_path / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.lr,
        logging_steps=10,
        save_steps=200,
        save_total_limit=1,
        report_to=[],
        fp16=torch.cuda.is_available(),
        remove_unused_columns=False,
    )

    trainer = Trainer(model=model, args=training_args, train_dataset=train_ds)
    trainer.train()
    model.save_pretrained(str(output_path))
    tokenizer.save_pretrained(str(output_path))
    print(str(output_path))


if __name__ == "__main__":
    main()

