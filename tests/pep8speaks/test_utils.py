import pytest
from pep8speaks.utils import update_dict


class TestUtils:

    @pytest.mark.parametrize('base, head, expected', [
        ({}, {}, {}),
        ({}, {"k1": "v1"}, {}),
        ({"k1": "v1"}, {}, {"k1": "v1"}),
        ({"k1": "v1"}, {"k1": "v2"}, {"k1": "v2"}),
        ({"k1": "v1"}, {"k1": None}, {"k1": None}),
        ({"k1": "v1"}, {"k2": "v2"}, {"k1": "v1"}),
        ({"k1": ["v1", "v2", "v3"]}, {"k1": "v1"}, {"k1": "v1"}),
        ({"k1": "v1"}, {"k1": {"k2": {'k3': 3}}}, {"k1": "v1"}),
        ({"k1": "v1"}, {"k1": ["v1", "v2", "v3"]}, {"k1": ["v1", "v2", "v3"]}),
        ({"k1": {"k2": "v1"}}, {"k1": "v1"}, {"k1": "v1"}),
        ({"k1": {"k2": "v1"}}, {"k1": {"k2": "v2"}}, {"k1": {"k2": "v2"}}),
        ({"k1": {"k2": "v1", "k3": "v2"}}, {"k1": {"k2": "v3"}}, {'k1': {'k2': 'v3', 'k3': 'v2'}}),
    ])
    def test_update_dict(self, base, head, expected):
        assert update_dict(base, head) == expected
