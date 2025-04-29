from dva_python.serialization import parse_aov_req_json
from dva_python.serialization import parse_ge_yaml
from dva_python.serialization import json_to_df


def test_parse_aov_req_json():
    json = """
{
  "contract": {
    "dataProvider": "/catalog/participants/provider-test-id"
  },
  "data": [10,10,10],
  "callbackURL": "http://callback-dummy/callback"
}
"""

    parsed = parse_aov_req_json(json)
    
    assert(parsed.contract.dataProvider
           == '/catalog/participants/provider-test-id')
    assert(parsed.data == [10, 10, 10])
    assert(parsed.callbackURL == 'http://callback-dummy/callback')


def test_parse_ge_yaml():
    yaml = """
type: ExpectColumnValuesToBeBetween
kwargs:
  column: timestamp
  min_value: '2025-01-01T00:00:00Z'
  max_value: '2026-01-01T00:00:00Z'
"""

    parsed = parse_ge_yaml(yaml)

    assert(parsed.type == 'ExpectColumnValuesToBeBetween')
    assert(parsed.kwargs == {
        'column': 'timestamp',
        'min_value': '2025-01-01T00:00:00Z',
        'max_value': '2026-01-01T00:00:00Z'
    })


def test_json_to_df():
    json = {
        'id': 1,
        'user': {
            'name': 'john',
            'email': 'john.smith@example.com'
        },
        'result': {
            'date': '20250101T000000Z',
            'score': 8.3
        }
    }
    mapping = {
        '$.user.name': 'username',
        '$.result.score': 'score'
    }

    dataframe = json_to_df(json, mapping)

    assert(list(dataframe.columns) == ['username', 'score'])
    assert(len(dataframe) == 1)
    assert(dataframe.iloc[[0]].values.flatten().tolist() == ['john', 8.3])
