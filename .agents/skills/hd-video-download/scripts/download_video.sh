#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"
CACHE_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}/hd-video-download"
VENV_DIR="$CACHE_ROOT/venv"
export PIP_CACHE_DIR="$CACHE_ROOT/pip-cache"
export PIP_DISABLE_PIP_VERSION_CHECK=1

if command -v python3.11 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.11)"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3)"
else
  echo "python3 is required." >&2
  exit 1
fi

mkdir -p "$CACHE_ROOT"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

if [[ ! -x "$VENV_DIR/bin/hd-video-download" && -f "$REPO_ROOT/pyproject.toml" && -d "$REPO_ROOT/src/yt_bili_hd_downloader" ]]; then
  "$VENV_DIR/bin/python" -m pip install -q -e "$REPO_ROOT"
elif [[ ! -x "$VENV_DIR/bin/hd-video-download" ]]; then
  "$VENV_DIR/bin/python" -m pip install -q \
    "git+https://github.com/apple-agent1/yt-bili-hd-downloader.git"
fi

exec "$VENV_DIR/bin/hd-video-download" "$@"
