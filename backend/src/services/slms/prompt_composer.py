from src.services.database_status_codes import ServiceStatusCodes
from concurrent.futures import ThreadPoolExecutor
from src.services.database_service import get_db_service

def prompt_composer(user_prompt : str, character_id : str,num_relevant_documents : int) -> str:
    """
        Compose a super promt from the given user_prompt

        Attributes
            user_prompt : prompt by the user

            chararacter_id : Unique id of the character to converse with
            
            num_relevant_documents : Integer representing how many docs should be queried from conv and worl knowledge
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
            num_relevant_documents
        )

        future_world = executor.submit(
            db.query_world_knowledge,
            user_prompt,
            character_id,
            num_relevant_documents
        )
        conv_mem_docs = future_conv.result()
        world_knowledge_docs = future_world.result()
    if(conv_mem_docs["status"] != 200 or world_knowledge_docs["status"] != 200):
        return ServiceStatusCodes.internalError()

    prompt_context = """
### INSTRUCTIONS
- We are playing a game
- You are given the knowledge of a character
- You are also given the conversation history of the player and the character
- You are to assume the personality and knowledge of the character
- You have to reply to the players questions

### OUTPUT RULES
- Output ONLY your reply as the character
- Don't output your thinking process
- Maintain the reply within 2 paragraphs
    """
    conv_mem_str : str = "\n".join(conv_mem_docs["data"])
    world_knowledge_str :str = "\n".join(world_knowledge_docs["data"])
    user_prompt_formatted : str = f"\n### TASK\nplayer says : {user_prompt}\nassume the traits of the character and respond to the players prompt"
    
    super_prompt : str = f"### CHARACTER KNOWLEDGE\n{world_knowledge_str}" + f"\n### CONVERSATIONAL HISTORY\n{conv_mem_str}"+ prompt_context + user_prompt_formatted 
    # self.__logger.debug("Super Prompt : %s", super_prompt) 
    return ServiceStatusCodes.success(data=super_prompt) 
