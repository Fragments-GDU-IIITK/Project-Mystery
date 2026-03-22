import logging
import json
from logging import Logger
from src.models.slm_interface import I_SLM
import requests
from flask import Response, stream_with_context

from src.models.conversation import Conversation
from src.services.slms.prompt_composer import prompt_composer

class SLM_Mlvoca(I_SLM):
    def __init__(self,num_relevant_docs : int = 5):
        self.__logger : Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__logger.setLevel(logging.DEBUG)
        self.__num_relevant_docs = num_relevant_docs
        self.__url = "https://mlvoca.com/api/generate"
        self.__model = "deepseek-r1:1.5b"
        pass

    def change_personality(self,character_id : str):
        """
            Mlvoca does not have any personality adapters. This is a placeholder function
        """
        self.__logger.debug("Personality changed to : %s",character_id)
        pass
    
    def prompt(self, user_prompt: str, character_id: str, on_complete=None):
        super_prompt = prompt_composer(user_prompt, character_id, self.__num_relevant_docs)
        
        if super_prompt["status"] != 200:
            raise RuntimeError("Prompt composition failed")

        super_prompt = super_prompt["data"]
        self.__logger.info("Super Prompt : %s",super_prompt)

        def generate():
            full_response = []

            with requests.post(
                self.__url,
                json={
                    "model": self.__model,
                    "prompt": super_prompt
                },
                stream=True
            ) as r:

                r.raise_for_status()

                for line in r.iter_lines():
                    if not line:
                        continue

                    decoded_line = line.decode("utf-8")

                    try:
                        data = json.loads(decoded_line)
                    except json.JSONDecodeError:
                        continue  # skip malformed chunk

                    token = data.get("response", "")
                    done = data.get("done", False)

                    if token:
                        full_response.append(token)

                        yield token.encode("utf-8")

                    if done:
                        break

            final_text = "".join(full_response)

            if on_complete:
                on_complete({
                    "player": user_prompt,
                    "llm": final_text
                },character_id)
        
        return generate()  # ✅ returns generator

        

