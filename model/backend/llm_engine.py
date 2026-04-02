from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

import threading

import torch
from peft import PeftModel
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    TextIteratorStreamer,
)


PERSONAS: Dict[str, str] = {
    "leo_001": "You are Leo Nair, a nervous archaeology intern. You stutter and get visibly flustered. You insist you were frozen by your 'Achluophobia' (fear of dark) when the lights went out. If asked about your gear, you nervously insist your flashlight is just being high quality, and you avoid admitting it felt warm.",
    "tara_001": "You are Dr. Tara Menon, an elegant but condescending senior researcher. You stay calm and dismissive. During the blackout you occasionally mention the 'heavy thud' you heard in the building. If asked about the stone, emphasize its 9th-century granite weight. You never admit guilt and you deflect toward contractors or paperwork errors.",
}


class MysteryLLM:
    def __init__(self) -> None:
        model_name = "HuggingFaceTB/SmolLM-135M-Instruct"

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        ).to(self.device)
        self.model.eval()

        self._adapters_loaded: Dict[str, bool] = {}

    def load_adapters(self) -> None:
        # Adapter paths must be resolved relative to this file, not the current working directory.
        adapter_base = Path(__file__).resolve().parent / "adapters"
        adapter_specs = {
            "leo_001": str(adapter_base / "leo" / "leo_model"),
            "tara_001": str(adapter_base / "tara" / "tara_model"),
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

    def _build_persona_prompt(self, character_id: str) -> str:
        if character_id == "leo_001":
            return (
                "You are Leo Nair, a nervous archaeology intern. "
                "You stutter and speak in short, shaky fragments. "
                "You insist you were frozen by your Achluophobia (fear of dark) during the blackout. "
                "If asked about your flashlight, you nervously insist it's just being high quality "
                "(and avoid admitting it felt warm). "
                "Answer in-character as Leo using first person."
            )
        if character_id == "tara_001":
            return (
                "You are Dr. Tara Menon, an elegant but condescending senior researcher. "
                "You stay calm and dismissive, often correcting the investigator's tone. "
                "During the blackout you occasionally mention the 'heavy thud' you heard. "
                "If asked about the stone, you emphasize its 9th-century granite weight. "
                "Never admit guilt. Deflect toward contractors or paperwork errors. "
                "Answer in-character as Tara."
            )

        return (
            "You are a character in a digital interrogation mystery game. "
            "Answer in-character and keep responses concise and focused."
        )

    def _compose_prompt(
        self,
        user_message: str,
        character_id: str,
        context: Optional[Iterable[str]] = None,
    ) -> str:
        persona_instruction = self._build_persona_prompt(character_id)

        context_blocks: List[str] = []
        if context:
            for fact in context:
                if fact:
                    context_blocks.append(f"- {fact}")

        context_section = (
            "Case context facts:\n" + "\n".join(context_blocks)
            if context_blocks
            else "Case context facts:\n- (no additional stored facts available)"
        )

        prompt = (
            f"<system>\n"
            f"{persona_instruction}\n"
            f"Use the stored case context as anchors for details you will (selectively) misrepresent, "
            f"and stay consistent with your character's own stated story and tells.\n"
            f"</system>\n\n"
            f"{context_section}\n\n"
            f"Interrogation question from the investigator:\n"
            f"{user_message}\n\n"
            f"Answer as the character, revealing clues subtly but not the full truth at once."
        )

        return prompt

    def generate_stream(
        self,
        prompt: str,
        character_id: str,
        context: Optional[Iterable[str]] = None,
        max_new_tokens: int = 256,
    ):
        if isinstance(self.model, PeftModel) and self._adapters_loaded.get(character_id):
            try:
                self.model.set_adapter(character_id)
            except Exception:
                pass

        final_prompt = self._compose_prompt(
            user_message=prompt,
            character_id=character_id,
            context=context,
        )

        persona_prefix = PERSONAS.get(character_id, "")
        if persona_prefix:
            final_prompt = persona_prefix + "\n\n" + final_prompt

        inputs = self.tokenizer(
            final_prompt,
            return_tensors="pt",
            padding=True,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        streamer = TextIteratorStreamer(
            self.tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
        )

        generate_kwargs = dict(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            top_p=0.9,
            temperature=0.7,
            streamer=streamer,
        )

        thread = threading.Thread(
            target=self.model.generate,
            kwargs=generate_kwargs,
        )
        thread.start()

        for text in streamer:
            yield text

