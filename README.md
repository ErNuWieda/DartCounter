# Dartcounter Deluxe

Ein einfacher, aber funktionsreicher Dart-Zähler, entwickelt mit Python und Tkinter.
Dieses Projekt zielt darauf ab, eine benutzerfreundliche Oberfläche für verschiedene Dartspiele zu bieten, um das manuelle Zählen von Punkten zu ersetzen.

## Features

*   **Verschiedene Spielmodi:**
    *   **x01 Spiele:** 301, 501, 701 mit Optionen für:
        *   Opt-In: Single, Double, Masters
        *   Opt-Out: Single, Double, Masters
    *   **Cricket:** Standard Cricket und Cut Throat Cricket
    *   **Tactics:** Erweiterte Cricket-Variante (Ziele 10-20 und Bull).
    *   **Around the Clock (ATC):** Mit Varianten für Single, Double, Triple als Ziel
    *   **Micky Maus:** Treffen der Zahlen 20 bis 12 und Bullseye.
    *   **Killer:** Jeder Spieler erhält ein Lebensfeld; Ziel ist es, "Killer" zu werden und andere Spieler zu eliminieren.
    *   **Elimination:** Jeder Spieler spielt von einem Startscore (z. B. 301) auf 0 – trifft man exakt den Punktestand eines Gegners, wird dieser zurückgesetzt.

    *   **Shanghai:** Jeder Spieler versucht mit genau drei Darts die Zahlen 1 bis 7 (oder bis 20 bzw. Anzahl vereinbarter Runden) der Reihe nach zu treffen – idealerweise mit einem Single, Double und Triple derselben Zahl in einer Runde, was sofort zum Sieg führt (ein sogenannter "Shanghai")    
*   **Spielerverwaltung:** Unterstützung für bis zu 4 Spieler mit individuellen Namen.
*   **Grafisches Dartboard:** Klickbares Dartboard zur Eingabe der Würfe.
*   **Individuelle Scoreboards:** Jeder Spieler erhält ein eigenes Fenster zur Anzeige des Spielstands und der Wurfhistorie.
*   **Visuelle Dart-Anzeige:** Getroffene Felder werden mit einem Dart-Symbol auf dem Board markiert.
![Startfenster](./assets/screenshot_dc3.png)
![Spiel-Einstellungen](./assets/screenshot_dc2.png)
![Board, Hits & Scoreboard](./assets/screenshot_dc1.png) 

## Installation & Ausführung

1.  **Voraussetzungen:**
    *   Python 3.x
    *   Pillow (PIL Fork): `pip install Pillow`
    *   Tkinter (ist normalerweise bei Standard-Python-Installationen dabei)

2.  **Klonen des Repositories:**
    ```bash
    git clone https://github.com/ErNuWieda/DartCounter.git
    cd dartcounter
    ```

3.  **Starten der Anwendung:**
    ```bash
    python main.py
    ```

## TODO - Zukünftige Features & Verbesserungen

Das Projekt befindet sich in aktiver Entwicklung. Hier sind einige geplante Features und Bereiche für Verbesserungen:

*   **[X] Elimination-Spielmodus:** Implementierung des „Mensch ärgere dich nicht“-ähnlichen Punktespiels mit Reset-Mechanik.
*   **[ ] Erweiterte Shanghai-Finish-Logik (x01):** Korrekte Erkennung eines Shanghai-Finish (Single, Double, Triple desselben Segments in einer Runde) für x01-Spiele. 
*   **[ ] Verbesserung Undo:** Implementierung der Undo-Funktion für "Finish"-Darts
*   **[ ] Spielerstatistiken:** Erfassung und Anzeige von Statistiken (z.B. Averages, Checkout-Quoten, höchste Würfe).
*   **[ ] Highscore-Listen:**
    *   **[ ] Implementierung einer Highscore-Liste pro Spielmodus.**
    *   **[ ] Anbindung an eine PostgreSQL-Datenbank zur persistenten Speicherung der Highscores.**
*   **[ ] Soundeffekte:** Optionale Soundeffekte für Treffer, Busts, Spielgewinn etc.
*   **[ ] UI/UX Verbesserungen:**
    *   Modernisierung des Designs.
    *   Verbesserte Fehlerbehandlung und Nutzerfeedback.
*   **[ ] Speichern/Laden von Spielständen:** Vollständige Implementierung der Möglichkeit, laufende Spiele zu speichern und später fortzusetzen.
*   **[ ] Konfigurierbare Regeln:** Mehr Flexibilität bei der Einstellung von Spielregeln (z.B. benutzerdefinierte x01 Startpunkte).
*   **[ ] Code-Refactoring & Optimierungen:**
    *   Weitere Modularisierung und Vereinfachung von Code-Abschnitten.
*   **[ ] Ausführliche Testabdeckung:** Erstellung von Unit-Tests und Integrationstests.

## Danksagung

Ein besonderer Dank geht an **Gemini Code Assist**. Die Unterstützung durch diesen KI-Coding-Assistenten war bei der Entwicklung, Fehlersuche, Strukturierung des Codes und der Erstellung von Dokumentation von unschätzbarem Wert. Viele der Implementierungen und Verbesserungen wurden durch die Vorschläge und Hilfestellungen von Gemini maßgeblich beschleunigt und qualitativ verbessert.

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Details finden Sie in der Datei `LICENSE`.

---

Wir freuen uns über Beiträge, Fehlermeldungen und Vorschläge! Erstelle einfach ein Issue oder einen Pull Request.
Viel Spaß beim Darten! 🎯