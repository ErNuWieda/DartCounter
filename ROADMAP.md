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
- **Turniermodus:** Implementierung Turniersysteme (K.o. und Doppel-K.o.) mit grafischem Turnierbaum.
- **Statistiken & Highscores:** Einführung einer Datenbank zur Speicherung von Spielerstatistiken (Average, MPR) und Highscores.
- **UI-Verbesserungen:** Hinzufügen eines dunklen Themes, Soundeffekten und einer überarbeiteten Spielerverwaltung.
- **Speichern & Laden:** Möglichkeit, laufende Spiele und Turniere zu speichern und fortzusetzen.
- **Qualitätssicherung:** Aufbau einer umfassenden Test-Suite mit `pytest`.

### Aktueller Stand (Post-1.2)
- **Adaptive KI ('KI-Klon'):** Die KI kann nun die Wurf-Charakteristiken (Genauigkeit, Streuung) menschlicher Spieler lernen und imitieren, um einen realistischen Sparringspartner zu erschaffen.
- **Intelligente Wurfstrategie:** Die KI-Logik wurde grundlegend überarbeitet und agiert nun strategisch im Finish-Bereich, inklusive sicherer Setup-Würfe und der Vermeidung von "Bogey"-Zahlen.
- **Stabiler Turniermodus:** Kritische Fehler in der Turnierlogik wurden behoben, was einen reibungslosen Ablauf von Anfang bis Ende sicherstellt.
- **Poliertes UI:** Dialoge und Ansichten (Profil-Manager, Turnierbaum) wurden verfeinert für eine bessere Benutzererfahrung.

---

## 🚀 Zukünftige Pläne (Version 1.3 und darüber hinaus)

### Kurzfristige Ziele
- **Erweiterte KI-Strategie (Cricket):** Die Cricket-KI soll lernen, den Punktestand der Gegner zu berücksichtigen, um aggressiver oder defensiver zu spielen.
- **Weitere Spielmodi:** Implementierung von "Legs" und "Sets" innerhalb von X01-Spielen.
- **Turnier-Optionen:** Auswahlmöglichkeit zwischen "Einfach-K.o." und "Doppel-K.o." im Turnier-Setup-Dialog.

### Langfristige Vision
- **Online-Freundschaftsspiele & Team-Modus:** Entwicklung einer einfachen Client-Server-Architektur für private Spiele. Dies könnte auch einen Team-Modus umfassen, bei dem menschliche Spieler mit KI-Partnern zufälliger Stärke gegen andere Teams antreten.
- **Erweiterte Statistiken:** Detailliertere Analyse von Trefferquoten auf einzelne Felder (Doubles, Triples).
- **Barrierefreiheit:** Verbesserung der UI für bessere Lesbarkeit und Bedienbarkeit.
- **Lokalisierung:** Unterstützung für weitere Sprachen (z.B. Englisch).