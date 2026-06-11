#!/usr/bin/env python3
"""
run.py  –  Lanceur DevisBTP
Vérifie les dépendances, initialise la BDD, puis démarre l'application.
"""
import sys
import subprocess
import importlib

REQUIRED = {
    "reportlab": "reportlab",
    "PIL":       "Pillow",
}

def check_and_install():
    missing = []
    for module, pkg in REQUIRED.items():
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"Installation des dépendances manquantes : {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
        print("Installation terminée.")

if __name__ == "__main__":
    check_and_install()
    from app import App
    app = App()
    app.mainloop()
