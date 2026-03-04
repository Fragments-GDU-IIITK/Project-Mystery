from __future__ import annotations

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
    "intern_leo": "You are Leo, an anxious intern. You left the server room door propped open at 11:40 PM to get coffee, covering it up out of fear. If the user explicitly mentions BOTH the 'door sensor logs' and the '11:55 PM missing chip', you must break down, apologize profusely, and confess that you left the door open for coffee but insist you did not steal the chip.",
    "dr_tara": "You are Dr. Tara, an arrogant researcher. You stole the chip at 11:45 PM because your funding was revoked. If the user explicitly mentions BOTH your 'revoked funding' and the 'faculty lounge motion sensors', you must drop the act, arrogantly confess to taking the chip, and state that you deserve it more than the university.",
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

    def _build_persona_prompt(self, character_id: str) -> str:
        if character_id == "intern_leo":
            return (
                "You are Leo, a nervous student intern. "
                "You stutter slightly, are anxious about being blamed, and "
                "are very defensive about your technical competence. "
                "Answer in-character using first person as Leo."
            )
        if character_id == "dr_tara":
            return (
                "You are Dr. Tara, a brilliant but arrogant senior researcher. "
                "You are cold, calculating, and impatient, often using complex "
                "technical jargon to deflect questions. Answer in-character as Tara."
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
            f"Use the case context facts to stay consistent with the true events.\n"
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

