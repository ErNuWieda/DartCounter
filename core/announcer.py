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

                if self.settings_manager:
                    enabled = self.settings_manager.get("voice_enabled", True)
                    volume = float(self.settings_manager.get("voice_volume", 100)) / 100.0
                    rate = int(self.settings_manager.get("voice_speed", 150))

                if enabled:
                    try:
                        engine.setProperty("rate", rate)
                        engine.setProperty("volume", volume)
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