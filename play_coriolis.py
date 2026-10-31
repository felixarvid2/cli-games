#!/usr/bin/env python3
"""Launch CORIOLIS: an Elite-style space game for the terminal."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))

from coriolis.ui import main  # noqa: E402

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
