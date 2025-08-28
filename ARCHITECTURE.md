# Anwendungsarchitektur

Die Architektur des Dartcounters folgt modernen Designprinzipien, um eine klare Trennung der Verantwortlichkeiten (**Separation of Concerns**), hohe Wartbarkeit und gute Testbarkeit zu gewährleisten. Sie lässt sich am besten als eine Mischung aus **Model-View-Controller (MVC)** und einer **komponentenbasierten Architektur** beschreiben.

---

## 1. Die Kernkomponenten und ihre Rollen

Die Anwendung ist in logische, entkoppelte Komponenten mit klar definierten Aufgaben unterteilt.

#### **App** (in `main.py`) - Der Orchestrator
*   Dies ist der zentrale Einstiegspunkt und die **Haupt-Controller-Klasse** der Anwendung.
*   Sie ist verantwortlich für die Initialisierung des Hauptfensters, der Menüs und aller globalen "Manager"-Klassen (z.B. `SettingsManager`, `SoundManager`).
*   Sie steuert den Lebenszyklus der Anwendung, reagiert auf Menü-Events (z.B. "Neues Spiel", "Laden") und delegiert die Aufgaben an die zuständigen Komponenten. Sie enthält selbst keine detaillierte Spiellogik oder UI-Dialog-Logik.

#### **GameSettingsDialog** (in `core/game_settings_dialog.py`) - Die Spielkonfiguration
*   Dies ist eine eigenständige, gekapselte UI-Komponente (`Toplevel`-Dialog), die alle Widgets und die Logik zur Auswahl von Spielmodus, Spielern und Optionen enthält.
*   Sie wird direkt von der `App`-Klasse aufgerufen und gibt die gewählten Einstellungen als Dictionary zurück, wenn der Benutzer auf "Spiel starten" klickt.

#### **Game** (in `core/game.py`) - Der Spiel-Controller
*   Diese Klasse steuert eine einzelne, aktive Spielsitzung.
*   Sie wird von der `App`-Klasse instanziiert und ist für die Erstellung ihrer eigenen UI-Komponenten (`DartBoard`, `ScoreBoard`) verantwortlich.
*   Sie verwaltet den gesamten Spielzustand (aktueller Spieler, Runde etc.) und hält direkte Referenzen auf ihre UI-Komponenten (z.B. `self.dartboard`).
*   Sie agiert als Vermittler zwischen der UI (z.B. ein Klick auf das Dartboard) und der spezifischen Spiellogik.

#### **Spiellogik-Klassen** (z.B. `X01`, `Cricket` in `core/`) - Die Strategien
*   Jede dieser Klassen implementiert die spezifischen Regeln für einen einzelnen Spielmodus (**Strategy Pattern**).
*   Die `Game`-Klasse wählt mithilfe einer Factory-Methode (`get_game_logic`) die passende Strategie-Klasse aus und delegiert die Verarbeitung von Würfen und die Prüfung von Spielbedingungen (Sieg, Bust) an diese.
*   Sie sind dafür verantwortlich, den Zustand des `Player`-Objekts (z.B. `player.score`, `player.state`, `player.stats`) entsprechend den Spielregeln zu aktualisieren.

#### **UI-Komponenten** (z.B. `DartBoard`, `ScoreBoard`, `AppSettingsDialog`)
*   Dies sind reine **View**-Klassen, die für die Darstellung von Informationen und die Entgegennahme von Benutzereingaben zuständig sind.
*   Sie sind stark entkoppelt und melden Ereignisse (z.B. "Feld X getroffen") an ihren Controller (`Game`), ohne die Spielregeln selbst zu kennen.

#### **Datenmodelle** (z.B. `Player` in `core/player.py`)
*   Klassen wie `Player` dienen als reine **Model**-Klassen (Datencontainer). Sie speichern den Zustand eines Objekts (Name, Punktestand, Statistiken), enthalten aber keine Logik zur Steuerung des Spielablaufs.

#### **Manager & Utilities** (z.B. `SettingsManager`, `SaveLoadManager`, `CheckoutCalculator`)
*   Dies sind spezialisierte Service-Klassen, die jeweils eine einzige, klar definierte Aufgabe erfüllen (**Single Responsibility Principle**). Sie kümmern sich um Persistenz, Sound, Berechnungen etc. und werden von den Controllern bei Bedarf genutzt.

## 2. Datenfluss am Beispiel: "Neues Spiel"

1.  **User-Aktion:** Der Benutzer klickt im Menü der `App` auf "Neues Spiel".
2.  **App (Orchestrator):** Die `new_game()`-Methode wird aufgerufen. Sie instanziiert und öffnet den `GameSettingsDialog`.
3.  **GameSettingsDialog (View):** Der Benutzer wählt Spielmodus und Spieler aus und klickt auf "Spiel starten". Der Dialog speichert die Auswahl in seinem `result`-Attribut und schließt sich.
4.  **App:** Sie liest das `result`-Dictionary aus dem geschlossenen Dialog aus, bereitet die `game_options` vor und ruft `_initialize_game_session()` auf, um eine neue `Game`-Instanz zu erstellen.
5.  **Game (Spiel-Controller):** Der `__init__`-Konstruktor wird ausgeführt. Er...
    *   ...wählt die passende Spiellogik-Klasse (z.B. `X01`) aus.
    *   ...erstellt die `Player`-Instanzen.
    *   ...erstellt seine eigene UI: eine `DartBoard`-Instanz und die `ScoreBoard`-Instanzen für jeden Spieler.
6.  **Spielstart:** Das Spiel ist initialisiert und wartet auf den ersten Wurf.

Dieses Design sorgt für eine robuste, flexible und leicht erweiterbare Anwendung.