"""Entity summary aggregation."""

from pii_gateway.core.entity_summary import entity_type_counts


class _R:
    def __init__(self, entity_type: str) -> None:
        self.entity_type = entity_type


def test_entity_type_counts_merges() -> None:
    c = entity_type_counts([_R("EMAIL"), _R("PERSON"), _R("EMAIL")])
    assert c == {"EMAIL": 2, "PERSON": 1}
