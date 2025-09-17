"""
PyJolt cli
"""
from typing import Callable
from pathlib import Path
import sys

from .new_project import new_project

methods: dict[str, Callable] = {
    "new-project": new_project
}


def main() -> None:
    # dispatch to subcommands however you like
    # e.g., argparse/typer/click. For now, just a stub:
    cwd = Path.cwd()
    args: list[str]
    if len(sys.argv) > 1:
        args = sys.argv[1:]
        method = methods.get(args[0], None)
        if method is None:
            print(f"Invalid method: {args[0]}. Valid options are: {', '.join(methods.keys())}")
            return
        method_args = args[1:] if len(args)>1 else None
        if method_args:
            return method(cwd, *method_args)
        return method(cwd)
