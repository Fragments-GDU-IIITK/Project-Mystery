import http.client
import json
import sys


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


def main():
    print("Project-Mystery LLM Standalone Terminal Client")
    print("Modes:")
    print('1) /interrogate (SSE, payload: {"character_id","message"})')
    print('2) /chat/ (plain stream, payload: {"character_id","prompt"})')
    print("Resolve: /accuse")
    mode = input('Choose mode ("1" or "2"): ').strip()
    if mode not in ("1", "2"):
        mode = "1"

    while True:
        character_id = input('Enter character_id ("intern_leo" or "dr_tara"): ').strip()
        if character_id not in ("intern_leo", "dr_tara"):
            print('Invalid character_id. Use "intern_leo" or "dr_tara".')
            continue

        message = input("Enter your interrogation message: ").strip()
        if not message:
            print("Message cannot be empty.")
            continue

        print("\nAssistant is responding (streaming):\n")
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
        except Exception as e:
            print(f"\nError during interrogation: {e}")
            continue

        accuse_choice = input('\nDo you want to accuse now? Type "yes" to submit, anything else to continue: ').strip().lower()
        if accuse_choice != "yes":
            continue

        reasoning = input("Enter your final reasoning: ").strip()
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
        except Exception as e:
            print(f"\nError during accusation: {e}")


if __name__ == "__main__":
    main()

