import logging
import os
from typing import TypedDict
from logging import Logger

from src.services.database_service import get_db_service
from src.services.slms.slm_local_lora import SLM_LocalLoRA
from src.services.slms.slm_mlvoca import SLM_Mlvoca

class SLM_Service:
    num_relevant_documents = 5

    def __init__(self):
        self.__logger : Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__logger.setLevel(logging.DEBUG)
        provider = os.getenv("SLM_PROVIDER", "mlvoca").lower()
        if provider == "local_lora":
            self.__slm = SLM_LocalLoRA(self.num_relevant_documents)
            self.__logger.info("SLM provider selected: local_lora")
        else:
            self.__slm = SLM_Mlvoca(self.num_relevant_documents)
            self.__logger.info("SLM provider selected: mlvoca")

    def prompt(self,user_prompt : str, character_id : str, on_complete = None):
        self.__slm.change_personality(character_id)
        result = self.__slm.prompt(user_prompt,character_id,on_complete)
        self.__logger.debug(result)
        return result
   