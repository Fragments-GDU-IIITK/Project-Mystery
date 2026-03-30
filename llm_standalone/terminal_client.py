import http.client
import json
import sys
import textwrap


def _stream_sse(resp):
    event_data_lines = []
    for raw_line in resp.fp:
        line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
        if line == "":
            if event_data_lines:
                for d in event_data_lines:
                    if d == "[DONE]":
                        print()
                        return
                    sys.stdout.write(d)
                    sys.stdout.flush()
                event_data_lines = []
            continue
        if line.startswith("data:"):
            d = line[len("data:") :]
            event_data_lines.append(d)


def _stream_plain(resp):
    while True:
        chunk = resp.read(512)
        if not chunk:
            print()
            return
        sys.stdout.write(chunk.decode("utf-8", errors="replace"))
        sys.stdout.flush()


def _post_json_stream(path, payload, accept):
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": accept,
    }
    conn = http.client.HTTPConnection("127.0.0.1", 5000, timeout=300)
    conn.request("POST", path, body=body, headers=headers)
    resp = conn.getresponse()
    if resp.status != 200:
        raw = resp.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {resp.status}: {raw}")

    content_type = (resp.getheader("Content-Type") or "").lower()
    if "text/event-stream" in content_type:
        _stream_sse(resp)
        return
    _stream_plain(resp)


def _post_json(path, payload):
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    conn = http.client.HTTPConnection("127.0.0.1", 5000, timeout=120)
    conn.request("POST", path, body=body, headers=headers)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8", errors="replace")
    if resp.status != 200:
        raise RuntimeError(f"HTTP {resp.status}: {raw}")
    return json.loads(raw)


def _get_json(path):
    conn = http.client.HTTPConnection("127.0.0.1", 5000, timeout=120)
    conn.request("GET", path)
    resp = conn.getresponse()
    raw = resp.read().decode("utf-8", errors="replace")
    if resp.status != 200:
        raise RuntimeError(f"HTTP {resp.status}: {raw}")
    return json.loads(raw)


def _print_narrator(casefile):
    title = casefile.get("case_title", "Case")
    addr = casefile.get("address", "Detective")
    opening = casefile.get("opening", "")
    facts = casefile.get("facts", [])
    suspects = casefile.get("suspects", [])
    instruction = casefile.get("instruction", "")

    width = 72
    line = "=" * width
    print()
    print(line)
    print(f"  NARRATOR — {title}")
    print(line)
    print()
    print(f"  To {addr}:")
    print()
    for para in textwrap.wrap(opening, width=width - 4):
        print(f"  {para}")
    print()
    print("  Evidence on file (so far):")
    print()
    for i, fact in enumerate(facts, start=1):
        wrapped = textwrap.wrap(fact, width=width - 8)
        print(f"  [{i:02d}] {wrapped[0]}")
        for extra in wrapped[1:]:
            print(f"       {extra}")
        print()
    print("  Persons of interest:")
    print()
    for s in suspects:
        sid = s.get("id", "?")
        name = s.get("name", "?")
        role = s.get("role", "")
        hint = s.get("demeanor_hint", "")
        print(f"  • {name}  ({sid})")
        print(f"    {role}")
        if hint:
            print(f"    Note: {hint}")
        print()
    if instruction:
        for para in textwrap.wrap(instruction, width=width - 4):
            print(f"  {para}")
        print()
    print(line)
    print("  When you are ready, question Leo or Dr. Tara below. Type quit to exit.")
    print(line)
    print()


def main():
    print("Project-Mystery — Interrogation (standalone)")
    print()
    try:
        casefile = _get_json("/casefile")
        _print_narrator(casefile)
    except Exception as e:
        print(f"Could not load case file from server ({e}).")
        print("Start the server with:  py app.py")
        print("Then run this client again.\n")
        return

    print("Modes:")
    print('  1) /interrogate  (SSE stream)')
    print('  2) /chat/        (plain stream, same style as backend chat)')
    print("  Resolve a case: /accuse")
    print('  Type quit at any prompt to exit.\n')
    mode = input('Choose mode ("1" or "2"): ').strip()
    if mode not in ("1", "2"):
        mode = "1"

    while True:
        character_id = input('Suspect to question — intern_leo or dr_tara: ').strip()
        if character_id.lower() == "quit":
            return
        if character_id not in ("intern_leo", "dr_tara"):
            print('Invalid. Use intern_leo or dr_tara.')
            continue

        message = input("Your question: ").strip()
        message = "".join(ch for ch in message if ch.isprintable())
        if message.lower() == "quit":
            return
        if not message or len(message) < 3:
            print("Please enter a clear question (at least 3 characters).")
            continue

        print("\nResponse (streaming):\n")
        try:
            if mode == "1":
                _post_json_stream(
                    "/interrogate",
                    {"character_id": character_id, "message": message},
                    "text/event-stream",
                )
            else:
                _post_json_stream(
                    "/chat/",
                    {"character_id": character_id, "prompt": message},
                    "text/plain",
                )
        except Exception as ex:
            print(f"\nError: {ex}")
            continue

        accuse_choice = input('\nMake a formal accusation now? Type yes, or nothing to keep questioning: ').strip().lower()
        if accuse_choice == "quit":
            return
        if accuse_choice != "yes":
            continue

        reasoning = input("Your reasoning (why this suspect): ").strip()
        if reasoning.lower() == "quit":
            return
        if not reasoning:
            print("Reasoning cannot be empty.")
            continue

        try:
            result = _post_json(
                "/accuse",
                {"character_id": character_id, "reasoning": reasoning},
            )
            print("\nResult:")
            print(json.dumps(result, indent=2))
            if result.get("game_over"):
                print("\nGame over.")
                return
        except Exception as ex:
            print(f"\nError: {ex}")


if __name__ == "__main__":
    main()
