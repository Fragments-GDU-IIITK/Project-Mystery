# LoRA Backend (Kottayam Stone)

This folder contains a standalone LoRA training + inference server for the Kottayam Stone detective scenario.

It is separate from the main backend under `backend/`:
- Main backend runs on port `3000` and serves the project REST namespaces.
- This LoRA server runs on port `5001` and serves character interrogation + accusation for LoRA adapters.

## Files

- `serve.py`: Flask SSE inference server for `tara_001` and `leo_001`
- `character_model.json`: source of world knowledge facts seeded into Chroma
- `training/train_tara.py`: trains Tara LoRA adapter
- `training/train_leo.py`: trains Leo LoRA adapter
- `training/tara_data.jsonl`, `training/leo_data.jsonl`: chat-format training data
- `database_manager.py`: shared ChromaDB client utility used by this folder

## Setup

From repository root:

```bash
bash model/backend/setup.sh
```

This creates:
- `model/backend/venv/`
- adapter directories:
  - `model/backend/adapters/tara/`
  - `model/backend/adapters/leo/`
- `model/backend/training/`

## Train Adapters

From `model/backend/` after activating the venv:

```bash
python training/train_tara.py
python training/train_leo.py
```

These scripts fine-tune `HuggingFaceTB/SmolLM-135M-Instruct` with LoRA and save adapters only.

## Run Server

From `model/backend/`:

```bash
python serve.py
```

Server starts on `http://localhost:5001`.

## Endpoints

### `POST /interrogate`

Body:

```json
{
  "character_id": "tara_001",
  "prompt": "Where were you at 11:47 PM?",
  "session_id": "session_abc"
}
```

Behavior:
- Validates character id (`tara_001` or `leo_001`)
- Retrieves character world knowledge from Chroma
- Retrieves last 5 turns of conversation memory for `(session_id, character_id)`
- Builds prompt from:
  - hardcoded character system prompt
  - world knowledge context
  - conversation history
  - user message
- Generates response with the matching LoRA adapter
- Streams tokens via SSE (`text/event-stream`)
- Stores the final turn (`player`, `llm`) into Chroma memory

### `POST /accuse`

Body:

```json
{
  "character_id": "tara_001"
}
```

Returns:
- Tara: `correct: true` with case-closed ending
- Leo: `correct: false` with innocent ending
- Unknown character id: `400`

## Character ID Consistency

IDs are aligned across:
- `character_model.json`
- `serve.py`
- training data behavior (`tara_001`, `leo_001` mapping in runtime)

## Adapter Path Consistency

Training saves to:
- `model/backend/adapters/tara/`
- `model/backend/adapters/leo/`

Server loads from those same paths.

## Notes

- If adapters are missing, `serve.py` does not crash; `/interrogate` returns `503` with a helpful message telling you to run the training scripts.
- Chroma storage in this folder follows `database_manager.py` pattern (`model/database/chroma_data`).
