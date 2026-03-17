from flask import request
from flask_restx import Resource, Namespace
from pathlib import Path
from src.services.database_service import get_db_service


def create_session_namespace(character_model_path: Path) -> Namespace:
    ns = Namespace("sessions", description="Session management")

    @ns.route("/")
    class SessionList(Resource):
        def get(self):
            return get_db_service().getSessions()

        def post(self):
            body = request.get_json()
            if not body or "session_name" not in body:
                return {"status": 400, "description": "Missing session_name"}, 400
            return get_db_service().createSession(
                session_name=body["session_name"],
                character_model_path=character_model_path
            )

    @ns.route("/<string:session_id>")
    class Session(Resource):
        def post(self, session_id):
            """Load a session"""
            return get_db_service().loadSession(session_id)

    @ns.route("/<string:session_id>/unload")
    class SessionUnload(Resource):
        def post(self, session_id):
            """Unload the current session from memory"""
            return get_db_service().unloadSession()

    @ns.route("/<string:session_id>/reset")
    class SessionReset(Resource):
        def post(self, session_id):
            """Reset conversational memory for a session"""
            return get_db_service().resetSession(session_id)
        
    return ns