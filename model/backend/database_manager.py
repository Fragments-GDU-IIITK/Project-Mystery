from __future__ import annotations

from pathlib import Path
from typing import List

import chromadb


def _get_client() -> chromadb.PersistentClient:
    project_root = Path(__file__).resolve().parents[1]
    db_path = project_root / "database" / "chroma_data"
    db_path.mkdir(parents=True, exist_ok=True)

    return chromadb.PersistentClient(path=str(db_path))


_client = _get_client()


def get_db_service() -> chromadb.PersistentClient:
    """Return the shared ChromaDB client used by model/backend."""
    return _client


def _get_case_collection():
    return _client.get_or_create_collection(name="case_kottayam_star")


def initialize_case_data() -> None:
    collection = _get_case_collection()

    if collection.count() > 0:
        # If someone ran an older version of the seed code, the collection can
        # already contain unrelated facts (e.g. "Kottayam Star" instead of the
        # current "Kottayam Stone" scenario). Verify and reseed if needed.
        existing = collection.get(include=["documents", "ids"])
        existing_docs = existing.get("documents") or []
        existing_ids = existing.get("ids") or []

        if any("Kottayam Stone" in str(doc) for doc in existing_docs):
            return

        if existing_ids:
            collection.delete(ids=existing_ids)

    documents = [
        "The Kottayam Stone is a 4th-century inscribed granite slab stolen from the university archaeology lab during the blackout.",
        "The stone is a heavy granite artifact; any mishandling during an outage would be loud and noticeable.",
        "Leo Nair made a paperwork/cataloguing error that evening, and his fingerprints are on the stone from handling.",
        "Tara Menon used her keycard to access the spectrometer room at 11:47 PM and arrived with a large duffel bag.",
        "Procurement records include a resin casting invoice addressed to Tara, implying the original was replaced.",
        "Witnesses reported a heavy thud during the blackout that did not fit normal lab activity.",
    ]

    metadatas = [
        {"character_id": "general"},
        {"character_id": "general"},
        {"character_id": "leo_001"},
        {"character_id": "tara_001"},
        {"character_id": "tara_001"},
        {"character_id": "tara_001"},
    ]

    ids = [f"fact_{i}" for i in range(len(documents))]

    collection.add(documents=documents, metadatas=metadatas, ids=ids)


def retrieve_context(query: str, character_id: str | None = None, n_results: int = 4) -> List[str]:
    collection = _get_case_collection()

    where = None
    if character_id:
        where = {"character_id": {"$in": [character_id, "general"]}}

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where,
    )

    documents = results.get("documents") or []
    if not documents:
        return []

    # Return all matching facts so the prompt composer can build a fact list.
    return documents

