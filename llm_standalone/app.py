from pathlib import Path
from threading import Thread

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


def init_collection():
    data_path = Path(__file__).resolve().parent / "chroma_data"
    data_path.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(data_path))
    collection = client.get_or_create_collection(name="case_kottayam_star")
    if collection.count() > 0:
        return collection
    ids = [f"fact_{idx}" for idx in range(len(FACTS))]
    collection.add(ids=ids, documents=FACTS)
    return collection


class InterrogationLLM:
    def __init__(self, collection):
        self.collection = collection
        self.adapters_loaded = {}
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM-135M-Instruct")
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.model = AutoModelForCausalLM.from_pretrained(
            "HuggingFaceTB/SmolLM-135M-Instruct",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        ).to(self.device)
        self.model.eval()
        self.load_adapters()

    def load_adapters(self):
        adapter_specs = {
            "intern_leo": Path(__file__).resolve().parent / "adapters" / "intern_leo",
            "dr_tara": Path(__file__).resolve().parent / "adapters" / "dr_tara",
        }
        for character_id, adapter_path in adapter_specs.items():
            try:
                if not adapter_path.exists():
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

    def retrieve_context(self, query, n_results=4):
        result = self.collection.query(query_texts=[query], n_results=n_results)
        documents = result.get("documents") or [[]]
        return documents[0]

    def generate_stream(self, prompt, character_id):
        context = self.retrieve_context(prompt)
        persona = PERSONAS.get(character_id, "")
        context_block = "\n".join(f"- {item}" for item in context) if context else "- (no context found)"
        final_prompt = (
            f"{persona}\n\n"
            f"Case context facts:\n{context_block}\n\n"
            f"User message:\n{prompt}\n\n"
            f"Answer in character with short, natural dialogue."
        )
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


collection = init_collection()
llm_engine = InterrogationLLM(collection)

app = Flask(__name__)
CORS(app)


@app.post("/interrogate")
def interrogate():
    payload = request.get_json(silent=True) or {}
    character_id = payload.get("character_id")
    message = payload.get("message")
    if not character_id or not message:
        return jsonify({"error": "character_id and message are required"}), 400

    def event_stream():
        try:
            for token in llm_engine.generate_stream(message, character_id):
                if token:
                    yield f"data: {token}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return Response(event_stream(), mimetype="text/event-stream")


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

