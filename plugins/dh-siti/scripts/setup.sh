#!/usr/bin/env bash
# Prepara il virtualenv di dhmigrate. Uso: setup.sh <cartella-venv>
# Il venv va fuori dalla cartella del plugin (che può essere in cache e sostituita a ogni aggiornamento):
# dalla skill si passa ${CLAUDE_PLUGIN_DATA}/venv.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
VENV="${1:?indicare la cartella del virtualenv, es. \${CLAUDE_PLUGIN_DATA}/venv}"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q -r "$HERE/requirements.txt"
echo "pronto: PYTHONPATH=$HERE $VENV/bin/python -m dhmigrate --help"
