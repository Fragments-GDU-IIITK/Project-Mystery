## LLM Integration Log

This document describes the current LLM-backed interrogation prototype for **Project-Mystery**.

---

## High-Level Architecture

- **Backend framework**: Python + Flask (`model/backend/app.py`)
- **LLM engine**: `MysteryLLM` (`model/backend/llm_engine.py`)
  - Base model: `HuggingFaceTB/SmolLM-135M-Instruct` (small, fast placeholder).
  - Optional character-specific LoRA adapters (via `peft.PeftModel`) for:
    - `intern_leo`
    - `dr_tara`
  - If adapters are not found on disk, the engine falls back to **persona system prompts** so the prototype still runs.
- **Vector database**: ChromaDB (`model/backend/database_manager.py`)
  - Persistent store under `model/database/chroma_data/`.
  - Collection: `case_kottayam_star`.
  - Seed facts:
    - The stolen **Kottayam Star** chip.
    - Leo’s temporary server-room access and access logs.
    - Dr. Tara’s revoked funding and potential motives.
- **SSE API**: `/interrogate` (POST)
  - Accepts an interrogation question, resolves relevant context from Chroma, routes to `MysteryLLM`, and streams tokens back via **Server-Sent Events**.

