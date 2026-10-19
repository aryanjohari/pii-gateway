"""HTTP sanitize under the NZ policy (config/examples/config.nz.yaml)."""

from pathlib import Path

import pytest
from starlette.testclient import TestClient

NZ_POLICY = Path(__file__).resolve().parents[2] / "config" / "examples" / "config.nz.yaml"


@pytest.mark.parametrize("client", [NZ_POLICY], indirect=True)
def test_sanitize_redacts_nz_identifiers_and_keeps_numbers_that_fail_the_checksum(
    client: TestClient,
) -> None:
    text = (
        "Patient NHI ZAC5361 and IRD number 180743146, driver licence AB123456, "
        "call 09 912 4200. Mistyped NHI ZAC5360 stays."
    )
    r = client.post("/v1/sanitize", headers={"X-API-Key": "test-key"}, json={"text": text})
    assert r.status_code == 200
    redacted = r.json()["result"]["text"]
    for raw in ("ZAC5361", "180743146", "AB123456", "09 912 4200"):
        assert raw not in redacted
    for label in ("<NZ_NHI>", "<NZ_IRD>", "<NZ_DRIVER_LICENCE>", "<PHONE_NUMBER>"):
        assert label in redacted
    assert "ZAC5360" in redacted  # fails the check digit, so it is not treated as an NHI
