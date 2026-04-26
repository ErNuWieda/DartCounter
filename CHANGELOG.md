# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.4.0] - 2026-04-27

### ✨ Features & Verbesserungen
*   **Immersive Spielerfahrung:** Umfassende Überarbeitung der Ansage-Engine und Einführung visueller sowie akustischer Effekte für besondere Spielereignisse.
    *   **"Big Fish" (170er Checkout):** Legendäre Ansagen und ein spezielles visuelles Overlay (Fisch-Emoji) auf dem Dartboard.
    *   **"180" (Maximum):** Flackernde Blitze und eine große "180"-Anzeige auf dem Dartboard.
    *   **"No Score" (0 Punkte):** Humorvoller Schnecken-Effekt auf dem Dartboard.
    *   **"Bust" (Überwerfen):** Explosions-Emoji und "BUST!"-Schriftzug auf dem Dartboard.
    *   **"Low Score" (1-7 Punkte):** Weinendes Emoji und "LOW SCORE!"-Schriftzug auf dem Dartboard.
    *   **Optionale Effekte:** Alle visuellen Effekte und die dazugehörigen Sounds können in den Einstellungen deaktiviert werden.
    *   **Verbessertes Timing:** Der "Big Fish"-Soundeffekt startet nun leicht verzögert nach der Sprachansage, um die Spannung zu erhöhen.
*   **Robuste Sprachausgabe (TTS):** Die Ansage-Engine wurde auf `edge-tts` umgestellt, mit `gTTS` als intelligentem Fallback, um eine zuverlässige und hochwertige Sprachausgabe zu gewährleisten.
*   **Kontextsensitive Ansagen:** Der Caller gibt nun detailliertere Ansagen für Match-Average, Madhouse-Finishes und Bullseye-Finishes.
*   **Verbesserte Testabdeckung:** Die Testsuite wurde erweitert und stabilisiert, um die neuen Features und die asynchrone TTS-Logik zuverlässig zu verifizieren.

### 🐛 Bugfixes & Stabilität

## [1.3.3] - 2026-04-22

### ✨ Features & Verbesserungen

### 🐛 Bugfixes & Stabilität

---

## [1.3.3] - 2026-04-22

### ✨ Features & Verbesserungen
*   **CI/CD-Integration:** Der Release-Workflow wurde finalisiert, um PostgreSQL-Abhängigkeiten (`requirements-db.txt`) plattformübergreifend korrekt in die Binaries einzubinden.
*   **Release-Automatisierung:** Optimierung der GitHub Actions für konsistente Builds auf Linux, Windows und macOS.

### 🐛 Bugfixes & Stabilität
*   Stabilität der Test-Suite in der CI-Umgebung verifiziert.

---

## [1.3.2] - 2025-09-15

### ✨ Features & Verbesserungen

### 🐛 Bugfixes & Stabilität

---

## [1.3.1] - 2025-08-28

### 🐛 Bugfixes & Stabilität
*   **Test-Suite:** Alle 250 Tests laufen jetzt wieder erfolgreich. Ein Fehler im Test-Setup für den `AIPlayer` wurde behoben, der zu 20 fehlschlagenden Tests führte.
*   **Checkout-Logik:** Die Logik im `CheckoutCalculator` wurde verfeinert, um in allen Fällen die optimalen Finish-Wege zu berechnen. Veraltete Testfälle wurden entsprechend aktualisiert.

---

## [1.3.0] - 2025-08-26

### ✨ Features & Verbesserungen
*   **Professioneller Match-Modus:** X01-Spiele können nun im "Best of Legs / Best of Sets"-Format gespielt werden.
*   **Doppel-K.o.-Turniere:** Der Turniermodus unterstützt jetzt das Doppel-K.o.-System mit Winners & Losers Bracket.
*   **Intelligentere KI:** Die KI-Strategien für X01 (Setup-Würfe) und Cricket (taktische Zielwahl) wurden erheblich verbessert.
*   **Stabile CI/CD-Pipeline:** Die GitHub Actions wurden repariert und optimiert, um zuverlässige Tests auf allen Plattformen zu gewährleisten.
*   **Verbesserte UI:** Der Turnierbaum und der Profil-Manager wurden optisch und funktional aufgewertet.

### 🐛 Bugfixes & Stabilität

*   **Turnier-Logik:** Kritische Fehler im Turniermodus wurden behoben, die zu Endlosschleifen und falschen Spielerzuweisungen führten.
*   **Test-Suite:** Die gesamte Test-Suite wurde stabilisiert. Alle Tests laufen jetzt zuverlässig und sind vom Dateisystem entkoppelt.

---

## [1.2.0] - 2025-08-01

### ✨ Features & Verbesserungen

*   **Neue Spielmodi:** Shanghai, Killer, Elimination, Tactics, Micky Maus und Around the Clock (ATC) wurden hinzugefügt.
*   **Speichern & Laden:**
    *   Laufende Spiele können jetzt gespeichert und zu einem späteren Zeitpunkt fortgesetzt werden.
    *   Speicherdateien enthalten jetzt eine Versionsnummer, um die Kompatibilität bei zukünftigen Updates sicherzustellen.
*   **Statistiken & Highscores:**
    *   Die Anwendung erfasst jetzt Basis-Statistiken (3-Dart-Average, MPR, Checkout-Quote).
    *   Highscores werden jetzt in einer PostgreSQL-Datenbank gespeichert (optional).
*   **Benutzererfahrung (UX):**
    *   Ein helles und ein dunkles Theme wurden hinzugefügt und können in den Einstellungen umgeschaltet werden.
    *   Soundeffekte für Treffer und Spielgewinne wurden implementiert (deaktivierbar).
    *   Spieler können ein laufendes Spiel jetzt verlassen.
*   **Build-System:**
    *   Ein plattformübergreifendes Build-Skript (`build.py`) wurde erstellt, das die Anwendung für Windows, macOS und Linux paketiert.
    *   Ein Skript zur Erstellung eines professionellen Windows-Installers (`setup.exe`) mit Inno Setup wurde hinzugefügt.

### 🐛 Bugfixes & Stabilität

*   **Umfassende Tests:** Eine Test-Suite mit über 166 Unit-Tests wurde implementiert, um die Kernlogik abzusichern und Regressionen zu verhindern.
*   **Fehlerbehandlung:** Die Fehlerbehandlung bei ungültigen Würfen oder Aktionen wurde verbessert.
*   **UI-Stabilität:** Diverse kleine Fehler in der UI-Anzeige und Fensterpositionierung wurden behoben.

### 📚 Dokumentation & Code-Qualität

*   **Architektur-Refactoring:** Die gesamte Codebasis wurde nach klaren Architekturprinzipien (MVC, Strategy Pattern) umstrukturiert, um die Wartbarkeit und Erweiterbarkeit zu verbessern.
*   **Dokumentation:**
    *   Eine detaillierte `ARCHITECTURE.md` beschreibt den Aufbau der Anwendung.
    *   Das `README.md` wurde umfassend überarbeitet und enthält jetzt detaillierte Installations- und Build-Anleitungen.
    *   Docstrings im gesamten Code wurden ergänzt und verbessert.
*   **Repository-Hygiene:** Eine `.gitignore`-Datei wurde hinzugefügt, um das Repository sauber zu halten.