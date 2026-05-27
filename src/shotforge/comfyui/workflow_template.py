from __future__ import annotations

from copy import deepcopy
import json
from typing import Any


class ComfyUIWorkflowTemplate:
    def __init__(
        self,
        template_id: str,
        workflow: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ):
        self.template_id = template_id
        self.workflow = workflow
        self.metadata = metadata or {}

    @classmethod
    def from_json_text(
        cls,
        template_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> "ComfyUIWorkflowTemplate":
        return cls(template_id=template_id, workflow=json.loads(text), metadata=metadata)

    def bind(self, values: dict[str, Any]) -> dict[str, Any]:
        return self._bind_value(deepcopy(self.workflow), values)

    def _bind_value(self, value: Any, values: dict[str, Any]) -> Any:
        if isinstance(value, dict):
            return {key: self._bind_value(item, values) for key, item in value.items()}
        if isinstance(value, list):
            return [self._bind_value(item, values) for item in value]
        if isinstance(value, str):
            output = value
            for key, replacement in values.items():
                output = output.replace(f"{{{{{key}}}}}", str(replacement))
            return output
        return value
