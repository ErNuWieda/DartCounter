# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import pyttsx3
import threading
import queue
import time
import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class Announcer:
    """
    Verwaltet die Sprachausgabe (Voice Caller) für das Spiel.
    Nutzt pyttsx3 für Offline-Unterstützung und einen separaten Thread,
    um die UI nicht zu blockieren.
    """

    def __init__(self, settings_manager: Optional["SettingsManager"] = None):
        self.settings_manager = settings_manager
        self.queue = queue.Queue()
        self.stop_event = threading.Event()

        # Thread als Daemon starten, damit er beim Beenden der App automatisch schließt
        self.thread = threading.Thread(target=self._worker, daemon=True, name="AnnouncerThread")
        self.thread.start()

    def _worker(self):
        """Interne Worker-Methode für den Sprachausgabe-Thread."""
        try:
            # Engine im Thread initialisieren (wichtig für Thread-Sicherheit)
            engine = pyttsx3.init()
        except Exception as e:
            logger.error(f"Fehler bei der Initialisierung von pyttsx3: {e}")
            return

        current_voice_id = None
        while not self.stop_event.is_set():
            try:
                # Holen der nächsten Nachricht (blockierend mit Timeout)
                text = self.queue.get(timeout=0.5)
                if text is None:  # Sentinel zum Beenden
                    break

                # Einstellungen prüfen (könnten sich während des Spiels ändern)
                enabled = True
                volume = 1.0
                rate = 150
                target_gender = "Weiblich"

                if self.settings_manager:
                    enabled = self.settings_manager.get("voice_enabled", True)
                    volume = float(self.settings_manager.get("voice_volume", 100)) / 100.0
                    rate = int(self.settings_manager.get("voice_speed", 150))
                    target_gender = self.settings_manager.get("voice_gender", "Weiblich")

                if enabled:
                    try:
                        # Kurze Pause (600ms), damit der Soundeffekt des Pfeileinschlags
                        # nicht von der Sprachansage überlagert wird.
                        time.sleep(0.6)

                        engine.setProperty("rate", rate)
                        engine.setProperty("volume", volume)

                        # Verbessertes Scoring-System zur Stimmen-Auswahl (verhindert Comedy-Effekte)
                        voices = engine.getProperty("voices")
                        selected_voice_id = None
                        scored_voices = []

                        # Bekannte Namen hochwertiger Systemstimmen
                        female_keys = ["female", "zira", "hedda", "anna", "stefanie", "katja", "victoria", "helena", "tanja", "hazel", "sabina"]
                        male_keys = ["male", "david", "stefan", "hans", "mark", "paul", "george", "herbert", "zero", "pavel"]
                        
                        target_keys = female_keys if target_gender == "Weiblich" else male_keys
                        other_keys = male_keys if target_gender == "Weiblich" else female_keys

                        for v in voices:
                            score = 0
                            v_info = (str(v.name) + str(v.id) + str(getattr(v, "gender", ""))).lower()
                            v_langs = [str(l).lower() for l in getattr(v, "languages", [])]

                            # 1. Geschlecht bewerten
                            if any(key in v_info for key in target_keys): score += 100
                            if any(key in v_info for key in other_keys): score -= 80
                            
                            # 2. Sprache bewerten (DE oder EN klingen deutlich natürlicher)
                            if any("de" in l or "en" in l for l in v_langs) or "german" in v_info or "english" in v_info:
                                score += 50
                            
                            scored_voices.append((score, v.id))
                        
                        if scored_voices:
                            # Nimm die Stimme mit der höchsten Punktzahl
                            scored_voices.sort(key=lambda x: x[0], reverse=True)
                            selected_voice_id = scored_voices[0][1]

                        # Nur setzen, wenn sich die Stimme wirklich geändert hat
                        if selected_voice_id and selected_voice_id != current_voice_id:
                            engine.setProperty("voice", selected_voice_id)
                            current_voice_id = selected_voice_id

                        engine.say(text)
                        engine.runAndWait()
                    except Exception as e:
                        logger.error(f"Fehler während der Sprachausgabe: {e}")

                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Unerwarteter Fehler im Announcer-Worker: {e}")

    def announce(self, text: str):
        """Fügt einen Text zur Warteschlange der Sprachausgabe hinzu."""
        if text:
            self.queue.put(str(text))

    def announce_score(self, score: int):
        """Sagt die erzielten Punkte an."""
        self.announce(str(score))

    def announce_bust(self):
        """Kündigt einen Überwurf (Bust) an."""
        self.announce("Bust")

    def announce_player_turn(self, player_name: str):
        """Kündigt an, wer als nächstes am Zug ist."""
        self.announce(player_name)

    def announce_game_shot(self, player_name: str):
        """Kündigt den Sieg an (Klassischer Caller-Spruch)."""
        self.announce(f"Game shot and the match, {player_name}")

    def announce_checkout_path(self, path: str):
        """Sagt einen vorgeschlagenen Checkout-Weg an."""
        if path and path != "-":
            self.announce(path)

    def stop(self):
        """Stoppt den Announcer-Thread sauber."""
        self.stop_event.set()
        self.queue.put(None)