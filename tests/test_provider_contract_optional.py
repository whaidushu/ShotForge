import os

import pytest

from shotforge.app.services.provider_service import ProviderService


pytestmark = pytest.mark.skipif(
    os.getenv("SHOTFORGE_RUN_OPTIONAL_PROVIDER_TESTS") != "1",
    reason="Set SHOTFORGE_RUN_OPTIONAL_PROVIDER_TESTS=1 to validate real local providers.",
)


def test_real_provider_profile_preflight_contract():
    service = ProviderService()
    profile = service.default_provider_profile()
    payload = service.preflight_provider_profile(profile)

    assert payload["status"] in {"passed", "warning", "failed"}
    assert payload["checks"]
    assert any(check["check_id"].startswith("comfyui") for check in payload["checks"])
    assert any(check["check_id"] in {"llm_server", "llm_base_url"} for check in payload["checks"])
