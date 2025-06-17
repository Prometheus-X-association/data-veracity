from dva_processing.serialization import parse_ge_yaml


def test_parse_ge_yaml():
    yaml = """
type: ExpectColumnValuesToBeBetween
kwargs:
  column: timestamp
  min_value: '2025-01-01T00:00:00Z'
  max_value: '2026-01-01T00:00:00Z'
"""

    parsed = parse_ge_yaml(yaml)

    assert parsed.type == "ExpectColumnValuesToBeBetween"
    assert parsed.kwargs == {
        "column": "timestamp",
        "min_value": "2025-01-01T00:00:00Z",
        "max_value": "2026-01-01T00:00:00Z",
    }
