# Projekt-Roadmap für Dartcounter Deluxe

Dieses Dokument skizziert den bisherigen Entwicklungsfortschritt und die geplanten zukünftigen Features für den Dartcounter.

---

## ✅ Abgeschlossene Meilensteine

### Version 1.0: Grundgerüst & Kernfunktionalität
- Implementierung der Basis-Spielmodi (301, 501).
- Klickbares Dartboard zur Wurfeingabe.
- Grundlegende Scoreboards für die Spieler.

### Version 1.1: Erweiterung der Spielmodi & Profile
- Hinzufügen weiterer Spielmodi (Cricket, Micky Maus, etc.).
- Einführung von persistenten Spielerprofilen mit Namen und Farbe.
- Erste Version einer KI mit einfacher Wurflogik.

### Version 1.2: Professionalisierung & Features
- **Turniermodus:** Implementierung eines K.o.-Turniersystems mit grafischem Turnierbaum.
- **Statistiken & Highscores:** Einführung einer Datenbank zur Speicherung von Spielerstatistiken (Average, MPR) und Highscores.
- **UI-Verbesserungen:** Hinzufügen eines dunklen Themes, Soundeffekten und einer überarbeiteten Spielerverwaltung.
- **Speichern & Laden:** Möglichkeit, laufende Spiele und Turniere zu speichern und fortzusetzen.
- **Qualitätssicherung:** Aufbau einer umfassenden Test-Suite mit `pytest`.

### Aktueller Stand (Post-1.2)
- **Intelligente KI:** Die KI-Logik wurde grundlegend überarbeitet und agiert nun strategisch im Finish-Bereich.
- **Stabiler Turniermodus:** Kritische Fehler in der Turnierlogik wurden behoben, was einen reibungslosen Ablauf von Anfang bis Ende sicherstellt.
- **Poliertes UI:** Dialoge und Ansichten (Profil-Manager, Turnierbaum) wurden verfeinert für eine bessere Benutzererfahrung.

---

## 🚀 Zukünftige Pläne (Version 1.3 und darüber hinaus)

### Kurzfristige Ziele
- **Strategische KI-Positionierung:** Die KI soll lernen, auf "sichere" Bereiche eines Segments zu zielen (z.B. die Innenseite der T20, um die 5 und 1 zu vermeiden).
- **Weitere Spielmodi:** Implementierung von "Legs" und "Sets" innerhalb von X01-Spielen.

### Langfristige Vision
- **Online-Modus:** Entwicklung einer Client-Server-Architektur, um Online-Spiele gegen andere zu ermöglichen.
- **Erweiterte Statistiken:** Detailliertere Analyse von Trefferquoten auf einzelne Felder (Doubles, Triples).
- **Barrierefreiheit:** Verbesserung der UI für bessere Lesbarkeit und Bedienbarkeit.
- **Lokalisierung:** Unterstützung für weitere Sprachen (z.B. Englisch).