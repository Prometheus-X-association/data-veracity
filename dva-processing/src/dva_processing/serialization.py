import yaml

from types import SimpleNamespace


def parse_ge_yaml(ge_yaml):
    return SimpleNamespace(**(yaml.safe_load(ge_yaml)))
