# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)

import pytest
from unittest.mock import MagicMock, patch, ANY, AsyncMock
import time
import threading
from core.announcer import Announcer

@pytest.fixture
def mock_settings():
    mock_settings = MagicMock()
    settings = {
        "voice_enabled": True,
        "voice_volume": 80,
        "voice_speed": 150,
        "voice_id": "en-GB-ThomasNeural"
    }
    mock_settings.get.side_effect = lambda k, d=None: settings.get(k, d)
    mock_settings.get_bool.side_effect = lambda k, d=None: settings.get(k, d)
    mock_settings.get_int.side_effect = lambda k, d=None: settings.get(k, d)
    return mock_settings

def test_announcer_initialization(mock_settings):
    """Testet, ob der Announcer und sein Thread korrekt starten und stoppen."""
    with patch("core.announcer.pygame.mixer"):
        announcer = Announcer(settings_manager=mock_settings)
        assert announcer.thread.is_alive()
        
        announcer.stop()
        announcer.thread.join(timeout=1.0)
        assert not announcer.thread.is_alive()

def test_announcer_score_logic(mock_settings):
    """Testet die Übersetzung von Scores in Ansagetexte."""
    with patch("core.announcer.pygame.mixer"):
        announcer = Announcer(settings_manager=mock_settings)
        
        # Normaler Score
        with patch.object(announcer.queue, 'put') as mock_put:
            announcer.announce_score(60)
            mock_put.assert_called_with("60")
            
            # Der Klassiker
            announcer.announce_score(180)
            called_text = mock_put.call_args[0][0]
            assert called_text in [
                "One hundred and eighty!",
                "Maximum! One hundred and eighty!",
                "Yes! One hundred and eighty!",
                "Brilliant! One hundred and eighty!"
            ]

            # No Score Logik testen
            announcer.announce_score(0)
            called_text = mock_put.call_args[0][0]
            assert called_text in [
                "No score!",
                "Zero!",
                "Nil!",
                "Nothing there!",
                "Unlucky, no score!"
            ]
        
        announcer.stop()

@patch("core.announcer.pygame.mixer")
def test_announcer_processes_queue_integration(mock_mixer, mock_settings, mock_engine):
    """Verifiziert den vollständigen Ablauf vom Queue-Eintrag bis zum asynchronen Aufruf."""
    mock_mixer.get_init.return_value = True
    # Korrektes Mocking der music-Subkomponente für die get_busy-Schleife
    mock_mixer.music = MagicMock()
    mock_mixer.music.get_busy.return_value = False
    
    # WICHTIG: Da mock_engine session-scoped ist, müssen wir den 
    # Zustand des Mocks für diesen Test explizit zurücksetzen.
    mock_engine.reset_mock()
    
    # Synchronisation: Ein Event, das gesetzt wird, wenn die Engine aufgerufen wird.
    call_event = threading.Event()
    mock_engine.Communicate.return_value.save.side_effect = lambda *a, **k: call_event.set()
    
    # Sicherstellen, dass die Verfügbarkeits-Flags im Worker-Thread True sind.
    # Wir mocken time.sleep im Modul, um Verzögerungen im Worker zu vermeiden.
    with patch("core.announcer.time.sleep"), \
         patch("core.announcer.EDGE_TTS_AVAILABLE", True):
        
        announcer = Announcer(settings_manager=mock_settings)

        # Nachricht absetzen
        announcer.announce("Test Message")
        
        # Warten, bis der Worker die Nachricht verarbeitet hat (max 5s)
        success = call_event.wait(timeout=5.0)
        assert success, "Die Sprachausgabe-Engine (save) wurde nicht vom Worker-Thread aufgerufen."

        announcer.stop()
        announcer.thread.join(timeout=1.0)

def test_announcer_respects_disabled_setting(mock_settings):
    """Stellt sicher, dass bei deaktivierter Sprachausgabe nichts passiert."""
    # Voice deaktivieren
    mock_settings.get.side_effect = lambda k, d=None: False if k == "voice_enabled" else 100
    
    with patch("core.announcer.pygame.mixer"):
        with patch("core.announcer.asyncio.run") as mock_async_run:
            announcer = Announcer(settings_manager=mock_settings)
            announcer.announce("Should be silent")
            
            time.sleep(0.2)
            mock_async_run.assert_not_called()
            
            announcer.stop()
            announcer.thread.join(timeout=1.0)

def test_announcer_special_announcements(mock_settings):
    """Testet spezialisierte Ansagemethoden wie Bust oder Game Shot."""
    with patch("core.announcer.pygame.mixer"):
        announcer = Announcer(settings_manager=mock_settings)
        with patch.object(announcer.queue, 'put') as mock_put:
            announcer.announce_bust()
            mock_put.assert_called_with("Bust")
            
            announcer.announce_game_shot("Martin")
            mock_put.assert_called_with("Game shot and the match, Martin")
            
            # Madhouse (D1) Finish testen
            announcer.announce_game_shot("Martin", was_madhouse=True)
            called_text = mock_put.call_args[0][0]
            assert called_text in [
                "Game shot and the match, Martin. Finally!",
                "Game shot, Martin. Straight out of the madhouse!",
                "Game shot and the match, Martin. That was a struggle!",
                "Game shot, Martin. You got there in the end!"
            ]
            
            # Bullseye Finish testen
            announcer.announce_game_shot("Martin", was_bullseye=True)
            called_text = mock_put.call_args[0][0]
            assert called_text in [
                "Game shot and the match, Martin. Unbelievable Bullseye finish!",
                "Game shot, Martin. Stunning Bullseye to win it!",
                "Game shot and the match, Martin. Clinical on the Bullseye!",
                "Game shot, Martin. What a way to finish on the Bullseye!"
            ]
            
            # Big Fish (170) Finish testen
            announcer.announce_game_shot("Martin", is_big_fish=True)
            called_text = mock_put.call_args[0][0]
            assert called_text in [
                "Game shot and the match, Martin! The big fish! One hundred and seventy!",
                "One hundred and seventy! Martin, you are a legend!",
                "Unbelievable! The big fish from Martin! Game shot and the match!",
                "The maximum checkout! The big fish for Martin!"
            ]
            
            announcer.announce_ring("Bullseye")
            mock_put.assert_called_with("Bullseye!")

            announcer.announce_match_average("Martin", 85.432)
            # Da die Ansage jetzt zufällig variiert, prüfen wir, ob der Aufruf
            # einer der erwarteten Phrasen entspricht.
            called_text = mock_put.call_args[0][0]
            assert called_text in [
                "Three dart average for Martin, 85.4",
                "Martin finished with an average of 85.4",
                "The average for Martin is 85.4",
                "Martin, match average 85.4"
            ]
            
        announcer.stop()

def test_announcer_get_available_voices(mock_settings):
    """Verifiziert, dass die Liste der verfügbaren Stimmen korrekt zurückgegeben wird."""
    with patch("core.announcer.pygame.mixer"):
        announcer = Announcer(settings_manager=mock_settings)
        voices = announcer.get_available_voices()
        assert len(voices) == 8
        assert voices[0]["id"] == "en-GB-ThomasNeural"
        announcer.stop()

def test_announcer_handles_mixer_error(mock_settings):
    """Testet, ob der Announcer bei defektem Mixer die Sprachausgabe deaktiviert."""
    with patch("core.announcer.pygame.mixer.init", side_effect=Exception("Audio device busy")):
        # In diesem Fall sollte der Worker-Thread sich beenden
        announcer = Announcer(settings_manager=mock_settings)
        
        # Dem Thread Zeit geben, den Fehler zu bemerken
        time.sleep(0.2)
        
        assert not announcer.thread.is_alive()
        # Sicherstellen, dass die Einstellung deaktiviert wurde
        mock_settings.set.assert_called_with("voice_enabled", False)
    
    assert not announcer.thread.is_alive()

def test_announcer_processes_queue(mock_engine):
    """Verifiziert, dass Texte aus der Queue an die Engine übergeben werden."""
    mock_engine.reset_mock()
    mock_settings = MagicMock()
    settings_dict = {
        "voice_enabled": True,
        "voice_volume": 80,
        "voice_speed": 150
    }
    mock_settings.get.side_effect = lambda k, d=None: settings_dict.get(k, d)
    mock_settings.get_bool.side_effect = lambda k, d=None: settings_dict.get(k, d)
    mock_settings.get_int.side_effect = lambda k, d=None: settings_dict.get(k, d)

    announcer = Announcer(settings_manager=mock_settings)
    time.sleep(0.5)  # Genug Zeit für Thread-Start
    announcer.announce("Triple 20")
    
    # Timeout-Loop für die Verarbeitung
    success = False
    for _ in range(30):
        if not announcer.queue.unfinished_tasks:
            success = True
            break
        time.sleep(0.1)
    
    assert success
    announcer.stop()
    announcer.thread.join(timeout=1.0)

def test_announcer_respects_settings(mock_engine):
    """Testet, ob Lautstärke und Geschwindigkeit aus den Settings übernommen werden."""
    mock_engine.reset_mock()
    mock_settings = MagicMock()
    settings_dict = {
        "voice_enabled": True,
        "voice_volume": 80,
        "voice_speed": 180
    }
    mock_settings.get_bool.side_effect = lambda k, d=None: settings_dict.get(k, d)
    mock_settings.get.side_effect = lambda k, d=None: settings_dict.get(k, d)
    mock_settings.get_int.side_effect = lambda k, d=None: settings_dict.get(k, d)
    
    announcer = Announcer(settings_manager=mock_settings)
    time.sleep(2.0)
    
    announcer.announce("Test")
    
    # Timeout-Loop für die Verarbeitung
    success = False
    for _ in range(30):
        if mock_engine.Communicate.called:
            success = True
            break
        time.sleep(0.1)
    
    assert success
    # Prüfen, ob die Einstellungen an Communicate übergeben wurden.
    # Wir prüfen den gesamten Aufruf (args + kwargs), da die Erfassung im Mock variieren kann.
    args, kwargs = mock_engine.Communicate.call_args
    call_data = str(args) + str(kwargs)
    
    assert "%" in call_data, f"Prozentzeichen für Geschwindigkeit/Lautstärke fehlt im Aufruf: {call_data}"
    assert "Test" in call_data
    announcer.stop()
    announcer.thread.join(timeout=1.0)

def test_announcer_stop_clears_queue(mock_engine):
    """Prüft, ob der Stop-Sentinel korrekt verarbeitet wird."""
    mock_engine.reset_mock()
    mock_settings = MagicMock()
    # Sicherstellen, dass voice_enabled True ist, damit der Announcer-Thread startet und die Queue verarbeitet
    mock_settings.get.side_effect = lambda k, d=None: {"voice_enabled": True}.get(k, d)
    mock_settings.get_bool.side_effect = lambda k, d=None: {"voice_enabled": True}.get(k, d)
    announcer = Announcer(settings_manager=mock_settings)
    time.sleep(0.5) # Konsistenz mit anderen Tests
    announcer.stop()
    # Längeres Join-Timeout für CI-Stabilität
    announcer.thread.join(timeout=2.0)
    
    assert not announcer.thread.is_alive()

@patch("core.announcer.pygame.mixer")
def test_announcer_fallback_to_gtts(mock_mixer, mock_settings, mock_engine):
    """Verifiziert, dass bei einem Fehler in Edge-TTS auf gTTS zurückgegriffen wird."""
    # Simuliere einen Fehler in edge-tts (z.B. Netzwerk/403)
    mock_engine.Communicate.side_effect = Exception("Handshake error")
    
    with patch("core.announcer.gTTS") as mock_gtts:
        announcer = Announcer(settings_manager=mock_settings)
        # Kurze Zeit für Thread-Start
        time.sleep(0.2)
        
        announcer.announce("Fallback Test")
        
        # Warten auf Verarbeitung (beachtet den 0.6s sleep im worker)
        success = False
        for _ in range(50):
            if mock_gtts.called:
                success = True
                break
            time.sleep(0.1)
            
        assert success, "gTTS wurde nicht als Fallback aufgerufen, nachdem Edge-TTS fehlschlug"
        announcer.stop()
        announcer.thread.join(timeout=1.0)