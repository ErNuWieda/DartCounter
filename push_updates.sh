#!/bin/bash

# Dartcounter Update & Push Script
echo ">>> Starte Update-Prozess..."

# 1. Lokale Tests ausführen (Sicherheitscheck)
echo ">>> Führe lokale Tests aus..."
python3 -m pytest
if [ $? -ne 0 ]; then
    echo "!!! FEHLER: Die Tests sind fehlgeschlagen. Push abgebrochen. !!!"
    exit 1
fi

echo ">>> Tests erfolgreich. Committe Änderungen..."

# 2. Änderungen hinzufügen
git add tests/conftest.py
git add .github/workflows/reusable-test-workflow.yml
git add .github/workflows/test-on-trixie.yml

# 3. Commit erstellen
git commit -m "fix: resolve ALSA audio errors in CI using SDL dummy driver and global mixer mocking"

# 4. Push
echo ">>> Pushe zum Repository..."
git push

echo ">>> Fertig! Das Eichhörnchen sollte jetzt Ruhe geben. ;)"
