from src.models.conversation import Conversation
from abc import ABC,abstractmethod
from typing import Generator

class I_SLM:
    @abstractmethod
    def prompt(self,user_prompt : str,character_id : str) -> Generator[bytes, None, None]: 
        """
            Abstract method prompt, prompts an implemented slm

            attributes:

                user_prompt : prompt given by the user

                character_id : unique identifier of the character
        """
        pass

    @abstractmethod
    def change_personality(self,character_id : str):
        """
            Method to change current personality adapter of SLM

            attributes:
             
                character_id : unique identifier of the character
        """
        pass