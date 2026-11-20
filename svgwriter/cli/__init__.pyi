from argparse import ArgumentParser
from collections.abc import Sequence
from ._media import SceneError as SceneError, load_scene as load_scene

__all__ = ["SceneError", "build_parser", "load_scene", "main"]

def build_parser() -> ArgumentParser: ...

def main(argv: Sequence[str] | None = None) -> int: ...
