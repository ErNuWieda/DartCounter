# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import platform
import shutil
import subprocess
import sys
import pathlib

# --- Konfiguration ---
VERSION = "1.2.0"
APP_NAME = "DartCounter"
SCRIPT_NAME = pathlib.Path("main.py")
ASSETS_DIR = pathlib.Path("assets")

def main():
    """Führt den plattformspezifischen Build-Prozess aus."""
    # --- Vorab-Prüfungen ---
    print(">>> Schritt 0: Überprüfe Voraussetzungen...")
    if not SCRIPT_NAME.is_file():
        print(f"\nFEHLER: Hauptskript '{SCRIPT_NAME}' nicht gefunden.")
        print("Stellen Sie sicher, dass Sie das Skript im Hauptverzeichnis des Projekts ausführen.")
        sys.exit(1)

    if not ASSETS_DIR.is_dir():
        print(f"\nFEHLER: Asset-Verzeichnis '{ASSETS_DIR}' nicht gefunden.")
        sys.exit(1)

    try:
        import PyInstaller
        print(">>> PyInstaller-Modul gefunden.")
    except ImportError:
        print("\nFEHLER: Das Modul 'PyInstaller' wurde nicht gefunden.")
        print(f"Bitte installieren Sie es in der aktiven Python-Umgebung ({sys.executable}) mit:")
        print("pip install pyinstaller")
        sys.exit(1)

    # --- Plattformspezifisches Setup ---
    system = platform.system()
    if system == "Windows":
        platform_name = "Windows"
        data_separator = ";"
        dist_artifact_name = f"{APP_NAME}.exe"
    elif system == "Darwin":  # macOS
        platform_name = "macOS"
        data_separator = ":"
        dist_artifact_name = f"{APP_NAME}.app"
    else:  # Linux ist das einzig andere unterstützte System
        platform_name = "Linux"
        data_separator = ":"
        dist_artifact_name = APP_NAME

    release_dir = pathlib.Path(f"{APP_NAME}_{platform_name}_v{VERSION}")
    zip_filename_base = str(release_dir)

    print(f"\n>>> Erstelle Release für {platform_name} v{VERSION}...")

    # --- Schritt 1: Alte Build-Artefakte bereinigen ---
    print(">>> Schritt 1: Alte Build-Artefakte bereinigen...")
    for path in [release_dir, pathlib.Path(f"{zip_filename_base}.zip"), pathlib.Path("build"), pathlib.Path("dist"), pathlib.Path(f"{APP_NAME}.spec")]:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            try:
                path.unlink()
            except OSError:
                pass  # Fehler ignorieren, wenn Datei in Gebrauch ist

    # --- Schritt 2: Anwendung mit PyInstaller bauen ---
    print("\n>>> Schritt 2: Anwendung mit PyInstaller bauen...")
    # Dies ist die robusteste Methode, PyInstaller aufzurufen. Sie verwendet denselben
    # Python-Interpreter, der dieses Skript ausführt, und umgeht so PATH-Probleme.
    pyinstaller_command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        f"--add-data={ASSETS_DIR}{data_separator}{ASSETS_DIR}",
        "--hidden-import=PIL._tkinter_finder",
        str(SCRIPT_NAME)
    ]

    print("Führe Befehl aus:")
    print(f"  {' '.join(pyinstaller_command)}")

    # Führe den Befehl aus und zeige die Ausgabe in Echtzeit an. KEIN capture_output.
    result = subprocess.run(pyinstaller_command)

    if result.returncode != 0:
        print("\n" + "="*50)
        print("FEHLER: PyInstaller ist mit einem Fehler fehlgeschlagen.")
        print(f"Exit-Code: {result.returncode}")
        print("Bitte überprüfen Sie die obige Ausgabe von PyInstaller auf die genaue Fehlermeldung.")
        print("Stellen Sie sicher, dass alle Abhängigkeiten aus requirements.txt installiert sind.")
        print("="*50 + "\n")
        sys.exit(1)
    print(">>> PyInstaller erfolgreich abgeschlossen.")

    # --- Schritt 3: Release-Verzeichnis erstellen und Dateien kopieren ---
    print(f"\n>>> Schritt 3: Release-Verzeichnis '{release_dir}' erstellen und Dateien kopieren...")
    release_dir.mkdir(exist_ok=True)

    source_artifact = pathlib.Path("dist") / dist_artifact_name
    if source_artifact.exists():
        shutil.move(str(source_artifact), str(release_dir / dist_artifact_name))
    else:
        print(f"FEHLER: Build-Artefakt '{source_artifact}' wurde nicht gefunden!")
        sys.exit(1)

    shutil.copy("config.ini.example", str(release_dir))
    shutil.copy("README.md", str(release_dir))

    # --- Schritt 4: ZIP-Archiv erstellen ---
    print(f"\n>>> Schritt 4: ZIP-Archiv '{zip_filename_base}.zip' erstellen...")
    shutil.make_archive(zip_filename_base, 'zip', root_dir='.', base_dir=str(release_dir))

    # --- Schritt 5: Temporäre Build-Artefakte bereinigen ---
    print("\n>>> Schritt 5: Temporäre Build-Artefakte bereinigen...")
    shutil.rmtree("build")
    shutil.rmtree("dist")
    pathlib.Path(f"{APP_NAME}.spec").unlink()
    shutil.rmtree(release_dir)

    print(f"\n{'='*50}\n✅ Fertig! Das Release-Paket befindet sich in: {zip_filename_base}.zip\n{'='*50}")

if __name__ == "__main__":
    main()