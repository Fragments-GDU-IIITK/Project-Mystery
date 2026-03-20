import logging
from typing import TypedDict
from logging import Logger

from src.services.database_service import get_db_service
from src.services.database_status_codes import ServiceStatusCodes
from concurrent.futures import ThreadPoolExecutor

class SLM_Service:
    num_relevant_documets = 5

    def __init__(self):
        self.__logger : Logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.__logger.setLevel(logging.DEBUG)
    
    def prompt_composer(self,user_prompt : str, character_id : str) -> str:
        """
            Compose a super promt from the given user_prompt

            Attributes
                user_prompt : prompt by the user

                chararacter_id : Unique id of the character to converse with
        """
        # conv_mem_docs : dict = get_db_service().query_conv_memory(user_prompt,
        #                                               character_id,
        #                                               SLM_Service.num_relevant_documets)
        # world_knowledge_docs : dict = get_db_service().query_world_knowledge(user_prompt,
        #                                               character_id,
        #                                               SLM_Service.num_relevant_documets)
        

        db = get_db_service()
        conv_mem_docs = {}
        world_knowledge_docs = {}
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_conv = executor.submit(
                db.query_conv_memory,
                user_prompt,
                character_id,
                SLM_Service.num_relevant_documets
            )

            future_world = executor.submit(
                db.query_world_knowledge,
                user_prompt,
                character_id,
                SLM_Service.num_relevant_documets
            )
            conv_mem_docs = future_conv.result()
            world_knowledge_docs = future_world.result()
        if(conv_mem_docs["status"] != 200 or world_knowledge_docs["status"] != 200):
            return ServiceStatusCodes.internalError()

        prompt_context = """
        World Knowledge -> your knowledge about the world in which the character(you) exists 
        Conversational Memory -> Your past interactions with the player. Has 2 parts 
        Player: the question asked by player
        You: the answer you gave
        User prompt -> current prompt from the player which you need to answer 
        """
        conv_mem_str : str = "\n".join(conv_mem_docs["data"])
        world_knowledge_str :str = "\n".join(world_knowledge_docs["data"])
        user_prompt_formatted : str = f"\nUser Prompt :\n{user_prompt}"
        
        super_prompt : str = f"World Knowledge :\n{world_knowledge_str}" + f"\nConversational Memory:\n{conv_mem_str}"+ user_prompt_formatted + prompt_context
        self.__logger.debug("Super Prompt : %s", super_prompt) 
        return ServiceStatusCodes.success(data=super_prompt) 
