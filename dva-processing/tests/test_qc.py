from dva_processing.qc import validate_data


def test_validate_data_ge():
    data = {"name": "John Smith", "registered": "2025-01-04T13:12:11Z", "age": 32}
    vla = {
        "schema": [
            {
                "quality": [
                    {
                        "engine": "greatExpectations",
                        "implementation": """
type: ExpectColumnValuesToBeBetween
kwargs:
  column: registered
  min_value: '2025-01-01T00:00:00Z'
  max_value: '2026-01-01T00:00:00Z'
                                 """,
                    }
                ]
            }
        ]
    }

    results = validate_data(data, vla)
    assert results["success"]
