#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MENU_PATH="$SCRIPT_DIR/menu.py"
VENV_PYTHON="$SCRIPT_DIR/hoarder_env/bin/python3"

if [[ ! -f "$MENU_PATH" ]]; then
  osascript -e 'display alert "hoarder-tools" message "menu.py was not found next to launch.command."' >/dev/null 2>&1 || true
  exit 1
fi

if [[ -x "$VENV_PYTHON" ]]; then
  PYTHON_BIN="$VENV_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  osascript -e 'display alert "hoarder-tools" message "python3 is not available in PATH."' >/dev/null 2>&1 || true
  exit 1
fi

run_menu() {
  cd "$SCRIPT_DIR"
  "$PYTHON_BIN" "$MENU_PATH"
}

run_menu
