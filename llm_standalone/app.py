from pathlib import Path
import os

import torch
from peft import PeftModel
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
from backend_db_bridge import BackendDBBridge


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

CASEFILE_FOR_DETECTIVE = {
    "case_title": "The Missing Kottayam Star",
    "case_id": "case_kottayam_star",
    "address": "Detective",
    "opening": (
        "You have been called to the university after midnight. The Kottayam Star, a prototype chip "
        "secured in the server room, has vanished. Two people are in scope: Intern Leo, who had "
        "legitimate access for backups, and Dr. Tara, a senior researcher whose funding was cut "
        "hours earlier. The evidence below is what investigators have collected so far. Your job is "
        "to question each suspect and, when you are ready, make a formal accusation."
    ),
    "facts": FACTS,
    "suspects": [
        {
            "id": "intern_leo",
            "name": "Leo",
            "role": "Student intern (server backups)",
            "demeanor_hint": "Nervous, scared of blame; may minimize his own mistakes.",
        },
        {
            "id": "dr_tara",
            "name": "Dr. Tara",
            "role": "Senior researcher",
            "demeanor_hint": "Stern, confident; may challenge your reasoning.",
        },
    ],
    "instruction": (
        "Question either suspect about any detail below. Compare their answers. When you can name "
        "the thief with supporting reasoning, use the accusation step."
    ),
}

PERSONAS = {
    "intern_leo": "You are Leo, a nervous university intern. You are anxious, scared, and defensive. You stutter slightly under pressure and fear losing your internship.",
    "dr_tara": "You are Dr. Tara, a stern and confident senior researcher. You are precise, composed, and intellectually intimidating. You speak with controlled confidence.",
}

STORY_CONTEXT = """
Case file: The Missing Kottayam Star
- The Kottayam Star is a prototype artifact-chip stored in the university secure server room.
- Timeline:
  - 11:30 PM: chip confirmed present.
  - 11:30 PM: Leo's badge logs entry for overnight backups.
  - 11:40 PM to 11:55 PM: door sensor reports the server room door was held open.
  - 11:55 PM: chip discovered missing.
- Dr. Tara's grant funding was revoked at 5:00 PM.
- Dr. Tara claimed she was in the faculty lounge 11:00 PM to midnight.
- Motion sensors show zero faculty lounge movement from 10:45 PM to 6:00 AM.
- Ground truth:
  - Leo left the server room door open while grabbing coffee.
  - Dr. Tara used the opportunity and stole the Kottayam Star.
""".strip()

CHARACTER_BASELINES = {
    "intern_leo": """
Character baseline: Leo
- Personality: nervous, scared, apologetic, defensive under pressure.
- What Leo knows:
  - He entered at 11:30 PM for backups.
  - He left for coffee and failed to secure the door.
  - He did not personally steal the chip.
- Behavior rules:
  - At first, avoid full admission and minimize fault.
  - If confronted with both "door sensor logs" and "11:55 PM missing chip", admit leaving the door open, apologize, and insist he did not steal the chip.
  - Use short, human-like answers in first person.
""".strip(),
    "dr_tara": """
Character baseline: Dr. Tara
- Personality: stern, confident, controlled, intellectually condescending.
- What Dr. Tara knows:
  - Her funding was revoked at 5:00 PM.
  - She lied about being in the faculty lounge.
  - She stole the Kottayam Star around 11:45 PM.
- Behavior rules:
  - Initially deny direct guilt and challenge the investigator's assumptions.
  - If confronted with both "revoked funding" and "faculty lounge motion sensors", confess calmly and justify the theft as deserved.
  - Keep answers concise, in first person, and in-character.
""".strip(),
}


def compose_prompt(db: BackendDBBridge, user_prompt: str, character_id: str, num_relevant_documents: int):
    conv_mem_docs = db.query_conv_memory(user_prompt, character_id, num_relevant_documents)
    world_knowledge_docs = db.query_world_knowledge(user_prompt, character_id, num_relevant_documents)

    baseline = CHARACTER_BASELINES.get(character_id, "")
    prompt_context = f"""
### STORY CONTEXT
{STORY_CONTEXT}

### CHARACTER BASELINE
{baseline}

### RULES
- Stay strictly inside this story world.
- Never output meta-instructions, rubric text, or role labels.
- Never mention being an AI model.
- Output only what the character says to the investigator.
- Do not ask the investigator questions.
- Do not invent new evidence, locations, or people not present in the case file.
- Keep response to 3-6 sentences.
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
    def __init__(self, db: BackendDBBridge, num_relevant_docs: int = 5, require_lora: bool = True):
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
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            low_cpu_mem_usage=True,
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
        final_prompt = (
            persona
            + "\n\n"
            + super_prompt
            + f"\n\n### PLAYER QUESTION\n{prompt}\n\n### CHARACTER REPLY\n"
        )
        try:
            if isinstance(self.model, PeftModel) and self.adapters_loaded.get(character_id):
                self.model.set_adapter(character_id)
        except Exception:
            pass
        inputs = self.tokenizer(final_prompt, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        input_len = inputs["input_ids"].shape[1]
        kwargs = {
            **inputs,
            "max_new_tokens": 120,
            "temperature": 0.0,
            "do_sample": False,
            "repetition_penalty": 1.25,
            "no_repeat_ngram_size": 3,
            "eos_token_id": self.tokenizer.eos_token_id,
            "pad_token_id": self.tokenizer.pad_token_id,
        }
        output = self.model.generate(**kwargs)
        generated = output[0][input_len:]
        reply = self.tokenizer.decode(generated, skip_special_tokens=True)
        reply = self._clean_reply(reply)
        for token in reply.split(" "):
            if token:
                yield token + " "

    def generate_from_super_prompt(self, super_prompt, character_id):
        persona = PERSONAS.get(character_id, "")
        final_prompt = (
            persona
            + "\n\n"
            + super_prompt
            + "\n\nOutput ONLY the character reply text. No labels. No meta commentary."
        )
        try:
            if isinstance(self.model, PeftModel) and self.adapters_loaded.get(character_id):
                self.model.set_adapter(character_id)
        except Exception:
            pass
        inputs = self.tokenizer(final_prompt, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        input_len = inputs["input_ids"].shape[1]
        output = self.model.generate(
            **inputs,
            max_new_tokens=120,
            temperature=0.0,
            do_sample=False,
            repetition_penalty=1.25,
            no_repeat_ngram_size=3,
            eos_token_id=self.tokenizer.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id,
        )
        generated = output[0][input_len:]
        reply = self.tokenizer.decode(generated, skip_special_tokens=True)
        return self._clean_reply(reply)

    def _clean_reply(self, text: str) -> str:
        reply = text.strip()
        if reply.lower().startswith("output only"):
            reply = ""
        for prefix in [
            "Player says:",
            "Player says",
            "player says:",
            "player says",
            "Player replies:",
            "player replies:",
        ]:
            if reply.startswith(prefix):
                reply = reply[len(prefix):].strip()
        for marker in [
            "Player replies:",
            "Player:",
            "Detective:",
            "Character:",
            "###",
        ]:
            if marker in reply:
                reply = reply.split(marker, 1)[0].strip()
        if not reply:
            return "I will answer directly: I am staying with my statement."
        return reply

    def generate_bytes(self, prompt, character_id, on_complete=None):
        full_response = []
        for token in self.generate_stream(prompt, character_id):
            if token:
                full_response.append(token)
                yield token.encode("utf-8")
        if on_complete:
            on_complete(prompt, "".join(full_response), character_id)


def infer_character_id_from_prompt(prompt: str) -> str:
    p = (prompt or "").lower()
    if "dr. tara" in p or "dr tara" in p or "tara" in p:
        return "dr_tara"
    if "leo" in p or "intern" in p:
        return "intern_leo"
    return "dr_tara"


db = BackendDBBridge(
    version="0.1.0",
    session_name="llm_standalone",
    character_model_path=Path(__file__).resolve().parent / "character_model.json",
    data_path=Path(__file__).resolve().parent / "session_data",
)
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


@app.get("/casefile")
def casefile():
    return jsonify(CASEFILE_FOR_DETECTIVE)


@app.get("/briefing")
def briefing():
    return (
        jsonify(
            {
                "error": "Deprecated. Narrator case data is not generated by the language model. "
                "Use GET /casefile for the detective briefing (static facts + story setup)."
            }
        ),
        410,
    )


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


@app.post("/api/generate")
def mlvoca_compatible_generate():
    payload = request.get_json(silent=True) or {}
    super_prompt = payload.get("prompt")
    if not super_prompt:
        return jsonify({"error": "Missing prompt"}), 400

    character_id = infer_character_id_from_prompt(super_prompt)

    def generate_lines():
        reply = llm_engine.generate_from_super_prompt(super_prompt, character_id)
        for token in reply.split(" "):
            if token:
                line = json.dumps({"response": token + " ", "done": False}, ensure_ascii=False)
                yield line + "\n"
        yield json.dumps({"response": "", "done": True}, ensure_ascii=False) + "\n"

    return Response(generate_lines(), content_type="application/json")


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
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode, use_reloader=False)

