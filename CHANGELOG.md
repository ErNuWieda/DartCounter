# Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### ✨ Features & Verbesserungen

### 🐛 Bugfixes & Stabilität

---

## [1.3.0] - 2025-08-09

### ✨ Features & Verbesserungen

### 🐛 Bugfixes & Stabilität

---

## [1.3.0] - 2025-08-09

### ✨ Features & Verbesserungen

*   **KI-Logik:** Die strategische Zielauswahl der KI-Spieler wurde grundlegend überarbeitet. Sie agiert jetzt im Finish-Bereich deutlich menschlicher, versucht gezielt Setup-Würfe zu spielen und vermeidet unsinnige Würfe auf die 20.
*   **Profil-Manager UI:** Der Dialog zur Verwaltung der Spielerprofile wurde überarbeitet. Er gruppiert und sortiert die Spieler nun logisch (Menschen zuerst, dann KI nach Stärke) und passt seine Fenstergröße dynamisch an den Inhalt an.
*   **Turnierbaum-Visualisierung:** Die Darstellung des Turnierbaums wurde verbessert. Verbindungslinien sind nun pixelgenau, und der Turniersieger wird am Ende prominent mit einem Trophäen-Symbol hervorgehoben.
*   **Legs & Sets für X01-Spiele:** X01-Spiele können nun im professionellen "Best of Legs / Best of Sets"-Modus gespielt werden, um vollwertige Matches zu simulieren.
*   **Doppel-K.o.-Turniere:** Der Turniermodus wurde um die Option "Doppel-K.o." erweitert, bei der Spieler erst nach zwei Niederlagen ausscheiden.
*   **Taktische Cricket-KI:** Die KI für Cricket-Spiele wurde verbessert. Sie analysiert nun den Punktestand und wählt strategisch zwischen dem Schließen von Feldern und dem Sammeln von Punkten.

### 🐛 Bugfixes & Stabilität

*   **Turnier-Logik:** Mehrere kritische Fehler im Turniermodus wurden behoben, die zu Endlosschleifen, falschen Spielerzuweisungen in Folgerunden und einer fehlerhaften Finaldarstellung führten.
*   **Statistik-Heatmap:** Die Wurf-Heatmap im Statistik-Fenster wird jetzt korrekt skaliert und passt sich der Bildschirmgröße an, analog zum Haupt-Dartboard.

---

## [1.2.0] - 2025-XX-XX

Dies ist ein großes Release, das den Dartcounter von einem einfachen Prototyp zu einer vollwertigen, robusten Anwendung weiterentwickelt. Der Fokus lag auf der Implementierung zahlreicher neuer Spielmodi, der Verbesserung der Code-Qualität durch Refactoring und der Einführung einer umfassenden Test-Suite.

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