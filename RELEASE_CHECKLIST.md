 # Release Checklist für Dartcounter v1.4.0

Diese Checkliste stellt einen reibungslosen und qualitativ hochwertigen Release-Prozess sicher.

---

## 1. Code Freeze & Finale Überprüfung

- [ ] **Feature Freeze:** Bestätigen, dass keine neuen Features mehr für diese Version hinzugefügt werden. Nur noch Bugfixes sind erlaubt.
- [ ] **Code-Überprüfung:** Eine letzte Überprüfung aller kürzlichen Änderungen und Bugfixes durchführen.
- [ ] **Linting:** Einen Linter (z.B. `pylint`, `flake8`) über die gesamte Codebasis laufen lassen, um Stilprobleme oder potenzielle Fehler zu finden.
- [ ] **CI-Pipeline prüfen:** Sicherstellen, dass die CI-Pipeline (GitHub Actions) auf dem Release-Branch erfolgreich durchläuft.
- [ ] **Datenbank-Migrationen finalisieren:** Sicherstellen, dass alle Modell-Änderungen in einer Alembic-Migration erfasst sind.
  ```bash
  alembic revision --autogenerate -m "Final changes for v1.3.1"
  ```
- [ ] **Alle Tests ausführen:** Die gesamte Test-Suite ausführen und sicherstellen, dass alle Tests erfolgreich sind.
  ```bash
  python3 -m pytest
  ```
- [ ] **In `main`-Branch mergen:** Sicherstellen, dass der release-fertige Branch in den `main`- (oder `master`-) Branch gemerged wurde.

## 2. Dokumentation & Versionierung
- [ ] **Release vorbereiten (automatisiert):** Das `prepare_release.py`-Skript ausführen, um die Versionsnummer zu erhöhen und das Changelog vorzubereiten.
  ```bash
  python3 prepare_release.py 1.3.0
  ```
- [ ] **Änderungen überprüfen:** Die vom Skript vorgenommenen Änderungen in `core/_version.py` und `CHANGELOG.md` überprüfen und committen.
- [ ] **`README.md` überprüfen:** Das `README.md` durchlesen, um sicherzustellen, dass alle Anleitungen (Installation, Build, Nutzung) korrekt und aktuell sind.
- [ ] **`ROADMAP.md` überprüfen:** Abgeschlossene Features aus den "Zukünftigen Plänen" in die "Abgeschlossenen Meilensteine" verschieben.
- [ ] **`ARCHITECTURE.md` überprüfen:** Sicherstellen, dass das Architektur-Dokument den finalen Stand des Codes widerspiegelt.
- [ ] **`LICENSE`-Datei prüfen:** Bestätigen, dass die `LICENSE`-Datei vorhanden und im `README.md` korrekt referenziert ist.

## 3. Build & Packaging

- [ ] **Saubere Umgebung:** Sicherstellen, dass die virtuelle Umgebung sauber ist und alle Abhängigkeiten aus der `requirements.txt` installiert sind.
- [ ] **Build-Skript ausführen:** Das Build-Skript ausführen, um die distributierbaren Pakete zu erstellen. (Hinweis: Das Skript führt die Tests als Teil des Prozesses erneut aus.)
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
    - [ ] **`config.ini`-Handhabung prüfen:** Verifizieren, dass die Anwendung eine `config.ini` im Anwendungsdaten-Verzeichnis des Benutzers korrekt verwendet oder erstellt.
    - [ ] **Datenbank-Initialisierung testen:** Auf einer sauberen Maschine mit einer leeren Datenbank verifizieren, dass die Anwendung beim ersten Start (dank Alembic) alle Tabellen korrekt anlegt.
    - [ ] Ein neues Spiel starten (z.B. 501).
    - [ ] Ein paar Runden spielen.
    - [ ] Die "Undo"- und "Weiter"-Buttons verwenden.
    - [ ] Das Spiel beenden und gewinnen.
- [ ] **Feature-Test:**
    - [ ] Speichern und Laden eines Spiels testen.
    - [ ] Ein **Doppel-K.o.-Turnier** starten, mehrere Matches spielen und den Turnierbaum (Winners & Losers Bracket) überprüfen.
    - [ ] Ein 501-Spiel im **"Legs & Sets"-Modus** starten (z.B. Best of 3 Legs, Best of 3 Sets) und den korrekten Ablauf prüfen.
    - [ ] Highscore-Fenster und Spielerstatistiken-Fenster testen (erfordert erfolgreiche DB-Initialisierung).
    - [ ] **Profil-Manager testen:** Ein neues Profil erstellen, ein bestehendes bearbeiten und eines löschen.
    - [ ] **Adaptive KI-Erstellung testen:** Für einen menschlichen Spieler das Genauigkeitsmodell berechnen und anschließend einen adaptiven KI-Klon erstellen.
    - [ ] Die Wurf-Heatmap im Statistik-Fenster prüfen.
    - [ ] Ein Spiel gegen eine adaptive KI ("KI-Klon") starten und ihr Verhalten beobachten.
    - [ ] Das neue Trainingsspiel **"Split Score"** starten und den korrekten Ablauf (feste Zielsequenz, Halbierung bei Fehltreffer) prüfen.
    - [ ] Ein Cricket-Spiel gegen die KI starten und ihre **taktische Zielauswahl** (Punkten vs. Schließen) beobachten.
    - [ ] Soundeffekte (an/aus) und Theme-Wechsel (hell/dunkel) testen.
- [ ] **Asset-Laden prüfen:** Sicherstellen, dass das Dartboard und alle anderen Bilder korrekt angezeigt werden.
## 5. Veröffentlichung

- [ ] **Git-Tag erstellen:** Einen neuen Git-Tag für das Release erstellen.
  ```bash
  git tag -a v1.3.0 -m "Release version 1.3.0"
  git push origin v1.3.0
  ```
- [ ] **GitHub-Release erstellen:**
    - [ ] Zur "Releases"-Sektion des GitHub-Repositories gehen.
    - [ ] Ein neues Release basierend auf dem `v1.2.0`-Tag entwerfen.
    - [ ] Den Release-Titel auf "Version 1.2.0" setzen.
    - [ ] Klare und prägnante Release Notes schreiben. **Tipp:** Den Inhalt aus dem `CHANGELOG.md` für diese Version als Basis verwenden.
    - [ ] Die gepackten Artefakte (die `.zip`-Datei und die `setup.exe`) hochladen.
- [ ] **Release veröffentlichen:** Das Release auf GitHub veröffentlichen.