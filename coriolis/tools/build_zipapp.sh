#!/usr/bin/env bash
# Build a single-file distribution: dist/coriolis.pyz
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist build_zipapp
mkdir -p dist build_zipapp
cp -r coriolis build_zipapp/
find build_zipapp -name __pycache__ -type d -prune -exec rm -rf {} +
cat > build_zipapp/__main__.py <<'PY'
from coriolis.ui import main

if __name__ == "__main__":
    main()
PY
python3 -m zipapp build_zipapp -o dist/coriolis.pyz -p "/usr/bin/env python3"
rm -rf build_zipapp
echo "built dist/coriolis.pyz ($(du -h dist/coriolis.pyz | cut -f1))"
