#!/usr/bin/env bash
set -e

if command -v python >/dev/null 2>&1; then
  PYTHON=python
elif command -v python3 >/dev/null 2>&1; then
  PYTHON=python3
else
  echo "Python is required but not found."
  exit 1
fi

$PYTHON -m pip install --upgrade pip
$PYTHON -m pip install -r requirements.txt
$PYTHON -m pip install --upgrade yt-dlp

if command -v apt-get >/dev/null 2>&1; then
  apt-get update
  apt-get install -y ffmpeg
else
  echo "WARNING: apt-get unavailable, skipping ffmpeg install."
fi
