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
git add core/ai_strategy.py
git add tests/test_ai_player.py
git add .github/workflows/reusable-test-workflow.yml
git add .github/workflows/release.yml

# 3. Commit erstellen
git commit -m "fix: AI Killer strategy, fallback test setup and workflow marker logic"

# 4. Push
echo ">>> Pushe zum Repository..."
git push

echo ">>> Fertig! Das Eichhörnchen sollte jetzt Ruhe geben. ;)"
