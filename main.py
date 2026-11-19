#!/usr/bin/env python3
"""Ship the finished front page to the grader's output folder.

The artwork is pre-rendered as entry.png beside this file; this
entrypoint only moves those exact bytes to where the grader looks, so
the submitted image is identical to the reviewed one.
"""

import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGE = "entry.png"
OUTPUT = "entry.png"


def main():
    src = HERE / IMAGE
    if not src.exists():
        print(f"no image at {src}", file=sys.stderr)
        return 1
    dest_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "out"))
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / OUTPUT
    shutil.copyfile(src, dest)
    print(f"delivered {dest} ({src.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
