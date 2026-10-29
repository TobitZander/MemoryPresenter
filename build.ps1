$ErrorActionPreference = "Stop"

py -3 -m pip install -r requirements.txt pyinstaller
py -3 build.py
