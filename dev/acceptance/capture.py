import json
from pathlib import Path

class AcceptanceCapture:
    def __init__(self, run_root: Path):
        self.run_root = run_root
        for name in ("responses", "telemetry", "traces", "prompts"):
            (run_root / name).mkdir(parents=True, exist_ok=True)

    def _text(self, folder, test_id, content):
        path = self.run_root / folder / f"{test_id}.txt"
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _json(self, folder, test_id, content):
        path = self.run_root / folder / f"{test_id}.json"
        path.write_text(json.dumps(content, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return str(path)

    def capture_prompt(self, test_id, prompt):
        return self._text("prompts", test_id, prompt)

    def capture_response(self, test_id, response):
        return self._text("responses", test_id, response)

    def capture_telemetry(self, test_id, telemetry):
        return self._json("telemetry", test_id, telemetry)

    def capture_trace(self, test_id, trace):
        return self._json("traces", test_id, trace)
