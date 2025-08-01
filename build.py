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
from core._version import __version__

# --- Konfiguration ---
# Die Version wird jetzt aus einer zentralen Datei gelesen (Single Source of Truth).
VERSION = __version__
APP_NAME = "DartCounter"
SCRIPT_NAME = pathlib.Path("main.py")
ASSETS_DIR = pathlib.Path("assets")

def run_tests():
    """Führt die Test-Suite aus und bricht bei Fehlern ab."""
    print("\n>>> Schritt 0.5: Führe Test-Suite aus...")
    try:
        # -s: Gibt print() ausgaben aus
        # -v: Verbose output
        # --ignore=... : Ignoriert das venv-Verzeichnis, um Konflikte zu vermeiden
        test_command = [sys.executable, "-m", "pytest", "-sv", "--ignore=.venv"]
        subprocess.run(test_command, check=True)
        print(">>> Alle Tests erfolgreich bestanden.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("\n" + "="*50)
        print("FEHLER: Die Test-Suite ist fehlgeschlagen oder pytest wurde nicht gefunden.")
        print("Bitte beheben Sie die Testfehler, bevor Sie einen Build erstellen.")
        print("="*50 + "\n")
        return False

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

    # Führe die Tests aus, bevor der Build-Prozess startet
    if not run_tests():
        sys.exit(1)

    # --- Plattformspezifisches Setup ---
    system = platform.system()
    if system == "Windows":
        data_separator = ";"
        icon_extension = ".ico"
    elif system == "Darwin":  # macOS
        data_separator = ":"
        icon_extension = ".icns"
    else:  # Linux ist das einzig andere unterstützte System
        data_separator = ":"
        icon_extension = None # Kein Standard-Icon-Format für ausführbare Linux-Dateien

    # Artefakt-Namen zentral definieren
    dist_artifact_name = f"{APP_NAME}.exe" if system == "Windows" else (f"{APP_NAME}.app" if system == "Darwin" else APP_NAME)
    release_dir = pathlib.Path(f"{APP_NAME}_{system}_v{VERSION}")
    zip_filename_base = str(release_dir)

    print(f"\n>>> Erstelle Release für {system} v{VERSION}...")

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
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=mx.DateTime",
    ]

    # Plattformspezifisches Icon hinzufügen (sauberere Logik)
    if icon_extension:
        icon_path = ASSETS_DIR / f"icon{icon_extension}"
        if icon_path.is_file():
            pyinstaller_command.append(f"--icon={icon_path}")

    # Zentralisierte Liste der Daten, die in den Build aufgenommen werden sollen.
    # Das macht das Hinzufügen neuer Dateien übersichtlicher.
    data_to_add = [
        (ASSETS_DIR, ASSETS_DIR),
        (pathlib.Path("core/game_config.json"), pathlib.Path("core")),
        (pathlib.Path("core/checkout_paths.json"), pathlib.Path("core")),
        (pathlib.Path("config.ini.example"), pathlib.Path(".")),
        (pathlib.Path("README.md"), pathlib.Path(".")),
    ]
    for src, dest in data_to_add:
        pyinstaller_command.append(f"--add-data={src}{data_separator}{dest}")

    pyinstaller_command.append(str(SCRIPT_NAME))

    print("Führe Befehl aus:")
    print(f"  {' '.join(pyinstaller_command)}")

    # Führe den Befehl aus und zeige die Ausgabe in Echtzeit an. KEIN capture_output.
    try:
        subprocess.run(pyinstaller_command, check=True)
    except subprocess.CalledProcessError as e:
        print("\n" + "="*50)
        print("FEHLER: PyInstaller ist mit einem Fehler fehlgeschlagen.")
        print(f"Exit-Code: {e.returncode}")
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

    # --- Schritt 4 & 5: Finalisieren (ZIP oder für Installer vorbereiten) ---
    # Im CI-Kontext auf Windows überspringen wir das Zippen und Aufräumen,
    # damit der Installer-Workflow auf die erstellten Dateien zugreifen kann.
    if system == "Windows" and os.getenv("CI"):
        print("\n>>> Schritt 4 & 5: CI-Umgebung (Windows) erkannt. Überspringe ZIP-Erstellung und Cleanup.")
        print(f">>> Die Build-Artefakte sind bereit für den Installer in: '{release_dir}'")
    else:
        # --- Schritt 4: ZIP-Archiv erstellen (lokaler Build) ---
        print(f"\n>>> Schritt 4: ZIP-Archiv '{zip_filename_base}.zip' erstellen...")
        shutil.make_archive(zip_filename_base, 'zip', root_dir='.', base_dir=str(release_dir))

        # --- Schritt 5: Temporäre Build-Artefakte bereinigen (lokaler Build) ---
        print("\n>>> Schritt 5: Temporäre Build-Artefakte bereinigen...")
        shutil.rmtree("build")
        shutil.rmtree("dist")
        pathlib.Path(f"{APP_NAME}.spec").unlink()
        shutil.rmtree(release_dir)

    print(f"\n{'='*50}\n✅ Build-Prozess abgeschlossen.\n{'='*50}")

if __name__ == "__main__":
    main()