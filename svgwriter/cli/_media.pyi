import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Any
from ..document import Document

__all__ = ["SceneError", "add_media_commands", "load_scene"]

class SceneError(ValueError):
    ...

def load_scene(path: str | Path) -> tuple[Document, Callable[[Document, float], object] | None, dict[str, Any]]: ...

def add_media_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None: ...
