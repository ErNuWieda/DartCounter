th# Release Checklist für Dartcounter v1.2.0

Diese Checkliste stellt einen reibungslosen und qualitativ hochwertigen Release-Prozess sicher.

---

## 1. Code Freeze & Finale Überprüfung

- [x] **Feature Freeze:** Bestätigen, dass keine neuen Features mehr für diese Version hinzugefügt werden. Nur noch Bugfixes sind erlaubt.
- [x] **Code-Überprüfung:** Eine letzte Überprüfung aller kürzlichen Änderungen und Bugfixes durchführen.
- [x] **Linting:** Einen Linter (z.B. `pylint`, `flake8`) über die gesamte Codebasis laufen lassen, um Stilprobleme oder potenzielle Fehler zu finden.
- [x] **Alle Tests ausführen:** Die gesamte Test-Suite ausführen und sicherstellen, dass alle 160 Tests erfolgreich sind.
- [x] **Alle Tests ausführen:** Die gesamte Test-Suite ausführen und sicherstellen, dass alle 166 Tests erfolgreich sind.
  ```bash
  python3 -m pytest
  ```
- [ ] **In `main`-Branch mergen:** Sicherstellen, dass der release-fertige Branch in den `main`- (oder `master`-) Branch gemerged wurde.

## 2. Dokumentation & Versionierung

- [x] **Versionsnummer aktualisieren:** Überprüfen, ob die Versionsnummer konsistent auf `1.2.0` gesetzt ist in:
    - `main.py` (`self.version = "v1.2.0"`)
    - `build.py` (`VERSION = "1.2.0"`)
- [ ] **`README.md` überprüfen:** Das `README.md` durchlesen, um sicherzustellen, dass alle Anleitungen (Installation, Build, Nutzung) für v1.2.0 korrekt und aktuell sind.
- [ ] **`ARCHITECTURE.md` überprüfen:** Sicherstellen, dass das Architektur-Dokument den finalen Stand des Codes widerspiegelt.
- [ ] **`LICENSE`-Datei prüfen:** Bestätigen, dass die `LICENSE`-Datei vorhanden und im `README.md` korrekt referenziert ist.
- [ ] **`CHANGELOG.md` aktualisieren (falls vorhanden):** Alle neuen Features, Bugfixes und Verbesserungen für diese Version dokumentieren.

## 3. Build & Packaging

- [ ] **Saubere Umgebung:** Sicherstellen, dass die virtuelle Umgebung sauber ist und alle Abhängigkeiten aus der `requirements.txt` installiert sind.
- [ ] **Build-Skript ausführen:** Das Build-Skript ausführen, um die distributierbaren Pakete zu erstellen.
  ```bash
  python3 build.py
  ```
- [ ] **Build-Output verifizieren:** Prüfen, ob das Skript erfolgreich das ZIP-Archiv (z.B. `DartCounter_Windows_v1.2.0.zip`) erstellt.
- [ ] **(Optional) Windows-Installer erstellen:**
    - [ ] Das Build-Artefakt entpacken.
    - [ ] `installer/create_installer.iss` mit der korrekten Version und dem Quellpfad aktualisieren.
    - [ ] Den Installer mit Inno Setup kompilieren.
    - [ ] Verifizieren, dass die `setup.exe` erstellt wurde.

## 4. Qualitätssicherung (QA) der Release-Artefakte

- [ ] **Test auf einer sauberen Maschine:** Die gepackte Anwendung (`.exe` oder `.app`) auf einem sauberen System (oder einer VM) ohne Python-Entwicklungsumgebung installieren und ausführen.
- [ ] **Kernfunktionalität testen:**
    - [ ] Ein neues Spiel starten (z.B. 501).
    - [ ] Ein paar Runden spielen.
    - [ ] Die "Undo"- und "Weiter"-Buttons verwenden.
    - [ ] Das Spiel beenden und gewinnen.
- [ ] **Feature-Test:**
    - [ ] Speichern und Laden eines Spiels testen.
    - [ ] Highscore-Fenster testen (falls DB verbunden).
    - [ ] Spielerstatistiken-Fenster testen (falls DB verbunden).
    - [ ] Soundeffekte (an/aus) und Theme-Wechsel (hell/dunkel) testen.
- [ ] **Asset-Laden prüfen:** Sicherstellen, dass das Dartboard und alle anderen Bilder korrekt angezeigt werden.
- [ ] **`config.ini`-Handhabung prüfen:** Verifizieren, dass die Anwendung eine `config.ini` im Anwendungsdaten-Verzeichnis des Benutzers korrekt verwendet oder erstellt.

## 5. Veröffentlichung

- [ ] **Git-Tag erstellen:** Einen neuen Git-Tag für das Release erstellen.
  ```bash
  git tag -a v1.2.0 -m "Release version 1.2.0"
  git push origin v1.2.0
  ```
- [ ] **GitHub-Release erstellen:**
    - [ ] Zur "Releases"-Sektion des GitHub-Repositories gehen.
    - [ ] Ein neues Release basierend auf dem `v1.2.0`-Tag entwerfen.
    - [ ] Den Release-Titel auf "Version 1.2.0" setzen.
    - [ ] Klare und prägnante Release Notes schreiben, die die wichtigsten Änderungen zusammenfassen.
    - [ ] Die gepackten Artefakte (die `.zip`-Datei und die `setup.exe`) hochladen.
- [ ] **Release veröffentlichen:** Das Release auf GitHub veröffentlichen.