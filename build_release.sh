#!/bin/bash

# Stellt sicher, dass das Skript bei einem Fehler abbricht
set -e

VERSION="1.2.0"
APP_NAME="DartCounter"
RELEASE_DIR="${APP_NAME}_Linux_v${VERSION}"

echo ">>> Schritt 1: Virtuelle Umgebung aktivieren (Annahme: .venv existiert)"
# Wenn du das Skript manuell ausführst, aktiviere die venv vorher:
# source .venv/bin/activate
if [ -z "$VIRTUAL_ENV" ]; then
    echo "WARNUNG: Keine aktive virtuelle Umgebung. Versuche .venv/bin/activate zu sourcen..."
    source .venv/bin/activate
fi

echo ">>> Schritt 2: Anwendung mit PyInstaller bauen..."
pyinstaller --noconfirm --onefile --windowed --name "$APP_NAME" \
            --add-data "assets:assets" \
            --hidden-import=PIL._tkinter_finder \
            main.py

echo ">>> Schritt 3: Release-Verzeichnis erstellen und aufräumen..."
rm -rf "$RELEASE_DIR" "${RELEASE_DIR}.zip" # Alte Versionen löschen
mkdir -p "$RELEASE_DIR"

echo ">>> Schritt 4: Notwendige Dateien kopieren..."
mv "dist/$APP_NAME" "$RELEASE_DIR/"
cp "config.ini.example" "$RELEASE_DIR/"
cp "README.md" "$RELEASE_DIR/"

echo ">>> Schritt 5: ZIP-Archiv erstellen..."
zip -r "${RELEASE_DIR}.zip" "$RELEASE_DIR"

echo ">>> Schritt 6: Build-Artefakte bereinigen..."
rm -rf build dist "$APP_NAME.spec" "$RELEASE_DIR"

echo "========================================================="
echo "✅ Fertig! Das Release-Paket befindet sich in: ${RELEASE_DIR}.zip"
echo "========================================================="