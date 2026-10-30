#!/usr/bin/env bash
# Build a single-file distribution: dist/cinderspire.pyz
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist build_zipapp
mkdir -p dist build_zipapp
cp -r cinderspire build_zipapp/
find build_zipapp -name __pycache__ -type d -prune -exec rm -rf {} +
cat > build_zipapp/__main__.py <<'PY'
from cinderspire.ui import main

if __name__ == "__main__":
    main()
PY
python3 -m zipapp build_zipapp -o dist/cinderspire.pyz -p "/usr/bin/env python3"
rm -rf build_zipapp
echo "built dist/cinderspire.pyz ($(du -h dist/cinderspire.pyz | cut -f1))"
