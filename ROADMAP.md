# Dartcounter Deluxe - Roadmap

## ✅ Abgeschlossen (v1.3.x)
- **Adaptive KI-Klone:** Analyse menschlicher Streumuster für realistische Gegner.
- **High-DPI Support:** Dynamische Skalierung für 4K-Monitore.
- **Undo-Persistence:** Rückgängigmachen von Gewinnwürfen bereinigt nun auch die DB.
- **Checkout-Logik:** KI priorisiert nun aktiv das "bevorzugte Double" aus dem Profil.

## 🎯 Kurzfristige Ziele (v1.4.0)
- **Voice Caller:** Integration von Text-to-Speech (gTTS oder pyttsx3), um geworfene Punkte und Checkout-Wege anzusagen ("Caller"-Feeling).
- **Erweiterte Turniere:** Speichern und Laden von Turnieren verbessern, sodass auch abgebrochene Halbfinals robuster wiederhergestellt werden.
- **Animationen:** Sanftere Übergänge beim Einblenden der Dart-Icons auf dem Canvas.

## 🚀 Mittelfristige Ziele (v1.5.0+)
- **Trainings-Modus "Bob's 27":** Spezielles Training für Doppelfelder mit eigener Highscore-Logik.
- **LAN-Multiplayer:** Spielstände über das lokale Netzwerk synchronisieren (z.B. Tablet als Eingabegerät, Fernseher als Scoreboard).
- **Web-Dashboard:** Export der Statistiken als HTML/Grafik für die mobile Ansicht.

## 🏗️ Refactoring & Code Quality (Laufend)
- **Controller-Entkopplung:** Die `Game`-Klasse weiter verschlanken und UI-Logik (Fenster-Management) strikter von der Spiel-Logik trennen.
- **Test-Abdeckung:** Integrationstests für das Laden komplexer Leg/Set-Match-Zustände.

---
*Letztes Update: April 2026*