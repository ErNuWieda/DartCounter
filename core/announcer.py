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

import asyncio
import random
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

import threading
import queue
import time
import logging
import io
import os
import tempfile
import pygame
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .settings_manager import SettingsManager

logger = logging.getLogger(__name__)


class Announcer:
    """
    Verwaltet die Sprachausgabe (Voice Caller) für das Spiel.
    Nutzt edge-tts für hochwertige Neural-Stimmen und einen separaten Thread,
    um die UI nicht zu blockieren.
    """

    def __init__(self, settings_manager: Optional["SettingsManager"] = None):
        self.settings_manager = settings_manager
        self.queue = queue.Queue()
        self.stop_event = threading.Event()

        if not EDGE_TTS_AVAILABLE and not GTTS_AVAILABLE:
            logger.warning("Weder 'edge-tts' noch 'gTTS' sind installiert. Sprachausgabe ist deaktiviert.")
            self.available_voices = []
            return
        
        # Stimmen einmalig beim Initialisieren suchen, um Thread-Konflikte zu vermeiden
        self.available_voices = self._discover_voices()

        # Thread als Daemon starten, damit er beim Beenden der App automatisch schließt
        self.thread = threading.Thread(target=self._worker, daemon=True, name="AnnouncerThread")
        self.thread.start()

    def _discover_voices(self) -> list[dict]:
        """Gibt eine kuratierte Liste der besten verfügbaren Online-Neural-Stimmen zurück."""
        return [
            {"id": "en-GB-ThomasNeural", "label": "🇬🇧 Male: Thomas (PDC Style)", "category": "Male"},
            {"id": "en-GB-SoniaNeural", "label": "🇬🇧 Female: Sonia (PDC Style)", "category": "Female"},
            {"id": "en-US-ChristopherNeural", "label": "🇺🇸 Male: Christopher (US)", "category": "Male"},
            {"id": "en-US-JennyNeural", "label": "🇺🇸 Female: Jenny (US)", "category": "Female"},
            {"id": "en-IE-ConnorNeural", "label": "🇮🇪 Male: Connor (Irish)", "category": "Male"},
            {"id": "en-AU-WilliamNeural", "label": "🇦🇺 Robotic: Synth-Aussie", "category": "Robotic"},
            {"id": "de-DE-ConradNeural", "label": "🇩🇪 Male: Conrad (DE)", "category": "Male"},
            {"id": "de-DE-KatjaNeural", "label": "🇩🇪 Female: Katja (DE)", "category": "Female"},
        ]

    def get_available_voices(self) -> list[dict]:
        """Gibt die vorab geladenen Stimmen zurück."""
        return self.available_voices

    async def _async_speak(self, text: str, voice_id: str, volume: int, rate: int):
        """Führt den eigentlichen Online-TTS Aufruf aus und spielt das Audio ab."""
        # Rate in das edge-tts Format (z.B. "+10%", "-20%")
        rate_str = f"{(rate - 150) // 2:+d}%"

        # Wir nutzen eine temporäre Datei, da music.load mit BytesIO unter Linux oft stumm bleibt.
        # Zudem unterstützt pygame.mixer.Sound kein MP3.
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name

        success = False
        try:
            if not voice_id.startswith("google-") and EDGE_TTS_AVAILABLE:
                try:
                    # Edge TTS Handling (Asynchron)
                    communicate = edge_tts.Communicate(text, voice_id, rate=rate_str)
                    await communicate.save(tmp_path)
                    success = True
                except Exception as e:
                    logger.warning(f"Edge-TTS fehlgeschlagen (403?), wechsle zu Fallback: {e}")
            
            # Wenn Edge-TTS fehlgeschlagen ist oder nicht verfügbar ist, nutze gTTS
            if not success and GTTS_AVAILABLE:
                # Sprache basierend auf der Voice-ID raten (Thomas/Sonia sind en-GB)
                # Wir nehmen standardmäßig Englisch, außer es steht explizit 'de' im Namen.
                lang = "de" if "de" in voice_id.lower() else "en"
                tts = gTTS(text=text, lang=lang)
                tts.save(tmp_path)
                success = True
            
            if success and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                # MP3-Daten laden und Lautstärke (0.0 bis 1.0) anwenden
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.set_volume(volume / 100.0)
                pygame.mixer.music.play()
                
                logger.debug(f"Playing TTS: '{text}' mit Stimme '{voice_id}'")
                # Warten, bis die Musik-Wiedergabe beendet ist
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.05)
                pygame.mixer.music.unload() # Wichtig unter Linux, um Datei freizugeben
            else:
                logger.warning("TTS Datei wurde nicht erstellt oder ist leer.")
        except Exception as e:
            logger.error(f"Fehler bei der Online-Sprachausgabe: {e}")
        finally:
            # Aufräumen: Temporäre Datei sofort löschen
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def clear_queue(self):
        """Entfernt alle noch ausstehenden Ansagen aus der Warteschlange."""
        try:
            while not self.queue.empty():
                self.queue.get_nowait()
                self.queue.task_done()
        except queue.Empty:
            pass

    def _worker(self):
        """Interne Worker-Methode für den Sprachausgabe-Thread."""
        # Sicherstellen, dass der Pygame-Mixer bereit ist
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                logger.info("Pygame mixer erfolgreich initialisiert.")
            except Exception as e:
                logger.error(f"Fehler bei der Initialisierung des Pygame mixers: {e}. Sprachausgabe wird deaktiviert.")
                self.settings_manager.set("voice_enabled", False)
                self.stop_event.set() # Signalisiere dem Thread, sich zu beenden
                return # Beende den Worker-Thread, da keine Audio-Wiedergabe möglich ist.

        while not self.stop_event.is_set():
            try:
                # Holen der nächsten Nachricht (blockierend mit Timeout)
                text = self.queue.get(timeout=0.5)
                if text is None:  # Sentinel zum Beenden
                    break

                # Einstellungen prüfen (könnten sich während des Spiels ändern)
                enabled = True
                volume = 100
                rate = 150 # Standard-PDC-Geschwindigkeit
                target_voice_id = "en-GB-ThomasNeural" # Globaler Standard

                if self.settings_manager:
                    enabled = self.settings_manager.get("voice_enabled", True)
                    volume = int(self.settings_manager.get("voice_volume", 100))
                    rate = int(self.settings_manager.get("voice_speed", 150))
                    target_voice_id = self.settings_manager.get("voice_id")

                # Erlaube Sprachausgabe, wenn mindestens ein Dienst verfügbar ist
                if enabled and (EDGE_TTS_AVAILABLE or GTTS_AVAILABLE):
                    try:
                        # Kurze Pause, damit der Soundeffekt des Pfeileinschlags
                        # nicht überlagert wird. Wenn die Queue aber voll ist (>1),
                        # überspringen wir das, um den Rückstau abzuarbeiten.
                        if self.queue.qsize() == 0:
                            time.sleep(0.4)

                        # Fallback falls ID ungültig/alt aus settings.json
                        valid_ids = [v["id"] for v in self.available_voices]
                        if target_voice_id not in valid_ids:
                            target_voice_id = "en-GB-ThomasNeural"

                        # Führe den asynchronen edge-tts Aufruf im Worker-Thread aus
                        asyncio.run(self._async_speak(text, target_voice_id, volume, rate))
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
        if score == 180:
            phrases = [
                "One hundred and eighty!",
                "Maximum! One hundred and eighty!",
                "Yes! One hundred and eighty!",
                "Brilliant! One hundred and eighty!"
            ]
            self.announce(random.choice(phrases))
        elif score == 0:
            phrases = [
                "No score!",
                "Zero!",
                "Nil!",
                "Nothing there!",
                "Unlucky, no score!"
            ]
            self.announce(random.choice(phrases))
        else:
            self.announce(str(score))

    def announce_ring(self, ring_name: str):
        """Sagt spezielle Ring-Treffer sofort an."""
        if ring_name == "Bullseye":
            self.announce("Bullseye!")
        elif ring_name == "Bull":
            self.announce("Twenty five")

    def announce_bust(self):
        """Kündigt einen Überwurf (Bust) an."""
        self.announce("Bust")

    def announce_player_turn(self, player_name: str):
        """Kündigt an, wer als nächstes am Zug ist."""
        self.announce(player_name)

    def announce_game_shot(self, player_name: str, was_madhouse: bool = False, was_bullseye: bool = False, is_big_fish: bool = False):
        """Kündigt den Sieg an (Klassischer Caller-Spruch)."""
        # Bei einem Sieg löschen wir den Rückstau an alten Scores,
        # damit der Siegesspruch sofort kommt.
        self.clear_queue()
        
        if is_big_fish:
            phrases = [
                f"Game shot and the match, {player_name}! The big fish! One hundred and seventy!",
                f"One hundred and seventy! {player_name}, you are a legend!",
                f"Unbelievable! The big fish from {player_name}! Game shot and the match!",
                f"The maximum checkout! The big fish for {player_name}!"
            ]
            self.announce(random.choice(phrases))
        elif was_bullseye:
            phrases = [
                f"Game shot and the match, {player_name}. Unbelievable Bullseye finish!",
                f"Game shot, {player_name}. Stunning Bullseye to win it!",
                f"Game shot and the match, {player_name}. Clinical on the Bullseye!",
                f"Game shot, {player_name}. What a way to finish on the Bullseye!"
            ]
            self.announce(random.choice(phrases))
        elif was_madhouse:
            phrases = [
                f"Game shot and the match, {player_name}. Finally!",
                f"Game shot, {player_name}. Straight out of the madhouse!",
                f"Game shot and the match, {player_name}. That was a struggle!",
                f"Game shot, {player_name}. You got there in the end!"
            ]
            self.announce(random.choice(phrases))
        else:
            self.announce(f"Game shot and the match, {player_name}")

    def announce_checkout_path(self, path: str):
        """Sagt einen vorgeschlagenen Checkout-Weg an."""
        if path and path != "-":
            self.announce(path)

    def announce_match_average(self, player_name: str, average: float):
        """Kündigt den 3-Dart-Average des Spielers am Ende des Matches an."""
        # Auf eine Nachkommastelle runden für eine flüssige Ansage
        rounded_avg = round(float(average), 1)
        avg_str = str(rounded_avg)

        phrases = [
            f"Three dart average for {player_name}, {avg_str}",
            f"{player_name} finished with an average of {avg_str}",
            f"The average for {player_name} is {avg_str}",
            f"{player_name}, match average {avg_str}"
        ]
        self.announce(random.choice(phrases))

    def stop(self):
        """Stoppt den Announcer-Thread sauber."""
        self.stop_event.set()
        self.queue.put(None)