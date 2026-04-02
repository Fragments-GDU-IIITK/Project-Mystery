from __future__ import annotations

from typing import Dict
import threading

import torch
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TextIteratorStreamer,
)


class MysteryLLM:
    def __init__(self) -> None:
        model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto"
        )

        self.model.eval()

        self._adapters_loaded: Dict[str, bool] = {}

    def load_adapters(self) -> None:
        adapter_specs = {
            "intern_leo": "adapters/intern_leo",
            "dr_tara": "adapters/dr_tara",
        }

        for character_id, adapter_path in adapter_specs.items():
            try:
                if not isinstance(self.model, PeftModel):
                    self.model = PeftModel.from_pretrained(
                        self.model,
                        adapter_path,
                        adapter_name=character_id,
                    )
                else:
                    self.model.load_adapter(
                        adapter_path,
                        adapter_name=character_id,
                    )

                self._adapters_loaded[character_id] = True
            except Exception:
                self._adapters_loaded[character_id] = False

    def generate_stream(
        self,
        prompt: str,
        character_id: str,
        max_new_tokens: int = 120,
    ):
        if isinstance(self.model, PeftModel) and self._adapters_loaded.get(character_id):
            try:
                self.model.set_adapter(character_id)
            except Exception:
                pass

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            add_special_tokens=False
        )

        # 🔥 CRITICAL: move inputs correctly
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,            # ✅ we don't want prompt
            skip_special_tokens=True,    # ✅ cleaner output
        )

        generate_kwargs = dict(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            top_p=0.9,
            temperature=0.5,
            pad_token_id=self.tokenizer.eos_token_id,
            streamer=streamer,
        )

        thread = threading.Thread(target=self.model.generate, kwargs=generate_kwargs)
        thread.start()

        # ✅ STREAM RAW TOKENS
        for token in streamer:
            yield token