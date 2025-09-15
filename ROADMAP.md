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

### Version 1.3: Spieltiefe & Professionalisierung
- **Erweiterter Turniermodus:** Implementierung von **Doppel-K.o.-Turnieren**, bei denen Spieler erst nach zwei Niederlagen ausscheiden.
- **Professionelle Match-Formate:** X01-Spiele können nun im **"Best of Legs / Best of Sets"**-Modus gespielt werden.
- **Verbesserte KI-Intelligenz:**
    - **Taktische Cricket-KI:** Die KI analysiert den Punktestand und wählt strategisch zwischen dem Schließen von Feldern und dem Sammeln von Punkten.
    - **Strategische X01-KI:** Die Zielauswahl der KI im Finish-Bereich wurde grundlegend überarbeitet, um menschlicher und strategischer zu agieren (inkl. Setup-Würfe).
- **Poliertes UI & Bugfixes:**
    - **Turnierbaum-Visualisierung:** Die Darstellung wurde mit pixelgenauen Linien und einem Trophäen-Symbol für den Sieger verfeinert.
    - **Profil-Manager:** Der Dialog zur Spieler-Verwaltung wurde für eine bessere Übersichtlichkeit und dynamische Größenanpassung überarbeitet.
    - **Stabiler Turniermodus:** Kritische Fehler in der Turnierlogik wurden behoben, was einen reibungslosen Ablauf sicherstellt.

### Version 1.3.1: Stabilität & Feinschliff
- **Robuste Test-Suite:** Die gesamte Test-Suite wurde stabilisiert, indem fehlerhafte Test-Setups und inkonsistente Mocks korrigiert wurden. Alle 243 Tests laufen nun zuverlässig.
- **Verfeinerte KI-Strategie:** Die Logik der X01-KI wurde weiter verbessert, insbesondere in Bezug auf Setup-Würfe und die Handhabung von Bogey-Nummern.
- **Erweiterte Testabdeckung:** Neue Tests für die `ShanghaiAIStrategy`, `AtcAIStrategy` und die adaptive KI-Logik wurden hinzugefügt, um die Code-Qualität weiter zu erhöhen.
- **Verbesserte Code-Struktur:** Die Strategie-Klassen für X01 und Cricket wurden refaktorisiert, um die Lesbarkeit und Wartbarkeit zu verbessern.

---

## 🚀 Zukünftige Pläne (Version 1.4 und darüber hinaus)

### Langfristige Vision (Auswahl)
- **Online-Freundschaftsspiele & Team-Modus:** Entwicklung einer einfachen Client-Server-Architektur für private Spiele. Dies könnte auch einen Team-Modus umfassen, bei dem menschliche Spieler mit KI-Partnern zufälliger Stärke gegen andere Teams antreten.
- **Erweiterte Statistiken:** Detailliertere Analyse von Trefferquoten auf einzelne Felder (Doubles, Triples).
- **Barrierefreiheit:** Verbesserung der UI für bessere Lesbarkeit und Bedienbarkeit.
- **Lokalisierung:** Unterstützung für weitere Sprachen (z.B. Englisch).