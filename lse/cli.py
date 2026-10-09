"""
    python -m lse.cli path/to/input.txt     
    python -m lse.cli             
"""
from __future__ import annotations

import argparse
from logging import root
import sys
from pathlib import Path

from lse import pipeline

FILE_EXTENSIONS = (".txt", ".blif")


class InputError(Exception):
    """Raised when the input file cannot be chosen or read."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lse", description="Logic Synthesis Engine")
    parser.add_argument("file", nargs="?", type=Path,
                        help=f"input file, {FILE_EXTENSIONS}); "
                             "file picker will pop up if not provided")
    return parser


def pick_file(title: str = "Select input file") -> Path | None:
    """File picker window"""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError as exc:
        raise InputError("file picker unavailable: tkinter is not installed; "
                         "pass the file path instead") from exc

    try:
        window = tk.Tk()
    except tk.TclError as exc:                  
        raise InputError(f"file picker unavailable ({exc}); "
                         "pass the file path instead") from exc
    window.withdraw()                            
    window.attributes("-topmost", True)           
    try:
        file_chosen = filedialog.askopenfilename(
            title=title,
            filetypes=[("Supported files", tuple(f"*{ext}" for ext in FILE_EXTENSIONS)),
                       ("All files", "*")])
    finally:
        window.destroy()
    return Path(file_chosen) if file_chosen else None     

def retrieve_path(file: Path | None) -> Path:
    path = file if file is not None else pick_file()
    if path is None:
        raise InputError("no file selected")
    path = path.expanduser()
    if not path.is_file():
        raise InputError(f"no file in path: {path}")
    if path.suffix.lower() not in FILE_EXTENSIONS:
        raise InputError(f"unsupported file type '{path.suffix}', "
                         f"should be {FILE_EXTENSIONS}")
    return path


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        path = retrieve_path(args.file)
        text = path.read_text(encoding="utf-8")
        results = pipeline.run(text)
    except (InputError, ValueError) as exc:
        print(f"lse: error: {exc}", file=sys.stderr)
        return 1
    print(f"Loaded input file: {path} ({len(text.splitlines())} lines)")
    for out, forms in results.items():
        print(f"\n[{out}]")
        print(f"  SOP:           {forms['sop']}")
        print(f"  Minterms:      \u03a3m({', '.join(map(str, forms['minterms']))})")
        print(f"  Canonical SOP: {forms['canonical_sop']}")
        print(f"  Maxterms:      \u03a0M({', '.join(map(str, forms['maxterms']))})")
        print(f"  Canonical POS: {forms['canonical_pos']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
