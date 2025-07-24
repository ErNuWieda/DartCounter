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

# --- Konfiguration ---
VERSION = "1.2.0"
APP_NAME = "DartCounter"
SCRIPT_NAME = "main.py"

def main():
    """Führt den plattformspezifischen Build-Prozess aus."""
    # --- Plattformspezifisches Setup ---
    system = platform.system()
    if system == "Windows":
        platform_name = "Windows"
        # PyInstaller --add-data separator for Windows is ';'
        data_separator = ";"
        # The final executable/bundle in the dist folder
        dist_artifact_name = f"{APP_NAME}.exe"
    elif system == "Darwin":  # macOS
        platform_name = "macOS"
        data_separator = ":"
        dist_artifact_name = f"{APP_NAME}.app"
    elif system == "Linux":
        platform_name = "Linux"
        data_separator = ":"
        dist_artifact_name = APP_NAME
    else:
        print(f"FEHLER: Nicht unterstütztes Betriebssystem: {system}")
        sys.exit(1)

    release_dir = f"{APP_NAME}_{platform_name}_v{VERSION}"
    zip_filename_base = release_dir

    print(f">>> Erstelle Release für {platform_name} v{VERSION}...")

    # --- Schritt 1: Alte Build-Artefakte bereinigen ---
    print(">>> Schritt 1: Alte Build-Artefakte bereinigen...")
    for path in [release_dir, f"{zip_filename_base}.zip", "build", "dist", f"{APP_NAME}.spec"]:
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        elif os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass # Ignore errors if file is in use

    # --- Schritt 2: Anwendung mit PyInstaller bauen ---
    print(">>> Schritt 2: Anwendung mit PyInstaller bauen...")
    pyinstaller_command = [
        "pyinstaller", "--noconfirm", "--onefile", "--windowed",
        f"--name={APP_NAME}",
        f"--add-data=assets{data_separator}assets",
        "--hidden-import=PIL._tkinter_finder",
        SCRIPT_NAME
    ]

    result = subprocess.run(pyinstaller_command, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        print("FEHLER: PyInstaller ist fehlgeschlagen.")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)

    # --- Schritt 3: Release-Verzeichnis erstellen und Dateien kopieren ---
    print(f">>> Schritt 3: Release-Verzeichnis '{release_dir}' erstellen und Dateien kopieren...")
    os.makedirs(release_dir, exist_ok=True)
    shutil.move(os.path.join("dist", dist_artifact_name), os.path.join(release_dir, dist_artifact_name))
    shutil.copy("config.ini.example", release_dir)
    shutil.copy("README.md", release_dir)

    # --- Schritt 4: ZIP-Archiv erstellen ---
    print(f">>> Schritt 4: ZIP-Archiv '{zip_filename_base}.zip' erstellen...")
    shutil.make_archive(zip_filename_base, 'zip', root_dir='.', base_dir=release_dir)

    # --- Schritt 5: Temporäre Build-Artefakte bereinigen ---
    print(">>> Schritt 5: Temporäre Build-Artefakte bereinigen...")
    shutil.rmtree("build")
    shutil.rmtree("dist")
    os.remove(f"{APP_NAME}.spec")
    shutil.rmtree(release_dir)

    print(f"\n{'='*50}\n✅ Fertig! Das Release-Paket befindet sich in: {zip_filename_base}.zip\n{'='*50}")

if __name__ == "__main__":
    main()