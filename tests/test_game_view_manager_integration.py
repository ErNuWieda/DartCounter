import pytest
from unittest.mock import MagicMock, patch
from core.game_view_manager import GameViewManager
from core.throw_result import ThrowResult
from core.player import Player

@pytest.fixture
def gvm_with_mocks(tk_root_session):
    """
    Richtet einen GameViewManager mit gemockten Komponenten für Integrationstests ein.
    """
    mock_controller = MagicMock()
    mock_options = MagicMock()
    mock_options.name = "501"
    
    mock_sound_manager = MagicMock()
    mock_settings_manager = MagicMock()
    # Standard: Visuelle Effekte sind an
    mock_settings_manager.get.side_effect = lambda k, d=True: True if k == "visual_effects_enabled" else d
    
    mock_announcer = MagicMock()
    
    # DartBoard und Scoreboard-Setup patchen, um Tkinter-Komplexität zu vermeiden
    with patch("core.game_view_manager.DartBoard"), \
         patch("core.game_view_manager.setup_scoreboards"):
        
        view_manager = GameViewManager(
            root=tk_root_session,
            game_controller=mock_controller,
            game_options=mock_options,
            players=[],
            sound_manager=mock_sound_manager,
            settings_manager=mock_settings_manager,
            is_tournament_match=False,
            on_game_end_callback=MagicMock(),
            announcer=mock_announcer
        )
        
        # Das echte Dartboard durch einen Mock ersetzen für Funktionsprüfungen
        view_manager.dartboard = MagicMock()
        
        return view_manager

class TestGameViewManagerIntegration:
    """
    Integrationstests für den GameViewManager, um die Kette vom Wurf-Feedback
    zu Sounds, Ansagen und Overlays zu prüfen.
    """

    def test_feedback_for_maximum_180(self, gvm_with_mocks):
        """Prüft, ob ein 180er Score die korrekte Ansage und das Overlay triggert."""
        gvm = gvm_with_mocks
        player = MagicMock(spec=Player)
        player.throws = [
            ("Triple", 20, (0.1, 0.1)),
            ("Triple", 20, (0.1, 0.1)),
            ("Triple", 20, (0.1, 0.1))
        ]
        
        # Simuliere die Score-Berechnung im Controller
        gvm.game_controller.get_score.side_effect = lambda r, s: 60 if r == "Triple" and s == 20 else 0
        
        result = ThrowResult(status="ok", sound="hit")
        
        gvm.display_throw_feedback(result, player, auto_close_ms=0)
        
        # Verify Sound
        gvm.sound_manager.play_hit.assert_called_once()
        
        # Verify Announcer (Score wird erst nach dem 3. Dart angesagt)
        gvm.announcer.announce_score.assert_called_once_with(180)
        
        # Verify Visual Overlay
        gvm.dartboard.show_180_effect.assert_called_once()

    def test_feedback_for_big_fish_finish(self, gvm_with_mocks):
        """Prüft das legendäre 170er Finish (Big Fish)."""
        gvm = gvm_with_mocks
        player = MagicMock(spec=Player)
        player.name = "Martin"
        player.throws = [
            ("Triple", 20, (0, 0)),
            ("Triple", 20, (0, 0)),
            ("Bullseye", 50, (0, 0))
        ]
        
        result = ThrowResult(status="win", message="Big Fish!", sound="win")
        
        # Patch root.after because gvm.root is a real Tk object in this fixture
        with patch.object(gvm.root, 'after') as mock_after:
            gvm.display_throw_feedback(result, player, auto_close_ms=0)
            
            # Verify win sound played immediately
            gvm.sound_manager.play_win.assert_called_once()
            
            # Verify Announcer call with correct flags
            gvm.announcer.announce_game_shot.assert_called_once_with(
                "Martin", was_madhouse=False, was_bullseye=True, is_big_fish=True
            )
            
            # Verify visual effect
            gvm.dartboard.show_big_fish_effect.assert_called_once()
            
            # Verify delayed special sound for big fish (1.5s delay)
            mock_after.assert_any_call(1500, gvm.sound_manager.play_big_fish)

    def test_feedback_for_bust(self, gvm_with_mocks):
        """Prüft, ob beim Überwerfen die richtigen Aktionen ausgelöst werden."""
        gvm = gvm_with_mocks
        player = MagicMock(spec=Player)
        
        result = ThrowResult(status="bust", sound="bust", message="Busted!")
        
        gvm.display_throw_feedback(result, player, auto_close_ms=0)
        
        gvm.sound_manager.play_bust.assert_called_once()
        gvm.announcer.announce_bust.assert_called_once()
        gvm.dartboard.show_no_score_effect.assert_called_once_with(is_bust=True)

    def test_pdc_style_immediate_bullseye_announcement(self, gvm_with_mocks):
        """Verifiziert, dass Bullseye-Treffer (wie im TV) sofort angesagt werden."""
        gvm = gvm_with_mocks
        player = MagicMock(spec=Player)
        player.throws = [("Bullseye", 50, (0, 0))] # Erster Dart
        
        result = ThrowResult(status="ok", sound="hit")
        
        gvm.display_throw_feedback(result, player, auto_close_ms=0)
        
        # PDC-Style: Bullseye wird sofort angesagt
        gvm.announcer.announce_ring.assert_called_once_with("Bullseye")
        # Score wird noch nicht angesagt
        gvm.announcer.announce_score.assert_not_called()

    def test_low_score_effect(self, gvm_with_mocks):
        """Prüft den Effekt für einen sehr niedrigen Score (z.B. 3 Punkte nach 3 Darts)."""
        gvm = gvm_with_mocks
        player = MagicMock(spec=Player)
        player.throws = [
            ("Single", 1, (0, 0)),
            ("Single", 1, (0, 0)),
            ("Single", 1, (0, 0))
        ]
        # Controller liefert 1+1+1 = 3
        gvm.game_controller.get_score.side_effect = lambda r, s: s
        
        result = ThrowResult(status="ok", sound="hit")
        
        gvm.display_throw_feedback(result, player, auto_close_ms=0)
        
        # Announcer sagt "3"
        gvm.announcer.announce_score.assert_called_once_with(3)
        # Visueller Low-Score Effekt
        gvm.dartboard.show_low_score_effect.assert_called_once()

    def test_feedback_for_madhouse_win(self, gvm_with_mocks):
        """Prüft die Ansage bei einem Sieg über Doppel-1 (Madhouse)."""
        gvm = gvm_with_mocks
        player = MagicMock(spec=Player)
        player.name = "Bob"
        player.throws = [("Double", 1, (0, 0))]
        
        result = ThrowResult(status="win", sound="win")
        
        gvm.display_throw_feedback(result, player, auto_close_ms=0)
        
        # Madhouse-Flag muss True sein
        gvm.announcer.announce_game_shot.assert_called_once_with(
            "Bob", was_madhouse=True, was_bullseye=False, is_big_fish=False
        )