#!/usr/bin/env python3
import sys
import subprocess
import importlib

REQUIRED = ["reportlab", "PIL"]

def check_and_install():
    missing = []
    for module in REQUIRED:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module.lower() if module == "PIL" else module)
    if missing:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)

if __name__ == "__main__":
    check_and_install()
    from app import App
    app = App()
    app.mainloop()
