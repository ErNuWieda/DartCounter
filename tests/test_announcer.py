# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)

import pytest
from unittest.mock import MagicMock, patch
import time
import queue
from core.announcer import Announcer

def test_announcer_initialization(mock_engine):
    """Testet, ob der Announcer die Engine im Thread korrekt initialisiert."""
    mock_engine.reset_mock()
    # Fix: SettingsManager muss gültige Standardwerte für float/int casts liefern
    mock_settings = MagicMock()
    # Sicherstellen, dass voice_enabled True ist, damit der Announcer-Thread startet
    settings_dict = {
        "voice_enabled": True,
        "voice_volume": 80,
        "voice_speed": 150
    }
    # Universal-Mock für alle get-Varianten (get, get_bool, get_int, etc.)
    mock_settings.get.side_effect = lambda k, d=None: settings_dict.get(k, d)
    mock_settings.get_bool.side_effect = lambda k, d=None: settings_dict.get(k, d)
    mock_settings.get_int.side_effect = lambda k, d=None: settings_dict.get(k, d)
    
    announcer = Announcer(settings_manager=mock_settings)
    time.sleep(0.5)
    announcer.stop()
    announcer.thread.join(timeout=1.0)
    
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
    time.sleep(1.5)  # Genug Zeit für Thread-Start
    announcer.announce("Triple 20")
    
    # Timeout-Loop für die Verarbeitung
    success = False
    for _ in range(50):
        if mock_engine.say.called:
            success = True
            break
        time.sleep(0.1)
    
    assert success
    mock_engine.say.assert_called_with("Triple 20")
    mock_engine.runAndWait.assert_called()
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
    mock_settings.get.side_effect = lambda k, d=None: settings_dict.get(k, d)
    mock_settings.get_int.side_effect = lambda k, d=None: settings_dict.get(k, d)
    
    announcer = Announcer(settings_manager=mock_settings)
    time.sleep(2.0)
    
    announcer.announce("Test")
    
    # Timeout-Loop für die Verarbeitung
    success = False
    for _ in range(50):
        # Prüfen, ob setProperty gerufen wurde (Reihenfolge in Announcer: rate dann volume)
        if mock_engine.setProperty.called:
            success = True
            break
        time.sleep(0.1)
    
    assert success
    # Prüfen, ob die Properties an der Engine gesetzt wurden
    mock_engine.setProperty.assert_any_call("volume", 0.8)
    mock_engine.setProperty.assert_any_call("rate", 180)
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