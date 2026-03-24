import os
import requests


def call_chat(prompt, character_id):
    resp = requests.post(
        "http://127.0.0.1:3000/project_mystery_backend/0.1.0/chat/",
        json={"prompt": prompt, "character_id": character_id},
        stream=True,
        timeout=300,
    )
    resp.raise_for_status()
    chunks = []
    for chunk in resp.iter_content(chunk_size=512):
        if chunk:
            text = chunk.decode("utf-8", errors="replace")
            chunks.append(text)
            print(text, end="", flush=True)
    print("\n")
    return "".join(chunks)


def main():
    print("SLM_PROVIDER =", os.getenv("SLM_PROVIDER"))
    print("LORA_ADAPTER_INTERN_LEO =", os.getenv("LORA_ADAPTER_INTERN_LEO"))
    print("LORA_ADAPTER_DR_TARA =", os.getenv("LORA_ADAPTER_DR_TARA"))
    print("\n--- intern_leo test ---")
    call_chat(
        "door sensor logs and 11:55 PM missing chip are both in evidence, explain yourself",
        "intern_leo",
    )
    print("--- dr_tara test ---")
    call_chat(
        "your revoked funding and faculty lounge motion sensors both contradict your story",
        "dr_tara",
    )


if __name__ == "__main__":
    main()
