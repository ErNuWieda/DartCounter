import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import tkinter as tk

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.game import Game


class TestGameWithX01(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Erstellt eine einzige, versteckte Tk-Wurzel für alle Integrationstests in dieser Klasse."""
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        """Zerstört die Tk-Wurzel, nachdem alle Tests beendet sind."""
        if cls.root:
            cls.root.destroy()
            cls.root = None

    def setUp(self):
        """Wird vor jedem Test ausgeführt."""
        # Wir "patchen" die zentralen UI-Utility-Funktionen, damit keine echten Fenster aufpoppen.
        self.patcher_show = patch('core.game.ui_utils.show_message')
        self.patcher_ask = patch('core.game.ui_utils.ask_question')
        self.mock_show_message = self.patcher_show.start()
        self.mock_ask_question = self.patcher_ask.start()

        # Mocks für alle externen Abhängigkeiten erstellen
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
        
        # Wir mocken die gesamte GameUI-Klasse, da sie alle UI-Fenster erzeugt
        with patch('core.game.GameUI'):
            self.game = Game(
                self.root, 
                game_options, 
                player_names, 
                self.mock_sound_manager, 
                self.mock_highscore_manager, 
                self.mock_player_stats_manager
            )
        
        # Manuelles Zuweisen von IDs, um die `leave`-Methode zuverlässig testen zu können
        self.game.players[0].id = 101 # Alice
        self.game.players[1].id = 102 # Bob
        # Da GameUI gemockt ist, müssen wir die Scoreboards manuell mocken
        for p in self.game.players:
            p.sb = MagicMock()

        self.game.players[2].id = 103 # Charlie

    def tearDown(self):
        """Wird nach jedem Test ausgeführt, um den Patcher zu stoppen."""
        self.patcher_show.stop()
        self.patcher_ask.stop()
        # Zerstöre die Spielinstanz und alle zugehörigen UI-Fenster,
        # um Ressourcenlecks und hängende Tests zu vermeiden.
        if self.game:
            self.game.destroy()

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
        self.mock_show_message.assert_called() # Es sollte eine Nachricht angezeigt werden

    def test_undo_dispatches_to_logic_handler(self):
        """Testet, ob game.undo() den Aufruf an den Spiellogik-Handler weiterleitet."""
        player = self.game.current_player()
        player.throws.append(("Triple", 20))
        
        # Mocken der Methoden, die aufgerufen werden sollen
        self.game.game._handle_throw_undo = MagicMock() # Mock für die Spiellogik
        self.game.ui = MagicMock() # Mocken der gesamten UI-Instanz

        self.game.undo()

        # Überprüfen, ob die Undo-Methode des Logik-Handlers aufgerufen wurde
        self.game.game._handle_throw_undo.assert_called_once_with(player, "Triple", 20, self.game.players)
        # Überprüfen, ob die clear-Methode des Dartboards aufgerufen wurde
        self.game.ui.db.clear_last_dart_image_from_canvas.assert_called_once()

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

    def test_undo_winning_throw_resets_game_state(self):
        """Testet, ob das Rückgängigmachen eines Gewinnwurfs den Spielzustand (end, winner) zurücksetzt."""
        # Setup: Alice hat 40 Punkte
        alice = self.game.players[0]
        alice.score = 40
        
        # Aktion: Alice wirft den Gewinn-Dart (D20).
        # Dies ruft die echte X01._handle_throw-Logik auf.
        self.game.throw("Double", 20)
        
        # Überprüfung des Endzustands
        self.assertTrue(self.game.end, "Das Spiel sollte nach dem Gewinnwurf beendet sein.")
        self.assertEqual(self.game.winner, alice, "Alice sollte die Gewinnerin sein.")
        
        # Aktion: Undo
        self.game.undo()
        
        # Überprüfung des wiederhergestellten Zustands
        self.assertFalse(self.game.end, "Die 'end'-Flagge sollte nach dem Undo zurückgesetzt sein.")
        self.assertIsNone(self.game.winner, "Der 'winner' sollte nach dem Undo zurückgesetzt sein.")
        self.assertEqual(alice.score, 40, "Der Punktestand von Alice sollte wiederhergestellt sein.")

if __name__ == '__main__':
    unittest.main()