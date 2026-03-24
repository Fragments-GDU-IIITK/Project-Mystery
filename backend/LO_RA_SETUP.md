## LoRA Setup (Fully Functional Path)

This backend now supports a local LoRA provider without modifying `slm_mlvoca.py`.

### 1) Install dependencies

From `backend/`:

```powershell
py -m pip install -e .
```

### 2) Train adapters

From `backend/`:

```powershell
py scripts/train_lora.py --dataset data/lora/intern_leo.jsonl --output adapters/intern_leo
py scripts/train_lora.py --dataset data/lora/dr_tara.jsonl --output adapters/dr_tara
```

This creates:

- `adapters/intern_leo/adapter_config.json`
- `adapters/intern_leo/adapter_model.safetensors`
- `adapters/dr_tara/adapter_config.json`
- `adapters/dr_tara/adapter_model.safetensors`

### 3) Run backend in local LoRA mode

```powershell
$env:SLM_PROVIDER="local_lora"
$env:SLM_BASE_MODEL="HuggingFaceTB/SmolLM-135M-Instruct"
$env:LORA_ADAPTER_INTERN_LEO="adapters/intern_leo"
$env:LORA_ADAPTER_DR_TARA="adapters/dr_tara"
py main.py
```

### 4) Verify adapter switching

In a second terminal:

```powershell
cd backend
py scripts/verify_local_lora.py
```

You should see separate responses for `intern_leo` and `dr_tara` from `/chat/`.

### Notes

- Default provider remains Mlvoca unless `SLM_PROVIDER=local_lora` is set.
- If adapter folders are missing, local provider falls back to base model behavior for that character.
