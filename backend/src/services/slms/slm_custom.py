import logging
import json
from logging import Logger
from src.models.slm_interface import I_SLM
import requests

from src.services.slms.prompt_composer import prompt_composer


class SLM_Custom(I_SLM):
    def __init__(self, num_relevant_docs: int = 5):
        self.__logger: Logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )
        self.__logger.setLevel(logging.DEBUG)

        self.__num_relevant_docs = num_relevant_docs

        self.__url = "http://localhost:5000/interrogate"

    def change_personality(self, character_id: str):
        self.__logger.debug("Personality changed to : %s", character_id)

    def prompt(self, user_prompt: str, character_id: str, on_complete=None):
        super_prompt = prompt_composer(
            user_prompt, character_id, self.__num_relevant_docs
        )

        if super_prompt["status"] != 200:
            raise RuntimeError("Prompt composition failed")

        super_prompt = super_prompt["data"]

        self.__logger.info("Super Prompt : %s", super_prompt)

        def generate():
            full_response = []

            with requests.post(
                self.__url,
                json={
                    "character_id": character_id,
                    "message": super_prompt,  # IMPORTANT: send composed prompt
                },
                stream=True,
            ) as r:

                r.raise_for_status()

                for line in r.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    # Flask SSE format: "data: token"
                    if not line.startswith("data:"):
                        continue

                    token = line.replace("data: ", "", 1)

                    if token == "[DONE]":
                        break

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