import unittest
import sys
import os
from unittest.mock import MagicMock, patch

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.killer import Killer

# --- Mock-Klassen zur Simulation von Abhängigkeiten ---

class MockPlayer:
    """Eine Mock-Klasse für Player, die für Killer-Tests benötigt wird."""
    def __init__(self, name, lifes=3):
        self.name = name
        self.lifes = lifes
        self.life_segment = ""
        self.can_kill = False
        self.killer_throws = 0
        self.throws = []
        self.sb = MagicMock() # Mock für das Scoreboard

    def reset_turn(self):
        self.throws = []

class MockGame:
    """Eine Mock-Klasse für Game, um den Spielzustand zu verwalten."""
    def __init__(self):
        self.end = False
        self.round = 1
        # Mocken der next_player Methode, um Aufrufe zu verfolgen
        self.next_player = MagicMock()

# --- Die eigentliche Test-Klasse ---

class TestKillerLogic(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem einzelnen Test ausgeführt."""
        # Wir patchen messagebox, damit keine echten Fenster aufpoppen
        self.patcher = patch('core.killer.messagebox')
        self.mock_messagebox = self.patcher.start()

        self.mock_game = MockGame()
        self.killer_logic = Killer(self.mock_game)
        
        self.player1 = MockPlayer("Alice")
        self.player2 = MockPlayer("Bob")
        self.players = [self.player1, self.player2]
        
        self.killer_logic.set_players(self.players)

    def tearDown(self):
        """Wird nach jedem Test ausgeführt, um den Patcher zu stoppen."""
        self.patcher.stop()

    def test_set_life_segment_successfully(self):
        """Testet, ob ein Spieler sein Lebensfeld erfolgreich festlegen kann."""
        self.assertEqual(self.player1.life_segment, "")
        
        # Alice wirft auf die 17, um ihr Lebensfeld zu bestimmen
        self.killer_logic._handle_throw(self.player1, "Single", 17, self.players)
        
        self.assertEqual(self.player1.life_segment, "17")
        # Der Zug sollte nach erfolgreicher Festlegung enden
        self.mock_game.next_player.assert_called_once()

    def test_set_life_segment_fails_if_taken(self):
        """Testet, dass ein Lebensfeld nicht gewählt werden kann, wenn es bereits vergeben ist."""
        self.player2.life_segment = "17" # Bob hat die 17 bereits
        
        # Alice versucht, ebenfalls die 17 zu nehmen
        self.killer_logic._handle_throw(self.player1, "Single", 17, self.players)
        
        self.assertEqual(self.player1.life_segment, "") # Sollte leer bleiben
        self.mock_game.next_player.assert_not_called() # Zug endet nicht

    def test_become_killer(self):
        """Testet, ob ein Spieler zum Killer wird, wenn er sein Lebensfeld (Double) trifft."""
        self.player1.life_segment = "16"
        self.assertFalse(self.player1.can_kill)
        
        # Alice trifft Double 16
        self.killer_logic._handle_throw(self.player1, "Double", 16, self.players)
        
        self.assertTrue(self.player1.can_kill)

    def test_killer_takes_life_from_opponent(self):
        """Testet, ob ein Killer einem Gegner ein Leben nehmen kann."""
        self.player1.life_segment = "20"
        self.player1.can_kill = True
        self.player2.life_segment = "19"
        
        initial_lifes_bob = self.player2.lifes
        
        # Alice (Killer) trifft Double 19 (Bobs Lebensfeld)
        self.killer_logic._handle_throw(self.player1, "Double", 19, self.players)
        
        self.assertEqual(self.player2.lifes, initial_lifes_bob - 1)

    def test_killer_hits_self_and_loses_life(self):
        """Testet, ob ein Killer ein Leben verliert, wenn er sein eigenes Lebensfeld trifft."""
        self.player1.life_segment = "20"
        self.player1.can_kill = True
        initial_lifes_alice = self.player1.lifes
        
        # Alice (Killer) trifft ihr eigenes Lebensfeld (Double 20)
        self.killer_logic._handle_throw(self.player1, "Double", 20, self.players)
        
        self.assertEqual(self.player1.lifes, initial_lifes_alice - 1)

    def test_win_condition_last_player_standing(self):
        """Testet die Gewinnbedingung, wenn nur noch ein Spieler übrig ist."""
        self.player1.life_segment = "20"
        self.player1.can_kill = True
        self.player2.life_segment = "19"
        self.player2.lifes = 1 # Bob hat nur noch ein Leben
        
        # Alice eliminiert Bob
        result = self.killer_logic._handle_throw(self.player1, "Double", 19, self.players)
        
        self.assertEqual(self.player2.lifes, 0)
        self.assertTrue(self.mock_game.end)
        self.assertIn("gewinnt Killer", result)

    def test_undo_life_loss(self):
        """Testet, ob die Undo-Funktion einen Lebensverlust korrekt rückgängig macht."""
        self.player1.life_segment = "20"; self.player1.can_kill = True
        self.player2.life_segment = "19"; self.player2.lifes = 3

        # Alice nimmt Bob ein Leben
        self.killer_logic._handle_throw(self.player1, "Double", 19, self.players)
        self.assertEqual(self.player2.lifes, 2)

        # Der Wurf wird rückgängig gemacht
        self.killer_logic._handle_throw_undo(self.player1, "Double", 19, self.players)
        self.assertEqual(self.player2.lifes, 3)

if __name__ == '__main__':
    unittest.main()