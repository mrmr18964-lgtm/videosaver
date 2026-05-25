#!/bin/bash
apt-get update
apt-get install -y ffmpeg
pip install --upgrade pip
pip install -r requirements.txt
pip install --upgrade yt-dlp
