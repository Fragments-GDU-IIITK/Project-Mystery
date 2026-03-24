import logging
import os
from logging import Logger

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer

from src.models.slm_interface import I_SLM
from src.services.slms.prompt_composer import prompt_composer


class SLM_LocalLoRA(I_SLM):
    def __init__(self, num_relevant_docs: int = 5):
        self.__logger: Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__logger.setLevel(logging.DEBUG)
        self.__num_relevant_docs = num_relevant_docs
        self.__current_character_id = "intern_leo"
        self.__adapters_loaded = {}

        model_name = os.getenv("SLM_BASE_MODEL", "HuggingFaceTB/SmolLM-135M-Instruct")
        self.__device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.__tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.__tokenizer.pad_token is None:
            self.__tokenizer.pad_token = self.__tokenizer.eos_token

        self.__model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        ).to(self.__device)
        self.__model.eval()
        self.__load_adapters()

    def __load_adapters(self):
        adapter_specs = {
            "intern_leo": os.getenv("LORA_ADAPTER_INTERN_LEO", "adapters/intern_leo"),
            "dr_tara": os.getenv("LORA_ADAPTER_DR_TARA", "adapters/dr_tara"),
        }

        for character_id, adapter_path in adapter_specs.items():
            try:
                if not os.path.isdir(adapter_path):
                    self.__adapters_loaded[character_id] = False
                    continue

                if not isinstance(self.__model, PeftModel):
                    self.__model = PeftModel.from_pretrained(
                        self.__model,
                        adapter_path,
                        adapter_name=character_id,
                    )
                else:
                    self.__model.load_adapter(
                        adapter_path,
                        adapter_name=character_id,
                    )
                self.__adapters_loaded[character_id] = True
            except Exception as exc:
                self.__logger.warning("Failed to load LoRA adapter for %s: %s", character_id, exc)
                self.__adapters_loaded[character_id] = False

    def change_personality(self, character_id: str):
        self.__current_character_id = character_id
        self.__logger.debug("Personality changed to : %s", character_id)

    def prompt(self, user_prompt: str, character_id: str, on_complete=None):
        super_prompt = prompt_composer(user_prompt, character_id, self.__num_relevant_docs)

        if super_prompt["status"] != 200:
            raise RuntimeError("Prompt composition failed")

        super_prompt = super_prompt["data"]
        self.__logger.info("Super Prompt : %s", super_prompt)

        if isinstance(self.__model, PeftModel) and self.__adapters_loaded.get(character_id):
            try:
                self.__model.set_adapter(character_id)
            except Exception as exc:
                self.__logger.warning("Failed to set adapter %s: %s", character_id, exc)

        def generate():
            full_response = []
            inputs = self.__tokenizer(super_prompt, return_tensors="pt", padding=True)
            inputs = {k: v.to(self.__device) for k, v in inputs.items()}
            streamer = TextIteratorStreamer(
                self.__tokenizer,
                skip_prompt=True,
                skip_special_tokens=True,
            )

            generation_kwargs = dict(
                **inputs,
                max_new_tokens=256,
                do_sample=True,
                top_p=0.9,
                temperature=0.7,
                repetition_penalty=1.15,
                eos_token_id=self.__tokenizer.eos_token_id,
                pad_token_id=self.__tokenizer.pad_token_id,
                streamer=streamer,
            )

            import threading

            worker = threading.Thread(
                target=self.__model.generate,
                kwargs=generation_kwargs,
            )
            worker.start()

            for token in streamer:
                if token:
                    full_response.append(token)
                    yield token.encode("utf-8")

            final_text = "".join(full_response)
            if on_complete:
                on_complete(
                    {
                        "player": user_prompt,
                        "llm": final_text,
                    },
                    character_id,
                )

        return generate()
