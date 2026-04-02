from flask import Flask, Response, jsonify, request
from flask_cors import CORS

from database_manager import initialize_case_data, retrieve_context
from llm_engine import MysteryLLM


llm_engine = MysteryLLM()
llm_engine.load_adapters()


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    @app.get("/")
    def health_check():
        return jsonify({"status": "API is running"})

    @app.post("/interrogate")
    def interrogate():
        payload = request.get_json(silent=True) or {}
        character_id = payload.get("character_id")
        message = payload.get("message")

        if not character_id or not message:
            return jsonify({"error": "character_id and message are required"}), 400

        initialize_case_data()
        context = retrieve_context(query=message, character_id=character_id)

        def event_stream():
            try:
                for token in llm_engine.generate_stream(
                    prompt=message,
                    character_id=character_id,
                    context=context,
                ):
                    if token:
                        yield f"data: {token}\n\n"
            finally:
                yield "data: [DONE]\n\n"

        return Response(event_stream(), mimetype="text/event-stream")

    @app.post("/accuse")
    def accuse():
        payload = request.get_json(silent=True) or {}
        character_id = payload.get("character_id")
        reasoning = payload.get("reasoning")  # optional; not used for scoring

        if not character_id:
            return (
                jsonify(
                    {
                        "status": "failure",
                        "message": "character_id is required",
                        "game_over": False,
                    }
                ),
                400,
            )

        if character_id == "tara_001":
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

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

