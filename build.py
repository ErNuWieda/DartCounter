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
DIST_DIR = pathlib.Path("dist")
ASSETS_DIR = pathlib.Path("assets")


def run_tests():
    """Führt die Test-Suite aus und bricht bei Fehlern ab."""
    print("\n>>> Schritt 0.5: Führe Test-Suite aus...")
    try:
        # Die Konfiguration für Coverage etc. wird jetzt aus der pytest.ini gelesen.
        # Wir behalten nur die Flags, die wir speziell für den Build-Prozess wollen.
        test_command = [
            sys.executable,
            "-m",
            "pytest",
            "-sv",  # -s: print() ausgeben, -v: verbose. Gut für Build-Logs.
        ]
        subprocess.run(test_command, check=True)
        print(">>> Alle Tests erfolgreich bestanden.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("\n" + "=" * 50)
        print("FEHLER: Die Test-Suite ist fehlgeschlagen.")
        print("Mögliche Ursachen:")
        print("  - Ein oder mehrere Tests sind nicht erfolgreich.")
        print("  - Die Test-Abhängigkeiten (pytest, pytest-cov) sind nicht installiert.")
        print("Stellen Sie sicher, dass Sie alle Entwicklungs-Abhängigkeiten installiert haben:")
        print("  pip install -r requirements-dev.txt")
        print("=" * 50 + "\n")
        return False


def clean_previous_builds(release_dir: pathlib.Path):
    """Entfernt alte Build-Artefakte, um einen sauberen Build zu gewährleisten."""
    print(">>> Schritt 1: Alte Build-Artefakte bereinigen...")
    zip_file = release_dir.with_suffix(".zip")
    spec_file = pathlib.Path(f"{APP_NAME}.spec")

    for path in [release_dir, zip_file, pathlib.Path("build"), DIST_DIR, spec_file]:
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file():
            try:
                path.unlink()
            except OSError:
                pass


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

    # --- Plattform- und Artefakt-Setup ---
    system = platform.system()
    data_separator = ";" if system == "Windows" else ":"
    dist_artifact_name = (
        f"{APP_NAME}.exe"
        if system == "Windows"
        else (f"{APP_NAME}.app" if system == "Darwin" else APP_NAME)
    )
    release_dir = pathlib.Path(f"{APP_NAME}_{system}_v{VERSION}")
    icon_extension = ".ico" if system == "Windows" else ".icns" if system == "Darwin" else None

    print(f"\n>>> Erstelle Release für {system} v{VERSION}...")

    clean_previous_builds(release_dir)

    # --- Schritt 2: Anwendung mit PyInstaller bauen ---
    print("\n>>> Schritt 2: Anwendung mit PyInstaller bauen...")
    # Dies ist die robusteste Methode, PyInstaller aufzurufen. Sie verwendet denselben
    # Python-Interpreter, der dieses Skript ausführt, und umgeht so PATH-Probleme.
    pyinstaller_command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        # Notwendig, damit PyInstaller die Brücke zwischen Pillow und Tkinter korrekt einbindet.
        "--hidden-import=PIL._tkinter_finder",
    ]

    # Plattformspezifisches Icon hinzufügen (sauberere Logik)
    if icon_extension:
        icon_path = ASSETS_DIR / f"icon{icon_extension}"
        if icon_path.is_file():
            pyinstaller_command.append(f"--icon={icon_path}")

    # Daten, die direkt in die ausführbare Datei gebündelt werden sollen.
    data_to_add = [
        (ASSETS_DIR, ASSETS_DIR),
        (pathlib.Path("game_config.json"), pathlib.Path(".")),
        (pathlib.Path("core/checkout_paths.json"), pathlib.Path("core")),
        # Alembic für Datenbank-Migrationen hinzufügen
        (pathlib.Path("alembic.ini"), pathlib.Path(".")),
        (pathlib.Path("alembic"), pathlib.Path("alembic")),
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
        print("\n" + "=" * 50)
        print("FEHLER: PyInstaller ist mit einem Fehler fehlgeschlagen.")
        print(f"Exit-Code: {e.returncode}")
        print(
            "Bitte überprüfen Sie die obige Ausgabe von PyInstaller auf die genaue Fehlermeldung."
        )
        print("Stellen Sie sicher, dass alle Abhängigkeiten aus requirements.txt installiert sind.")
        print("=" * 50 + "\n")
        sys.exit(1)
    print(">>> PyInstaller erfolgreich abgeschlossen.")

    # --- Schritt 3: Release-Verzeichnis erstellen und Dateien kopieren ---
    print(f"\n>>> Schritt 3: Release-Verzeichnis '{release_dir}' erstellen und Dateien kopieren...")
    release_dir.mkdir(exist_ok=True)

    # Haupt-Artefakt verschieben
    source_artifact = DIST_DIR / dist_artifact_name
    if source_artifact.exists():
        print(f"  -> Verschiebe Artefakt: '{source_artifact}' -> '{release_dir}'")
        shutil.move(str(source_artifact), str(release_dir / dist_artifact_name))
    else:
        print(f"FEHLER: Build-Artefakt '{source_artifact}' wurde nicht gefunden!")
        sys.exit(1)

    # 3.2: Zusätzliche, für den Benutzer nützliche Dateien kopieren
    files_to_copy = ["README.md", "config.ini.example"]
    for filename in files_to_copy:
        src = pathlib.Path(filename)
        if src.exists():
            print(f"  -> Kopiere '{src}' nach '{release_dir}'")
            shutil.copy(src, release_dir)

    # --- Schritt 4 & 5: Finalisieren (ZIP oder für Installer vorbereiten) ---
    # Im CI-Kontext auf Windows überspringen wir das Zippen und Aufräumen,
    # damit der Installer-Workflow auf die erstellten Dateien zugreifen kann.
    if system == "Windows" and os.getenv("CI"):
        print(
            "\n>>> Schritt 4 & 5: CI-Umgebung (Windows) erkannt. Überspringe ZIP-Erstellung und Cleanup."
        )
        print(f">>> Die Build-Artefakte sind bereit für den Installer in: '{release_dir}'")
    else:
        # --- Schritt 4: ZIP-Archiv erstellen (lokaler Build) ---
        print(f"\n>>> Schritt 4: ZIP-Archiv '{release_dir}.zip' erstellen...")
        shutil.make_archive(str(release_dir), "zip", root_dir=".", base_dir=str(release_dir))

        # --- Schritt 5: Temporäre Build-Artefakte bereinigen (lokaler Build) ---
        print("\n>>> Schritt 5: Temporäre Build-Artefakte bereinigen...")
        shutil.rmtree("build")
        shutil.rmtree(DIST_DIR)
        pathlib.Path(f"{APP_NAME}.spec").unlink()
        shutil.rmtree(release_dir)

    print(f"\n{'='*50}")
    print("✅ Build-Prozess erfolgreich abgeschlossen.")
    print(f"Das finale ZIP-Archiv finden Sie hier: {release_dir}.zip")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
