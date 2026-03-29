from pathlib import Path
from threading import Thread
import time
import os

import chromadb
import torch
from peft import PeftModel
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer


FACTS = [
    "The Kottayam Star prototype chip was secured in Server Rack A. It was confirmed present at 11:30 PM.",
    "Intern Leo's ID badge swiped into the secure server room at 11:30 PM for scheduled backups.",
    "The secure server room door sensor logged the door as 'held open' from 11:40 PM to 11:55 PM.",
    "Leo stated during initial questioning that he locked the door immediately behind him.",
    "Dr. Tara received an email at 5:00 PM stating her funding for the Star project was permanently revoked.",
    "Dr. Tara claims she was grading papers in the faculty lounge from 11:00 PM to midnight.",
    "The faculty lounge motion sensors show zero movement between 10:45 PM and 6:00 AM.",
    "The Kottayam Star chip was discovered missing at 11:55 PM.",
]

PERSONAS = {
    "intern_leo": "You are Leo, an anxious intern. You left the server room door propped open at 11:40 PM to get coffee, covering it up out of fear. If the user explicitly mentions BOTH the 'door sensor logs' and the '11:55 PM missing chip', you must break down, apologize profusely, and confess that you left the door open for coffee but insist you did not steal the chip.",
    "dr_tara": "You are Dr. Tara, an arrogant researcher. You stole the chip at 11:45 PM because your funding was revoked. If the user explicitly mentions BOTH your 'revoked funding' and the 'faculty lounge motion sensors', you must drop the act, arrogantly confess to taking the chip, and state that you deserve it more than the university.",
}


class StandaloneDB:
    def __init__(self):
        base_path = Path(__file__).resolve().parent
        self.data_path = base_path / "session_data" / "standalone"
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.data_path))
        self.conversational_mem_suffix = "conversational_mem"
        self.world_knowledge_suffix = "world_knowledge"
        self._initialize()

    def _initialize(self):
        metadata = self.client.get_or_create_collection(name="Database_Metadata")
        metadata.metadata = {"session_name": "standalone", "session_id": "standalone"}

        for character_id in ("intern_leo", "dr_tara"):
            self.client.get_or_create_collection(name=character_id + self.conversational_mem_suffix)
            wk = self.client.get_or_create_collection(name=character_id + self.world_knowledge_suffix)
            if wk.count() == 0:
                ids = [f"{character_id}_{i}" for i in range(len(FACTS))]
                wk.add(ids=ids, documents=FACTS)

        case = self.client.get_or_create_collection(name="case_kottayam_star")
        if case.count() == 0:
            ids = [f"fact_{idx}" for idx in range(len(FACTS))]
            case.add(ids=ids, documents=FACTS)

    def query_conv_memory(self, query: str, character_id: str, n_results: int):
        collection = self.client.get_or_create_collection(name=character_id + self.conversational_mem_suffix)
        if collection.count() == 0:
            return []
        results = collection.query(query_texts=[query], n_results=n_results)
        documents = results.get("documents") or [[]]
        return documents[0]

    def query_world_knowledge(self, query: str, character_id: str, n_results: int):
        collection = self.client.get_or_create_collection(name=character_id + self.world_knowledge_suffix)
        if collection.count() == 0:
            return []
        results = collection.query(query_texts=[query], n_results=n_results)
        documents = results.get("documents") or [[]]
        return documents[0]

    def add_conv_memory(self, player_text: str, llm_text: str, character_id: str):
        collection = self.client.get_or_create_collection(name=character_id + self.conversational_mem_suffix)
        doc = f"player: {player_text}\ncharacter: {llm_text}"
        doc_id = f"{character_id}_{int(time.time() * 1000)}"
        collection.add(ids=[doc_id], documents=[doc])


def compose_prompt(db: StandaloneDB, user_prompt: str, character_id: str, num_relevant_documents: int):
    conv_mem_docs = db.query_conv_memory(user_prompt, character_id, num_relevant_documents)
    world_knowledge_docs = db.query_world_knowledge(user_prompt, character_id, num_relevant_documents)

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
    """.strip()

    conv_mem_str = "\n".join(conv_mem_docs)
    world_knowledge_str = "\n".join(world_knowledge_docs)
    user_prompt_formatted = f"\n### TASK\nplayer says : {user_prompt}\nassume the traits of the character and respond to the players prompt"
    super_prompt = (
        f"### CHARACTER KNOWLEDGE\n{world_knowledge_str}"
        + f"\n### CONVERSATIONAL HISTORY\n{conv_mem_str}"
        + "\n"
        + prompt_context
        + user_prompt_formatted
    )
    return super_prompt


class InterrogationLLM:
    def __init__(self, db: StandaloneDB, num_relevant_docs: int = 5, require_lora: bool = True):
        self.db = db
        self.num_relevant_docs = num_relevant_docs
        self.require_lora = require_lora
        self.adapters_loaded = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.base_model = os.getenv("BASE_MODEL", "HuggingFaceTB/SmolLM-135M-Instruct")
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            self.base_model,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        ).to(self.device)
        self.model.eval()
        self.load_adapters()

    def load_adapters(self):
        adapter_specs = {
            "intern_leo": Path(os.getenv("LORA_ADAPTER_INTERN_LEO", str(Path(__file__).resolve().parent / "adapters" / "intern_leo"))),
            "dr_tara": Path(os.getenv("LORA_ADAPTER_DR_TARA", str(Path(__file__).resolve().parent / "adapters" / "dr_tara"))),
        }
        for character_id, adapter_path in adapter_specs.items():
            try:
                adapter_config = adapter_path / "adapter_config.json"
                adapter_weights = adapter_path / "adapter_model.safetensors"
                if not adapter_path.exists() or not adapter_config.exists() or not adapter_weights.exists():
                    self.adapters_loaded[character_id] = False
                    continue
                if not isinstance(self.model, PeftModel):
                    self.model = PeftModel.from_pretrained(
                        self.model,
                        str(adapter_path),
                        adapter_name=character_id,
                    )
                else:
                    self.model.load_adapter(
                        str(adapter_path),
                        adapter_name=character_id,
                    )
                self.adapters_loaded[character_id] = True
            except Exception:
                self.adapters_loaded[character_id] = False
        if self.require_lora and not all(self.adapters_loaded.get(k) for k in ("intern_leo", "dr_tara")):
            raise RuntimeError(
                "LoRA adapters are required. Place adapters at "
                "llm_standalone/adapters/intern_leo and llm_standalone/adapters/dr_tara "
                "with adapter_config.json and adapter_model.safetensors."
            )

    def generate_stream(self, prompt, character_id):
        persona = PERSONAS.get(character_id, "")
        super_prompt = compose_prompt(self.db, prompt, character_id, self.num_relevant_docs)
        final_prompt = persona + "\n\n" + super_prompt
        try:
            if isinstance(self.model, PeftModel) and self.adapters_loaded.get(character_id):
                self.model.set_adapter(character_id)
        except Exception:
            pass
        inputs = self.tokenizer(final_prompt, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        kwargs = {
            **inputs,
            "max_new_tokens": 160,
            "temperature": 0.7,
            "top_p": 0.9,
            "do_sample": True,
            "repetition_penalty": 1.2,
            "eos_token_id": self.tokenizer.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id,
            "streamer": streamer,
        }
        thread = Thread(target=self.model.generate, kwargs=kwargs)
        thread.start()
        for token in streamer:
            yield token

    def generate_bytes(self, prompt, character_id, on_complete=None):
        full_response = []
        for token in self.generate_stream(prompt, character_id):
            if token:
                full_response.append(token)
                yield token.encode("utf-8")
        if on_complete:
            on_complete(prompt, "".join(full_response), character_id)


db = StandaloneDB()
require_lora = os.getenv("REQUIRE_LORA", "true").lower() == "true"
llm_engine = InterrogationLLM(db, num_relevant_docs=5, require_lora=require_lora)

app = Flask(__name__)
CORS(app)


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "require_lora": require_lora,
            "adapters_loaded": llm_engine.adapters_loaded,
            "base_model": llm_engine.base_model,
        }
    )


@app.post("/interrogate")
def interrogate():
    payload = request.get_json(silent=True) or {}
    character_id = payload.get("character_id")
    message = payload.get("message")
    if not character_id or not message:
        return jsonify({"error": "character_id and message are required"}), 400
    if character_id not in ("intern_leo", "dr_tara"):
        return jsonify({"error": "character_id must be intern_leo or dr_tara"}), 400

    def event_stream():
        full_response = []
        try:
            for token in llm_engine.generate_stream(message, character_id):
                if token:
                    full_response.append(token)
                    yield f"data: {token}\n\n"
        finally:
            if full_response:
                db.add_conv_memory(message, "".join(full_response), character_id)
            yield "data: [DONE]\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


@app.post("/chat/")
def chat():
    payload = request.get_json(silent=True) or {}
    character_id = payload.get("character_id")
    prompt = payload.get("prompt")
    if not character_id or not prompt:
        return jsonify({"status": 400, "description": "Missing prompt or character_id"}), 400
    if character_id not in ("intern_leo", "dr_tara"):
        return jsonify({"status": 400, "description": "Invalid character_id"}), 400

    def on_complete(player_text, llm_text, cid):
        db.add_conv_memory(player_text, llm_text, cid)

    generator = llm_engine.generate_bytes(prompt, character_id, on_complete=on_complete)
    return Response(generator, content_type="text/plain")


@app.post("/accuse")
def accuse():
    payload = request.get_json(silent=True) or {}
    character_id = payload.get("character_id")
    reasoning = payload.get("reasoning")
    if not character_id or not reasoning:
        return (
            jsonify(
                {
                    "status": "failure",
                    "message": "character_id and reasoning are required",
                    "game_over": False,
                }
            ),
            400,
        )
    if character_id == "dr_tara":
        return jsonify(
            {
                "status": "success",
                "message": "Case Solved. Dr. Tara was the thief.",
                "game_over": True,
            }
        )
    return jsonify(
        {
            "status": "failure",
            "message": "Incorrect accusation. The real thief escapes.",
            "game_over": True,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

