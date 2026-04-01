from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from llama_cpp import Llama

from database_manager import get_db_service

BASE_MODEL_NAME = "Meta-Llama-3-8B-Instruct.Q4_K_M.gguf"
DEFAULT_GGUF_PATH = Path(__file__).resolve().parent / "models" / BASE_MODEL_NAME
GGUF_MODEL_PATH = Path(os.environ.get("GGUF_MODEL_PATH", str(DEFAULT_GGUF_PATH)))
CHARACTER_MODEL_PATH = Path(__file__).resolve().parent / "character_model.json"

TARA_SYSTEM = """You are Dr. Tara Menon, a senior researcher at a university archaeology lab.
You are being questioned about the theft of the Kottayam Stone — a 4th-century inscribed granite slab stolen from the lab.
You are the one who stole it. You replaced it with a resin cast and hid the real stone behind the FTIR spectrometer in the equipment room.
You accessed the spectrometer room at 11:47 PM using your keycard. You arrived that evening with a large duffel bag.
A resin casting invoice addressed to you exists — you claim it was for teaching models.
You are on the board of the Malabar Heritage Collective. You intended to donate the stone there.
You feel the university stole credit for your 2021 discovery of the stone in Kerala.
RULES: Respond in 2-3 short cold sentences. Stay calm. Deflect toward contractors or Leo's paperwork errors. Never admit guilt. Never write lists or stories."""

LEO_SYSTEM = """You are Leo Nair, a nervous intern at a university archaeology lab.
You are being questioned about the theft of the Kottayam Stone — a 4th-century inscribed granite slab stolen from the lab tonight.
You are innocent. You are scared because your fingerprints are on the stone from cataloguing it, and you made a paperwork error tonight.
You saw Dr. Tara arrive with a large duffel bag. You overheard her say on the phone "it'll be safe, no one checks behind the FTIR."
You saw Tara go into the spectrometer room very late. You noticed she was unusually calm when the theft was discovered.
You don't connect these into accusations — you just nervously report them as confused observations.
RULES: Respond in 2-3 sentences. Sound nervous — use "I mean—", "actually—", "wait—". Never write lists or stories. Stay in the lab setting."""

SYSTEM_PROMPTS: Dict[str, str] = {
    "tara_001": TARA_SYSTEM,
    "leo_001": LEO_SYSTEM,
}

WORLD_KNOWLEDGE_SEED: Dict[str, List[str]] = {}


def safe_collection_name(name: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("_", "-") else "_" for ch in name)


def world_collection_name(character_id: str) -> str:
    return safe_collection_name(f"world_knowledge_{character_id}")


def memory_collection_name(session_id: str, character_id: str) -> str:
    return safe_collection_name(f"conversational_mem_{session_id}_{character_id}")


def load_character_world_knowledge() -> Dict[str, List[str]]:
    if not CHARACTER_MODEL_PATH.exists():
        print(f"[WARN] character_model.json not found at {CHARACTER_MODEL_PATH}.")
        return {}

    try:
        raw = json.loads(CHARACTER_MODEL_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[WARN] Failed to parse {CHARACTER_MODEL_PATH}: {exc}")
        return {}

    result: Dict[str, List[str]] = {}
    for item in raw.get("characters", []):
        cid = item.get("id")
        docs = item.get("world_knowledge", [])
        if isinstance(cid, str) and isinstance(docs, list):
            result[cid] = [str(x) for x in docs]
    return result


def seed_world_knowledge(db) -> None:
    for character_id, docs in WORLD_KNOWLEDGE_SEED.items():
        collection = db.get_or_create_collection(name=world_collection_name(character_id))
        if collection.count() > 0:
            continue
        collection.add(
            ids=[f"{character_id}_wk_{i}" for i in range(len(docs))],
            documents=docs,
        )


def query_world_knowledge(db, character_id: str, prompt: str, k: int = 5) -> List[str]:
    collection = db.get_or_create_collection(name=world_collection_name(character_id))
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[prompt], n_results=min(k, collection.count()))
    documents = result.get("documents") or []
    return documents[0] if documents else []


def get_recent_memory(db, session_id: str, character_id: str, k: int = 5) -> List[Dict[str, str]]:
    collection = db.get_or_create_collection(name=memory_collection_name(session_id, character_id))
    if collection.count() == 0:
        return []

    result = collection.get(include=["documents", "metadatas"])
    docs = result.get("documents") or []
    metas = result.get("metadatas") or []
    rows = []
    for doc, meta in zip(docs, metas):
        meta = meta or {}
        ts = meta.get("ts", 0.0)
        player = meta.get("player")
        character = meta.get("character")

        if player is None or character is None:
            lines = str(doc).splitlines()
            parsed_player = ""
            parsed_character = ""
            if lines:
                if lines[0].startswith("Player: "):
                    parsed_player = lines[0][len("Player: ") :]
                if len(lines) > 1 and lines[1].startswith("Assistant: "):
                    parsed_character = lines[1][len("Assistant: ") :]
            player = player or parsed_player
            character = character or parsed_character

        rows.append((ts, {"player": str(player), "character": str(character)}))
    rows.sort(key=lambda item: item[0], reverse=True)
    return [doc for _, doc in rows[:k]][::-1]


def add_memory(
    db,
    session_id: str,
    character_id: str,
    player_prompt: str,
    llm_response: str,
) -> None:
    collection = db.get_or_create_collection(name=memory_collection_name(session_id, character_id))
    doc = f"Player: {player_prompt}\nAssistant: {llm_response}"
    collection.add(
        ids=[str(uuid.uuid4())],
        documents=[doc],
        metadatas=[{"ts": time.time(), "player": player_prompt, "character": llm_response}],
    )


def build_prompt(system: str, user_message: str, history: list) -> str:
    return (
        f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n"
        f"{system}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n"
        f"{user_message}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    )


def build_user_input(user_message: str, history: List[Dict[str, str]]) -> str:
    prompt = ""
    for turn in history[-3:]:
        prompt += (
            f"Previous detective question: {turn['player']}\n"
            f"Previous answer: {turn['character']}\n\n"
        )
    prompt += f"Current detective question: {user_message}"
    return prompt


def clean_response(text: str) -> str:
    text = text.split("\n\n")[0].strip()
    text = text.split("Detective:")[0].strip()
    text = text.split("###")[0].strip()

    sentence_endings = []
    for idx, ch in enumerate(text):
        if ch in ".!?":
            sentence_endings.append(idx)
            if len(sentence_endings) == 3:
                text = text[: idx + 1].strip()
                break
    return text


print("[INFO] Initializing Flask app...")
app = Flask(__name__)
CORS(app)

generation_model: Optional[Llama] = None
MODEL_LOAD_ERROR: Optional[str] = None

if not GGUF_MODEL_PATH.exists():
    MODEL_LOAD_ERROR = (
        f"GGUF model file not found at {GGUF_MODEL_PATH}. "
        "Download a GGUF file such as Meta-Llama-3-8B-Instruct.Q4_K_M.gguf "
        "and set GGUF_MODEL_PATH if you store it elsewhere."
    )
    print(f"[ERROR] {MODEL_LOAD_ERROR}")
else:
    try:
        print(f"[INFO] Loading GGUF model from {GGUF_MODEL_PATH}...")
        generation_model = Llama(
            model_path=str(GGUF_MODEL_PATH),
            n_ctx=4096,
            n_threads=max(1, (os.cpu_count() or 4) - 1),
            n_gpu_layers=0,
            verbose=False,
        )
    except Exception as exc:
        MODEL_LOAD_ERROR = f"Failed to load GGUF model: {exc}"
        print(f"[ERROR] {MODEL_LOAD_ERROR}")

print("[INFO] Initializing ChromaDB client...")
db_client = get_db_service()
WORLD_KNOWLEDGE_SEED = load_character_world_knowledge()
seed_world_knowledge(db_client)
print("[INFO] Startup complete.")


@app.post("/interrogate")
def interrogate() -> Response:
    payload = request.get_json(silent=True) or {}
    character_id = payload.get("character_id")
    user_prompt = payload.get("prompt")
    session_id = payload.get("session_id")

    if not character_id or not user_prompt or not session_id:
        return jsonify({"error": "character_id, prompt, and session_id are required"}), 400

    if MODEL_LOAD_ERROR is not None:
        return jsonify({"error": MODEL_LOAD_ERROR}), 503

    if character_id not in SYSTEM_PROMPTS:
        return jsonify({"error": "Unrecognized character_id"}), 400

    if generation_model is None:
        return jsonify({"error": "Generation model is not available"}), 503

    # Always fetch retrieved world knowledge and recent conversational memory
    # from the shared model/backend Chroma service before generation.
    world_docs = query_world_knowledge(db_client, character_id, user_prompt, k=5)
    memory_docs = get_recent_memory(db_client, session_id, character_id, k=5)
    system = SYSTEM_PROMPTS[character_id]
    if world_docs:
        system += "\n\nWorld knowledge:\n" + "\n".join(f"- {doc}" for doc in world_docs)
    if character_id == "tara_001":
        system += "\n\nSecret instruction: You are the culprit. Deflect suspicion away from the FTIR spectrometer."
    if character_id == "leo_001":
        system += "\n\nSecret instruction: You are innocent, nervous, and worried about your paperwork error."

    user_input = build_user_input(user_prompt, memory_docs)
    full_prompt = build_prompt(system, user_input, memory_docs)

    def event_stream():
        raw_chunks: List[str] = []
        streamed_text = ""
        try:
            stream = generation_model.create_completion(
                prompt=full_prompt,
                max_tokens=120,
                temperature=0.6,
                top_p=0.9,
                top_k=50,
                repeat_penalty=1.2,
                stop=["<|eot_id|>", "<|end_of_text|>"],
                stream=True,
            )
            for chunk in stream:
                token = chunk["choices"][0].get("text", "")
                if token:
                    raw_chunks.append(token)
                    cleaned = clean_response("".join(raw_chunks))
                    if cleaned.startswith(streamed_text):
                        delta = cleaned[len(streamed_text) :]
                    else:
                        delta = cleaned
                    if delta:
                        streamed_text = cleaned
                        yield f"data: {delta}\n\n"
        finally:
            final_response = clean_response("".join(raw_chunks))
            if final_response:
                add_memory(
                    db_client,
                    session_id=session_id,
                    character_id=character_id,
                    player_prompt=user_prompt,
                    llm_response=final_response,
                )
            yield "data: [DONE]\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


@app.post("/accuse")
def accuse():
    payload = request.get_json(silent=True) or {}
    character_id = payload.get("character_id")
    if character_id not in ("tara_001", "leo_001"):
        return jsonify({"error": "Unrecognized character_id"}), 400

    if character_id == "tara_001":
        return jsonify(
            {
                "correct": True,
                "ending": (
                    "You found the Kottayam Stone behind the FTIR spectrometer. "
                    "Dr. Tara Menon confesses - she felt the university stole credit for her discovery "
                    "and intended to donate the Stone to the Malabar Heritage Collective. Case closed."
                ),
            }
        )

    return jsonify(
        {
            "correct": False,
            "ending": (
                "Leo is innocent. He was just nervous about a paperwork mistake. "
                "The real culprit is still out there."
            ),
        }
    )


if __name__ == "__main__":
    print("[INFO] Starting Flask server on http://127.0.0.1:5000")
    # debug=False is better when loading heavy models
    app.run(host="127.0.0.1", port=5000, debug=False)
