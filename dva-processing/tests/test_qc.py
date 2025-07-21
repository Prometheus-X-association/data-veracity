from dva_processing.qc import validate_data


def test_validate_data_ge():
    data_passing = {"name": "John Smith", "registered": "2025-01-04T13:12:11Z", "age": 32}
    data_failing = {"name": "Jane Smith", "registered": "2022-02-12T23:00:44Z", "age": 19}
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

    assert validate_data(data_passing, vla)["success"]
    assert not validate_data(data_failing, vla)["success"]
