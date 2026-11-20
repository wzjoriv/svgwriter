import argparse
from argparse import ArgumentParser, Namespace
from ..elements.core._element import Element

__all__ = ["add_basic_commands", "emit", "output_options"]

def emit(root: Element, args: Namespace) -> None: ...

def output_options(sub: ArgumentParser) -> None: ...

def add_basic_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None: ...
