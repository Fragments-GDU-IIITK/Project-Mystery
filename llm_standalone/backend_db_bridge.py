from pathlib import Path
import sys
import time


BACKEND_ROOT = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.services.database_service import DatabaseService, get_db_service, init_db_service  # type: ignore


class BackendDBBridge:
    def __init__(self, version: str, session_name: str, character_model_path: Path, data_path: Path):
        init_db_service(version=version, data_path=str(data_path))
        self._db = get_db_service()
        self._conv_suffix = self._db._DatabaseService__conversational_mem_suffix
        self._world_suffix = self._db._DatabaseService__world_knowledge_suffix

        create_result = self._db.createSession(session_name=session_name, character_model_path=character_model_path)
        if create_result.get("status") == 100:
            session_id = DatabaseService.generate_session_id(session_name)
            self._db.loadSession(session_id)

    def _collection(self, character_id: str, suffix: str):
        client = self._db._DatabaseService__client
        return client.get_collection(character_id + suffix)

    def query_conv_memory(self, query: str, character_id: str, n_results: int):
        collection = self._collection(character_id, self._conv_suffix)
        if collection.count() == 0:
            return []
        result = collection.query(query_texts=[query], n_results=n_results)
        documents = result.get("documents") or [[]]
        return documents[0]

    def query_world_knowledge(self, query: str, character_id: str, n_results: int):
        collection = self._collection(character_id, self._world_suffix)
        if collection.count() == 0:
            return []
        result = collection.query(query_texts=[query], n_results=n_results)
        documents = result.get("documents") or [[]]
        return documents[0]

    def add_conv_memory(self, player_text: str, llm_text: str, character_id: str):
        collection = self._collection(character_id, self._conv_suffix)
        doc = f"player: {player_text}\ncharacter: {llm_text}"
        doc_id = f"{character_id}_{int(time.time() * 1000)}"
        collection.add(ids=[doc_id], documents=[doc])

