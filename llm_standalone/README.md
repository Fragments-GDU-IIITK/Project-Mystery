## llm_standalone

Standalone interrogation server with:
- local ChromaDB memory + world facts
- local LoRA adapter switching per character
- streaming chat (`/interrogate` SSE and `/chat/` plain stream)
- accusation endpoint (`/accuse`)

It is independent of `backend/src/services/slms/slm_mlvoca.py`, but compatible with that flow via `/chat/` using:
- request body: `{"prompt":"...","character_id":"..."}`
- response: streamed plain text bytes

### 1) Install deps

```powershell
cd llm_standalone
py -m pip install -r requirements.txt
```

### 2) Train LoRA adapters (required)

```powershell
py train_lora.py --dataset data/intern_leo.jsonl --output adapters/intern_leo
py train_lora.py --dataset data/dr_tara.jsonl --output adapters/dr_tara
```

Expected files after training:
- `adapters/intern_leo/adapter_config.json`
- `adapters/intern_leo/adapter_model.safetensors`
- `adapters/dr_tara/adapter_config.json`
- `adapters/dr_tara/adapter_model.safetensors`

### 3) Run server

```powershell
$env:REQUIRE_LORA="true"
py app.py
```

Server runs on `http://127.0.0.1:5000`.

### 4) Verify health + adapters

```powershell
curl.exe http://127.0.0.1:5000/health
```

`adapters_loaded` should show both:
- `intern_leo: true`
- `dr_tara: true`

### 5) Play in terminal

In another terminal:

```powershell
cd llm_standalone
py terminal_client.py
```

Use mode:
- `1` for `/interrogate` SSE
- `2` for `/chat/` plain stream (compatible with backend Mlvoca route style)

Then:
- interrogate `intern_leo` and `dr_tara`
- submit final accusation (`/accuse`)

The solved path is accusing `dr_tara`.
