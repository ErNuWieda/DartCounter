import unittest
from unittest.mock import patch, MagicMock, mock_open, ANY
import json

# Klasse, die getestet wird
from core.save_load_manager import SaveLoadManager
# Klassen, die als Abhängigkeiten gemockt werden
from core.game import Game
from core.player import Player

class TestSaveLoadManager(unittest.TestCase):
    """Testet die Logik zum Speichern und Laden von Spielständen."""

    def setUp(self):
        """Setzt eine kontrollierte Testumgebung für jeden Test auf."""
        # Mock für ein Game-Objekt mit Spielern und Daten
        self.mock_game = MagicMock(spec=Game)
        self.mock_game.name = "501"
        self.mock_game.opt_in = "Double"
        self.mock_game.opt_out = "Double"
        self.mock_game.opt_atc = "Single"
        self.mock_game.count_to = 501
        self.mock_game.lifes = 3
        self.mock_game.rounds = 7
        self.mock_game.current = 1
        self.mock_game.round = 5

        mock_player1 = MagicMock(spec=Player)
        mock_player1.name = "P1"
        mock_player1.id = 1
        mock_player1.score = 140
        mock_player1.throws = [("Triple", 20)]
        mock_player1.stats = {'total_darts_thrown': 10}
        mock_player1.state = {'has_opened': True}
        # Mock für das Scoreboard des Spielers
        mock_player1.sb = MagicMock()

        mock_player2 = MagicMock(spec=Player)
        mock_player2.name = "P2"
        mock_player2.id = 2
        mock_player2.score = 200
        mock_player2.throws = []
        mock_player2.stats = {'total_darts_thrown': 9}
        mock_player2.state = {'has_opened': True}
        mock_player2.sb = MagicMock()

        self.mock_game.players = [mock_player1, mock_player2]

        # Mock für das Parent-Fenster (für Dialoge)
        self.mock_parent = MagicMock()

        # Patch für messagebox, um UI-Popups zu verhindern
        patcher_ui = patch('core.save_load_manager.ui_utils')
        self.mock_ui_utils = patcher_ui.start()
        self.addCleanup(patcher_ui.stop)

    @patch('core.save_load_manager.filedialog.asksaveasfilename', return_value="/dummy/path/save.json")
    @patch('builtins.open', new_callable=mock_open)
    @patch('json.dump')
    def test_save_game_state_success(self, mock_json_dump, mock_file_open, mock_asksaveasfilename):
        """Testet den erfolgreichen Speichervorgang."""
        result = SaveLoadManager.save_game_state(self.mock_game, self.mock_parent)

        self.assertTrue(result)
        mock_asksaveasfilename.assert_called_once()
        mock_file_open.assert_called_once_with("/dummy/path/save.json", 'w', encoding='utf-8')
        
        # Überprüfen, ob json.dump mit den korrekten, gesammelten Daten aufgerufen wurde
        self.assertTrue(mock_json_dump.called)
        args, _ = mock_json_dump.call_args
        saved_data = args[0]
        self.assertEqual(saved_data['game_name'], "501")
        self.assertEqual(saved_data['current_player_index'], 1)
        self.assertEqual(len(saved_data['players']), 2)
        self.assertEqual(saved_data['players'][0]['name'], "P1")
        self.assertEqual(saved_data['players'][0]['score'], 140)
        self.assertEqual(saved_data['players'][0]['state'], {'has_opened': True})
        self.assertEqual(saved_data['save_format_version'], SaveLoadManager.SAVE_FORMAT_VERSION)

        self.mock_ui_utils.show_message.assert_called_once_with('info', ANY, ANY, parent=self.mock_parent)

    @patch('core.save_load_manager.filedialog.asksaveasfilename', return_value="")
    def test_save_game_state_cancelled(self, mock_asksaveasfilename):
        """Testet, was passiert, wenn der Benutzer den Speicherdialog abbricht."""
        result = SaveLoadManager.save_game_state(self.mock_game, self.mock_parent)
        self.assertFalse(result)
        mock_asksaveasfilename.assert_called_once()
        self.mock_ui_utils.show_message.assert_not_called()

    @patch('core.save_load_manager.filedialog.askopenfilename', return_value="/dummy/path/load.json")
    @patch('builtins.open')
    @patch('json.load')
    def test_load_game_data_success(self, mock_json_load, mock_file_open, mock_askopenfilename):
        """Testet den erfolgreichen Ladevorgang."""
        # Simuliere die Daten, die aus der Datei geladen werden
        mock_data = {
            'save_format_version': SaveLoadManager.SAVE_FORMAT_VERSION,
            'save_type': SaveLoadManager.GAME_SAVE_TYPE, # Hinzugefügt für die neue Validierung
            'game_name': '301', # Beispiel-Daten
            'players': [{'name': 'P1'}]
        }
        mock_json_load.return_value = mock_data

        result = SaveLoadManager.load_game_data(self.mock_parent)

        self.assertEqual(result, mock_data)
        mock_askopenfilename.assert_called_once()
        mock_file_open.assert_called_once_with("/dummy/path/load.json", 'r', encoding='utf-8')
        mock_json_load.assert_called_once()
        self.mock_ui_utils.show_message.assert_not_called()

    @patch('core.save_load_manager.filedialog.askopenfilename', return_value="/dummy/path/load.json")
    @patch('builtins.open')
    @patch('json.load')
    def test_load_game_data_version_mismatch(self, mock_json_load, mock_file_open, mock_askopenfilename):
        """Testet, ob eine inkompatible Speicherversion korrekt abgelehnt wird."""
        mock_data = {'save_format_version': -1, 'game_name': '301'}
        mock_json_load.return_value = mock_data

        result = SaveLoadManager.load_game_data(self.mock_parent)

        self.assertIsNone(result)
        self.mock_ui_utils.show_message.assert_called_once_with('error', ANY, ANY, parent=self.mock_parent)

    def test_restore_game_state(self):
        """Testet, ob der Spielzustand korrekt aus den geladenen Daten wiederhergestellt wird."""
        # Die `state`-Attribute der Mock-Spieler müssen für diesen Test
        # selbst Mocks sein, damit wir den Aufruf von `.update()` überprüfen können.
        for p in self.mock_game.players:
            p.state = MagicMock()

        loaded_data = {
            'round': 10, 'current_player_index': 1,
            'players': [
                {'name': 'P1_loaded', 'id': 1, 'score': 50, 'throws': [('T', 20)], 'stats': {'s1': 1}, 'state': {'hits': {'20': 1}}},
                {'name': 'P2_loaded', 'id': 2, 'score': 75, 'throws': [], 'stats': {'s2': 2}, 'state': {'hits': {'19': 2}}},
            ]
        }
        SaveLoadManager.restore_game_state(self.mock_game, loaded_data)

        self.assertEqual(self.mock_game.round, 10)
        self.assertEqual(self.mock_game.current, 1)
        player1, player2 = self.mock_game.players
        self.assertEqual(player1.name, 'P1_loaded')
        self.assertEqual(player1.score, 50)
        player1.state.update.assert_called_once_with({'hits': {'20': 1}})
        player1.sb.update_score.assert_called_with(50)
        player1.sb.update_display.assert_called_once()
        player2.sb.update_score.assert_called_with(75)