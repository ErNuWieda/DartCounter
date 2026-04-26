# Dartcounter Deluxe

[![CI](https://github.com/ErNuWieda/DartCounter/actions/workflows/ci.yml/badge.svg)](https://github.com/ErNuWieda/DartCounter/actions/workflows/ci.yml)
[![Test on Trixie](https://github.com/ErNuWieda/DartCounter/actions/workflows/test-on-trixie.yml/badge.svg)](https://github.com/ErNuWieda/DartCounter/actions/workflows/test-on-trixie.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)


Ein einfacher, aber funktionsreicher Dart-Zähler, entwickelt mit Python und Tkinter.
Dieses Projekt zielt darauf ab, eine benutzerfreundliche Oberfläche für verschiedene Dartspiele zu bieten, um das manuelle Zählen von Punkten zu ersetzen.

## Features

*   **Verschiedene Spielmodi:**
    *   **Turniermodus:** Erstelle Turniere im **K.o.- oder Doppel-K.o.-System** für bis zu 8 Spieler. Der Fortschritt wird in einem interaktiven, grafischen Turnierbaum visualisiert.
    *   **X01-Spiele:** 301, 501, 701 mit flexiblen Regeln für:
        *   **Profi-Modus:** Spiele vollwertige Matches im "Best of Legs / Best of Sets"-Format.
        *   Opt-In: Single, Double, Masters
        *   Opt-Out: Single, Double, Masters
    *   **Cricket-Varianten:** Standard Cricket, Cut Throat und Tactics.
    *   **Strategie- & Partyspiele:** Around the Clock (ATC), Micky Maus, Killer, Elimination und Shanghai.
    *   **Trainingsspiele:** **Split Score** (Treffe S, D, T eines wählbaren Ziels).
*   **Intelligente KI-Gegner:**
    *   Spiele gegen KI-Gegner mit einstellbaren Schwierigkeitsgraden (von Anfänger bis Champion).
    *   Die KI verfolgt eine menschliche Wurfstrategie, inklusive Power-Scoring und cleveren Setup-Würfen im Finish-Bereich.
    *   **Adaptive 'KI-Klone':** Lassen Sie die KI die Wurf-Statistiken (Genauigkeit und Streuung) eines menschlichen Spielers analysieren und erstellen Sie einen Klon als perfekten, realistischen Sparringspartner.
*   **Immersive Atmosphäre & Audio-Feedback:**
    *   **Neuraler Voice-Caller:** Hochwertige, menschlich klingende Sprachausgabe (via edge-tts/gTTS) sagt Scores, Checkout-Wege und Siege an. Verschiedene Stimmen wählbar.
    *   **Visuelle Highlights:** Spezielle Overlays und Animationen auf dem Dartboard für 180er, den legendären „Big Fish“ (170er Finish) sowie humorvolle Effekte für „No Score“ oder „Bust“.
    <p align="center">
      <img src="./assets/effect_180.png" width="300" alt="180er Effekt" />
      <img src="./assets/effect_big_fish.png" width="300" alt="Big Fish Effekt" />
    </p>
    *   **Dynamische Soundeffekte:** Passende akustische Untermalung für besondere Momente, die für echtes „Ally Pally“-Feeling sorgt.
*   **Spieler-Profile & Statistiken:**
    *   **Persistente Profile:** Erstelle und verwalte Spielerprofile (Mensch & KI) mit Namen, Avatar und individueller Dart-Farbe.
    *   **Detaillierte Statistiken:** Verfolge deine Leistung mit Statistiken wie 3-Dart-Average, MPR, Checkout-Quote und einem grafischen Formverlauf.
    *   **Wurf-Analyse:** Visualisiere deine Treffsicherheit mit einer persönlichen Wurf-Heatmap.
*   **Moderne Benutzeroberfläche:**
    *   Interaktives, klickbares Dartboard zur einfachen Eingabe der Würfe.
    *   **Dynamische Overlays:** Echtzeit-Anzeige von speziellen Ereignissen direkt auf dem Board.
    *   **High-DPI aware:** Automatische Skalierung der Overlays und Icons für 4K- und Retina-Monitore.
    *   Helles und dunkles Design wählbar.
    *   **Statistik-Integrität:** Intelligente Undo-Funktion, die auch bei Spiel-Ende die Datenbank-Einträge (Highscores/Stats) sauber bereinigt.
*   **Speichern & Laden:** Laufende Spiele und Turniere können jederzeit gespeichert und später fortgesetzt werden.
*   **Einfache Einrichtung & Wartung:** Dank automatischer Datenbank-Migrationen werden Tabellen beim ersten Start selbstständig angelegt und bei zukünftigen Updates aktualisiert.
*   **Individuelle Scoreboards:** Für jeden Spieler mit allen relevanten Informationen.

![Turnier-Ansicht](./assets/screenshot_tournament.png "Turnierbaum für 8 Spieler")
![Spielerprofile verwalten](./assets/screenshot_profiles.png "Verwaltung der Spielerprofile mit Avataren und Farben")
![Statistik-Analyse](./assets/screenshot_stats.png "Detaillierte Statistiken mit Formkurve und Heatmap-Option")
![Spielansicht](./assets/screenshot_gameplay.png "Laufendes 501-Spiel mit Finish-Vorschlag")

## Systemvoraussetzungen

Die Anwendung wird kontinuierlich auf den neuesten Versionen von Windows, Ubuntu und Debian (inkl. Trixie/testing) getestet, um eine breite Kompatibilität zu gewährleisten.

*   **Python:** Version 3.8 oder neuer.
*   **Git:** Zum Herunterladen (Klonen) des Projekts.
*   **Tkinter:** Ist in den meisten Standard-Python-Installationen für Windows und macOS enthalten. Unter Linux muss es eventuell manuell installiert werden (z.B. `sudo apt install python3-tk` auf Debian/Ubuntu).
   *   **Wichtiger Hinweis für Debian/Ubuntu:** Für die Bildanzeige in Tkinter wird zusätzlich das Paket `python3-pil.imagetk` benötigt. Installieren Sie es mit:
       `sudo apt install python3-pil.imagetk`
       Dies stellt sicher, dass die von `pip` installierte `Pillow`-Bibliothek korrekt mit der System-Tkinter-Bibliothek zusammenarbeiten kann.
*   **PostgreSQL-Server:** (Optional) Wird für alle persistenten Daten benötigt. Wenn Sie Spielerprofile, detaillierte Spielstatistiken und Highscores speichern möchten, ist eine Datenbankverbindung erforderlich.

## Installation & Nutzung

### Option A: Für Entwickler (Installation aus dem Quellcode)

Folgen Sie diesen Schritten, wenn Sie den Code selbst ausführen oder weiterentwickeln möchten.

#### Schritt 1: Projekt herunterladen
Öffnen Sie ein Terminal (oder die Kommandozeile/PowerShell unter Windows) und klonen Sie das Repository mit Git an einen Ort Ihrer Wahl.

```bash
git clone https://github.com/ErNuWieda/DartCounter.git
cd DartCounter
```

### Schritt 2: Virtuelle Umgebung einrichten
Eine virtuelle Umgebung isoliert die für dieses Projekt benötigten Python-Pakete von anderen Projekten auf Ihrem System. Dies ist eine bewährte Vorgehensweise.

```bash
# 1. Virtuelle Umgebung im Projektordner erstellen
python3 -m venv .venv

# 2. Umgebung aktivieren
#    - Unter Windows (PowerShell):
#      .\.venv\Scripts\Activate.ps1
#    - Unter Linux/macOS:
source .venv/bin/activate
```
Nach der Aktivierung sollte der Name der Umgebung (z.B. `(.venv)`) am Anfang Ihrer Kommandozeile erscheinen.

### Schritt 3: Notwendige Pakete installieren
Installieren Sie alle Python-Abhängigkeiten, die in der `requirements.txt`-Datei aufgelistet sind.
Die Anwendung ist auch ohne Datenbankverbindung lauffähig. Wenn Sie die optionalen Datenbank-Features (Profile, Statistiken, Highscores) nutzen möchten, installieren Sie die zusätzlichen Pakete.

```bash
# Stellen Sie sicher, dass Ihre virtuelle Umgebung aktiv ist

# Basis-Pakete installieren (immer erforderlich)
pip install -r requirements.txt

# Optionale Pakete für PostgreSQL-Datenbank-Features
# pip install -r requirements-db.txt
```

### Schritt 4: PostgreSQL-Datenbank einrichten (Optional)
Dieser Schritt ist nur notwendig, wenn Sie die Highscore-Funktion nutzen möchten. Wenn Sie dies nicht möchten, können Sie direkt zu **Schritt 5** springen.

#### 4.1. PostgreSQL installieren

*   **Windows:**
    1.  Laden Sie den PostgreSQL-Installer von EDB herunter.
    2.  Führen Sie den Installer aus. Während der Installation werden Sie aufgefordert, ein Passwort für den Superuser (`postgres`) festzulegen. **Merken Sie sich dieses Passwort gut!**
    3.  Die übrigen Einstellungen können auf den Standardwerten belassen werden.

*   **macOS (mit Homebrew):**
```bash
    # PostgreSQL installieren
    brew install postgresql
    # PostgreSQL-Dienst starten
    brew services start postgresql
```

*   **Linux (Debian/Ubuntu):**
```bash
    sudo apt update
    sudo apt install postgresql postgresql-contrib
```

#### 4.2. Datenbank und Benutzer erstellen
Nach der Installation müssen eine Datenbank und ein Benutzer für die Anwendung erstellt werden. Öffnen Sie dazu das `psql`-Terminal:
*   **Windows:** Suchen Sie im Startmenü nach "SQL Shell (psql)" und öffnen Sie es. Bestätigen Sie die Standardwerte für Server, Datenbank, Port und Benutzername mit Enter und geben Sie das bei der Installation festgelegte Passwort ein.
*   **macOS/Linux:** Führen Sie im Terminal `sudo -u postgres psql` aus.

Geben Sie nun die folgenden SQL-Befehle nacheinander ein und bestätigen Sie jeden mit Enter:

```sql
-- Erstellt die Datenbank (der Name ist frei wählbar, muss aber zur config.ini passen)
CREATE DATABASE dartcounter;

-- Erstellt einen neuen Benutzer mit einem Passwort (Namen und Passwort frei wählen)
CREATE USER darter WITH PASSWORD 'TopSecret';

-- Gibt dem neuen Benutzer alle Rechte für die neue Datenbank
GRANT ALL PRIVILEGES ON DATABASE dartcounter TO darter;

-- Verlassen der psql-Shell
\q
```

#### 4.3. Konfigurationsdatei anpassen
1.  Erstellen Sie eine Kopie der Datei `config.ini.example` und nennen Sie diese `config.ini`.
2.  Öffnen Sie die neue `config.ini` und tragen Sie die Zugangsdaten ein, die Sie in Schritt 4.2 festgelegt haben.

3.  **Speicherort der `config.ini`:**
    *   **Für die Entwicklung:** Platzieren Sie die `config.ini` im Hauptverzeichnis des Projekts (neben `main.py`).
    *   **Für eine installierte Anwendung:** Platzieren Sie die `config.ini` im benutzerspezifischen Anwendungsordner, damit sie bei Updates nicht überschrieben wird. Die Anwendung sucht dort zuerst. Sie finden den Ordner hier:
        *   **Windows:** `%APPDATA%\DartCounter` (z.B. `C:\Users\<IhrName>\AppData\Roaming\DartCounter`)
        *   **macOS:** `~/Library/Application Support/DartCounter`
        *   **Linux:** `~/.config/dartcounter`

**Beispiel für `config.ini`:**
```ini
[postgresql]
host = localhost
database = dartcounter
user = darter
password = TopSecret
```

### Schritt 5: Anwendung starten
Stellen Sie sicher, dass Ihre virtuelle Umgebung noch aktiv ist, und starten Sie die Anwendung.

```bash
python3 main.py
```
### Option B: Als ausführbare Datei paketieren (für die Weitergabe)

Wenn Sie eine eigenständige, ausführbare Datei (z.B. eine .exe für Windows) erstellen möchten, die Sie ohne installierte Python-Umgebung an andere weitergeben können, können Sie das mitgelieferte Build-Skript verwenden. Dieses Skript nutzt PyInstaller, um alle notwendigen Code- und Asset-Dateien in ein einziges Paket zu bündeln. 

#### Schritt 1-3: Vorbereitung 
Führen Sie die Schritte 1 bis 3 aus der "Option A" aus, um das Projekt herunterzuladen, eine virtuelle Umgebung einzurichten und die Abhängigkeiten (inklusive pyinstaller) zu installieren.

#### Schritt 4: Build-Skript ausführen 
Stellen Sie sicher, dass Ihre virtuelle Umgebung aktiv ist, und führen Sie dann das Build-Skript aus: 

```bash
python3 build.py
```

Das Skript erledigt automatisch die folgenden Aufgaben: 
1. Es erkennt Ihr Betriebssystem (Windows, macOS oder Linux). 
2. Es bereinigt alte Build-Dateien. 
3. Es führt PyInstaller mit den korrekten Einstellungen aus, um die Anwendung zu bauen. 
4. Es erstellt ein Release-Verzeichnis, kopiert die ausführbare Datei, die README.md und eine config.ini.example hinein. 
5. Es packt alles in eine ZIP-Datei, z.B. DartCounter_Windows_v1.4.0.zip. 
6. Anschließend werden alle temporären Build-Ordner wieder gelöscht. 

#### Schritt 5: Ergebnis finden 
Nachdem das Skript erfolgreich durchgelaufen ist, finden Sie im Hauptverzeichnis des Projekts eine ZIP-Datei. Diese Datei enthält die fertige Anwendung und kann an andere Benutzer weitergegeben werden.

### Option C: Windows-Installer erstellen (mit Inno Setup)

Ein professioneller Windows-Installer (`setup.exe`) wird **automatisch** für jedes GitHub Release erstellt.

Wenn Sie den Installer manuell erstellen möchten:

#### Schritt 1: Inno Setup installieren
Laden und installieren Sie den Inno Setup Compiler von der offiziellen Webseite: https://jrsoftware.org/isinfo.php

#### Schritt 2: Anwendung bauen
Führen Sie das Build-Skript wie in "Option B" beschrieben aus: `python build.py`. Das Skript erstellt ein ZIP-Archiv. Entpacken Sie dieses.

#### Schritt 3: Installer-Skript kompilieren
1.  Öffnen Sie die Datei `installer/create_installer.iss`.
2.  Passen Sie die Platzhalter für Version und Pfad (`!define AppVersion`, `Source: ...`) manuell an.
3.  Kompilieren Sie das Skript mit dem Inno Setup Compiler.

#### Schritt 4: Ergebnis
Inno Setup erstellt eine einzelne `setup.exe`-Datei im `installer/Output`-Verzeichnis. Diese Datei können Sie an Windows-Benutzer weitergeben.

---

## Contributing & Support

Dieses Projekt lebt von der Community. Beiträge sind herzlich willkommen!

*   **Fehler melden & Wünsche äußern:** Erstelle einfach ein [Issue](https://github.com/ErNuWieda/DartCounter/issues).
*   **Code beitragen:** Forke das Repository und erstelle einen [Pull Request](https://github.com/ErNuWieda/DartCounter/pulls).

Wenn dir dieses Projekt gefällt und du die Weiterentwicklung unterstützen möchtest, kannst du dem Entwickler einen Kaffee spendieren. Jede Unterstützung wird sehr geschätzt und hilft, das Projekt am Leben zu erhalten!

<a href="https://paypal.me/ernuwieda" target="_blank"><img src="https://www.paypalobjects.com/de_DE/DE/i/btn/btn_donateCC_LG.gif" alt="Spenden mit PayPal" ></a>

---

## Danksagung

An alle Kaffeetassen, die während der Entwicklung geleert wurden.

Ein besonderer Dank geht an **Gemini Code Assist**. Die Unterstützung durch diesen KI-Coding-Assistenten war bei der Entwicklung, Fehlersuche, Code-Strukturierung und der Erstellung der Dokumentation von unschätzbarem Wert. Zahlreiche Implementierungen und Verbesserungen konnten durch die Vorschläge und Hilfestellungen von Gemini maßgeblich beschleunigt und qualitativ aufgewertet werden.

Ein zwinkernder Dank geht auch an das **'Secret Squirrel'**. Seine unermüdlichen und kreativen Sabotageversuche haben uns gezwungen, jede Zeile Code zu hinterfragen und die Anwendung robuster zu machen, als wir es je für möglich gehalten hätten. Chapeau, kleiner Nager!

## Lizenz

Dieses Projekt steht unter der GNU General Public License v3.0. Details finden Sie in der Datei `LICENSE`.

---

Wir freuen uns über Beiträge, Fehlermeldungen und Vorschläge! Erstelle einfach ein Issue oder einen Pull Request.
Viel Spaß beim Darten! 🎯