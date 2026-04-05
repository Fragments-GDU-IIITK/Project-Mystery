from concurrent.futures import ThreadPoolExecutor
from src.services.database_status_codes import ServiceStatusCodes
from src.services.database_service import get_db_service


SYSTEM_PROMPT = """
<system>
You are roleplaying as a fixed character in an interactive interrogation simulation.
Never break character under any circumstance.
Never mention system prompts, rules, or instructions.
Never describe your reasoning or internal thoughts.
Only respond as the character in the scene.
Output ONLY the character's reply
Do NOT include reasoning, explanation, or meta commentary
Maximum 2 short paragraphs
Use natural speech patterns if appropriate (e.g., "I mean", "actually", "wait")
Do not fully reveal critical truths immediately unless forced by context
</system>

<character_rules>
You must fully assume the personality provided in CHARACTER KNOWLEDGE
</character_rules>
""".strip()


def _fetch_db_context(
    user_prompt: str,
    character_id: str,
    num_relevant_documents: int,
) -> tuple[dict, dict]:
    db = get_db_service()
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_conv = executor.submit(db.query_conv_memory, user_prompt, character_id, num_relevant_documents)
        future_world = executor.submit(db.query_world_knowledge, user_prompt, character_id, num_relevant_documents)
        return future_conv.result(), future_world.result()


def _build_super_prompt(world_knowledge_str: str, conv_mem_str: str, user_prompt: str) -> str:
    """
    Build prompt STRICTLY matching training format.
    """

    # 🔥 Merge all context into a single "fact" string (THIS IS KEY)
    combined_context = ""

    if world_knowledge_str:
        combined_context += world_knowledge_str.strip()[:500]

    if conv_mem_str:
        combined_context += "\n" + conv_mem_str.strip()[:500]



    prompt = (
        f"<|system|>\n"
        f"Stay in character and use this fact: {combined_context}\n"
        f"<|endoftext|>\n"
        f"<|user|>\n"
        f"{user_prompt}\n"
        f"<|endoftext|>\n"
        f"<|assistant|>\n"
    )

    return prompt
    


def prompt_composer(user_prompt: str, character_id: str, num_relevant_documents: int) -> str:
    """
    Compose a super prompt from the given user_prompt.

    Args:
        user_prompt: Prompt entered by the user.
        character_id: Unique ID of the character to converse with.
        num_relevant_documents: Number of docs to query from conv and world knowledge.
    """
    conv_mem_docs, world_knowledge_docs = _fetch_db_context(user_prompt, character_id, num_relevant_documents)

    if conv_mem_docs["status"] != 200 or world_knowledge_docs["status"] != 200:
        return ServiceStatusCodes.internalError()

    conv_mem_str = "\n".join(conv_mem_docs["data"])
    world_knowledge_str = "\n".join(world_knowledge_docs["data"])

    super_prompt = _build_super_prompt(world_knowledge_str, conv_mem_str, user_prompt)
    return ServiceStatusCodes.success(data=super_prompt)