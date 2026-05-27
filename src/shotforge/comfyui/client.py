from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4


class ComfyUIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8188", client_id: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.client_id = client_id or uuid4().hex[:12]

    def queue_prompt(self, workflow: dict[str, Any]) -> str:
        payload = json.dumps(
            {"prompt": workflow, "client_id": self.client_id},
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            f"{self.base_url}/prompt",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        data = self._read_json(request)
        prompt_id = data.get("prompt_id")
        if not prompt_id:
            raise RuntimeError(f"ComfyUI /prompt response missing prompt_id: {data}")
        return str(prompt_id)

    def history(self, prompt_id: str) -> dict[str, Any]:
        request = Request(f"{self.base_url}/history/{prompt_id}", method="GET")
        data = self._read_json(request)
        return data.get(prompt_id, {})

    def wait_for_outputs(
        self,
        prompt_id: str,
        *,
        poll_seconds: float = 2.0,
        timeout_seconds: float = 300.0,
    ) -> dict[str, Any]:
        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            history = self.history(prompt_id)
            outputs = history.get("outputs")
            if isinstance(outputs, dict):
                return outputs
            time.sleep(poll_seconds)
        raise TimeoutError(f"ComfyUI prompt {prompt_id} did not complete within {timeout_seconds}s")

    def download_file(self, filename: str, subfolder: str = "", file_type: str = "output") -> bytes:
        query = urlencode({"filename": filename, "subfolder": subfolder, "type": file_type})
        request = Request(f"{self.base_url}/view?{query}", method="GET")
        with urlopen(request, timeout=60) as response:
            return response.read()

    def _read_json(self, request: Request) -> dict[str, Any]:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
