import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.game import Game


class TestGameWithX01(unittest.TestCase):

    def setUp(self):
        """Wird vor jedem Test ausgeführt."""
        # Wir "patchen" messagebox, damit keine echten Fenster aufpoppen
        self.patcher = patch('core.game.messagebox')
        self.mock_messagebox = self.patcher.start()

        # Mocks für alle externen Abhängigkeiten erstellen
        self.mock_root = MagicMock()
        self.mock_sound_manager = MagicMock()
        self.mock_highscore_manager = MagicMock()
        self.mock_player_stats_manager = MagicMock()

        player_names = ["Alice", "Bob", "Charlie"]
        game_options = {
            "name": "301",
            "opt_in": "Single",
            "opt_out": "Double",
            "opt_atc": "Single",
            "count_to": "301",
            "lifes": "3",
            "rounds": "7"
        }
        
        # Wir mocken die Scoreboard-Erstellung, da sie UI erzeugt
        with patch('core.game.ScoreBoard'):
            self.game = Game(
                self.mock_root, 
                game_options, 
                player_names, 
                self.mock_sound_manager, 
                self.mock_highscore_manager, 
                self.mock_player_stats_manager
            )
        
        # Manuelles Zuweisen von IDs, um die `leave`-Methode zuverlässig testen zu können
        self.game.players[0].id = 101 # Alice
        self.game.players[1].id = 102 # Bob
        self.game.players[2].id = 103 # Charlie

    def tearDown(self):
        """Wird nach jedem Test ausgeführt, um den Patcher zu stoppen."""
        self.patcher.stop()

    def test_initial_state(self):
        """Testet den korrekten Anfangszustand des Spiels."""
        self.assertEqual(self.game.name, "301")
        self.assertEqual(len(self.game.players), 3)
        self.assertEqual(self.game.current_player().name, "Alice")
        self.assertEqual(self.game.round, 1)
        for player in self.game.players:
            self.assertEqual(player.score, 301)

    def test_full_turn_and_next_player(self):
        """Simuliert einen vollen Zug und einen kompletten Rundenwechsel."""
        alice = self.game.current_player()
        self.assertEqual(alice.name, "Alice")

        # Wir mocken die Spiellogik, um uns auf die Game-Klasse zu konzentrieren
        self.game.game._handle_throw = MagicMock()

        # Alice wirft 3 Darts
        self.game.throw("Triple", 20)
        self.game.throw("Single", 20)
        self.game.throw("Single", 5)
        
        self.assertEqual(len(alice.throws), 3)

        # Wechsel zum nächsten Spieler
        self.game.next_player()
        bob = self.game.current_player()
        self.assertEqual(bob.name, "Bob")
        self.assertEqual(self.game.round, 1)

        # Komplette Runde durchlaufen
        self.game.next_player() # zu Charlie
        self.assertEqual(self.game.current_player().name, "Charlie")
        self.assertEqual(self.game.round, 1)

        self.game.next_player() # zurück zu Alice
        self.assertEqual(self.game.current_player().name, "Alice")
        self.assertEqual(self.game.round, 2, "Nach einem vollen Durchlauf sollte eine neue Runde beginnen.")

    def test_remove_player(self):
        """Testet das Entfernen von Spielern aus dem Spiel."""
        # Anfangszustand: [Alice, Bob, Charlie], current=0 (Alice)
        self.assertEqual(len(self.game.players), 3)
        
        # 1. Entferne einen Spieler, der nicht am Zug ist (Charlie)
        self.game.leave(player_id=103)
        self.assertEqual(len(self.game.players), 2)
        self.assertEqual([p.name for p in self.game.players], ["Alice", "Bob"])
        self.assertEqual(self.game.current_player().name, "Alice", "Der aktuelle Spieler sollte sich nicht ändern.")

        # 2. Entferne den aktuellen Spieler (Alice)
        self.game.leave(player_id=101)
        self.assertEqual(len(self.game.players), 1)
        self.assertEqual(self.game.players[0].name, "Bob")
        self.assertEqual(self.game.current_player().name, "Bob", "Der nächste Spieler sollte nun am Zug sein.")
        self.mock_messagebox.showinfo.assert_called() # Es sollte eine Nachricht angezeigt werden

    def test_undo_dispatches_to_logic_handler(self):
        """Testet, ob game.undo() den Aufruf an den Spiellogik-Handler weiterleitet."""
        player = self.game.current_player()
        player.throws.append(("Triple", 20))
        
        # Mocken der Methoden, die aufgerufen werden sollen
        self.game.game._handle_throw_undo = MagicMock()
        self.game.db = MagicMock() # Mocken der Dartboard-Instanz

        self.game.undo()

        # Überprüfen, ob die Undo-Methode des Logik-Handlers aufgerufen wurde
        self.game.game._handle_throw_undo.assert_called_once_with(player, "Triple", 20, self.game.players)
        # Überprüfen, ob die clear-Methode des Dartboards aufgerufen wurde
        self.game.db.clear_last_dart_image_from_canvas.assert_called_once()

    def test_stat_recording_on_win(self):
        """Testet, ob Statistiken bei einem Sieg korrekt erfasst werden."""
        winner = self.game.current_player()
        
        # Mocken der throw-Methode des Logik-Handlers, um eine Gewinnnachricht zurückzugeben
        self.game.game._handle_throw = MagicMock(return_value=f"🏆 {winner.name} gewinnt!")
        
        # Mocken der Statistik-Methoden des Spielers für vorhersagbare Ergebnisse
        winner.get_average = MagicMock(return_value=85.5)
        winner.get_checkout_percentage = MagicMock(return_value=50.0)
        winner.stats = {'highest_finish': 120}

        # Simuliere den Gewinnwurf
        self.game.throw("Double", 20)

        # Überprüfen, ob der Stats-Manager aufgerufen wurde
        self.mock_player_stats_manager.add_game_record.assert_called()
        
        # Überprüfen der Argumente für den Gewinner
        # Der Manager wird für alle Spieler aufgerufen, wir suchen den Aufruf für den Gewinner
        winner_call_found = False
        for call in self.mock_player_stats_manager.add_game_record.call_args_list:
            player_name_arg, stats_dict_arg = call.args
            if player_name_arg == winner.name:
                winner_call_found = True
                self.assertTrue(stats_dict_arg['win'])
                self.assertEqual(stats_dict_arg['game_mode'], '301')
                self.assertEqual(stats_dict_arg['average'], 85.5)
                break
        
        self.assertTrue(winner_call_found, "Statistikaufzeichnung für den Gewinner wurde nicht gefunden.")

if __name__ == '__main__':
    unittest.main()