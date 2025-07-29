# Projekt-Roadmap für Dartcounter

Dieses Dokument skizziert geplante Features und Verbesserungen für zukünftige Versionen des Dartcounters.

---

## Version 1.2.0 - "The Tournament Edition" (Veröffentlicht)

Dieses Release hat den Dartcounter zu einer vollwertigen, kompetitiven Anwendung gemacht. Der Fokus lag auf der Einführung von Mehrspieler-Turnieren, personalisierbaren Spielerprofilen und erweiterten Statistiken.

- **Implementiert:**
  - **Turnier-Modus:** K.o.-Turniere für bis zu 8 Spieler mit grafischem Turnierbaum.
  - **Spieler-Profile:** Persistente Profile mit Namen, anpassbaren Avataren und Dart-Farben.
  - **Erweiterte Statistiken:** Detaillierte Spiel-Historie pro Spieler, Formkurven-Diagramm und Wurf-Heatmap.
  - **Umfassende Spielmodi:** X01, Cricket, Killer, Shanghai, etc.
  - **Speichern & Laden:** Spiele und Turniere können gespeichert und fortgesetzt werden.
  - **Highscores & Theming:** Optionale Highscore-Datenbank und wählbares helles/dunkles Design.
- **Technisch:** MVC-Architektur, Test-Suite (>160 Tests), professionelles Build-System.

---

## Version 1.3.0 - "The Online Challenge" (In Planung)

Der Fokus für v1.3.0 liegt darauf, den Dartcounter netzwerkfähig zu machen und das Spielen gegen KI-Gegner zu ermöglichen.

### ✨ Geplante Haupt-Features

- **[ ] Online-Mehrspielermodus (Peer-to-Peer):**
  - **[ ] Netzwerk-Schicht:** Implementierung einer robusten Netzwerkkommunikation (z.B. mit Sockets oder einer Bibliothek wie `Twisted`), um Spiel-Events (Wurf, Undo, nächster Spieler) zu serialisieren und zwischen Clients zu synchronisieren.
  - **[ ] UI:** Dialoge zum Hosten eines Spiels und zum Beitreten eines Spiels über eine IP-Adresse.
  - **[ ] Logik:** Anpassung der `Game`-Klasse, um zwischen lokalen und Netzwerk-Inputs zu unterscheiden.
  - **[ ] Fehlerbehandlung:** Graceful Handling von Verbindungsabbrüchen.

- **[ ] KI-Gegner:**
  - **[ ] Logik:** Implementierung einer `AIPlayer`-Klasse, die von `Player` erbt.
  - **[ ] Wurf-Simulation:** Entwicklung einer Logik, die Würfe simuliert, indem sie auf ein Ziel auf dem Board "zielt" und eine Abweichung (Streuung) basierend auf dem Schwierigkeitsgrad anwendet.
  - **[ ] Checkout-Strategie:** Implementierung einer Logik, die es der KI ermöglicht, auf Checkout-Wege zu zielen, wenn sie sich im Finish-Bereich befindet.
  - **[ ] Schwierigkeitsgrade:** Verschiedene Stufen für die KI (Anfänger, Fortgeschritten, Profi), die die Treffsicherheit und die Checkout-Intelligenz beeinflussen.
  - **[ ] UI:** Möglichkeit, im Spiel-Setup einen oder mehrere KI-Gegner hinzuzufügen.

### 🔧 Kleinere Verbesserungen (Quality of Life)

- **[ ] UI:** Überarbeitung des `GameSettingsDialog`, um die Auswahl der Spieloptionen intuitiver zu gestalten.
- **[ ] Sound:** Hinzufügen von mehr Soundvarianten für verschiedene Ereignisse (z.B. High-Scores wie 140, 177).
- **[ ] Statistiken:** Erweiterung der Statistik-Ansicht um Filter- und Sortieroptionen.
