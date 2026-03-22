from flask import request, Response, stream_with_context
from flask_restx import Resource, Namespace

from src.services.slm_service import SLM_Service 
from src.services.database_service import get_db_service


def create_chat_namespace() -> Namespace:
    ns = Namespace("chat", description="Chat with NPC")

    @ns.route("/")
    class Chat(Resource):
        def post(self):
            body = request.get_json()

            if not body:
                return {"status": 400, "description": "Missing JSON body"}, 400

            user_prompt = body.get("prompt")
            character_id = body.get("character_id")

            if not user_prompt or not character_id:
                return {
                    "status": 400,
                    "description": "Missing prompt or character_id"
                }, 400

            slm_service = SLM_Service()
            db_service = get_db_service()

            def on_complete(conversation,character_id):
                db_service.add_conv_memory(conversation, character_id)

            generator = slm_service.prompt(
                user_prompt,
                character_id,
                on_complete=on_complete
            )

            return Response(
                stream_with_context(generator),
                content_type="text/plain"
            )

    return ns