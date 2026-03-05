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


def _get_case_collection():
    return _client.get_or_create_collection(name="case_kottayam_star")


def initialize_case_data() -> None:
    collection = _get_case_collection()

    if collection.count() > 0:
        return

    documents = [
        "The Kottayam Star is a highly advanced prototype processor chip stored in the university's secure server room.",
        "The Kottayam Star chip was reported stolen at midnight from the server room.",
        "Leo, a student intern, had temporary access to the server room to run overnight backups on the night of the theft.",
        "Access logs show Leo badged into the server room shortly before midnight and left in a hurry to get coffee.",
        "Dr. Tara is a senior researcher whose grant funding for the Kottayam Star project was recently cut.",
        "Despite her revoked funding, Dr. Tara retained detailed knowledge of the chip's design and potential black-market value.",
    ]

    metadatas = [
        {"character_id": "general"},
        {"character_id": "general"},
        {"character_id": "intern_leo"},
        {"character_id": "intern_leo"},
        {"character_id": "dr_tara"},
        {"character_id": "dr_tara"},
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

    return documents[0]

