import pytest
from unittest.mock import MagicMock
import sys
import os
import tkinter as tk

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.game import Game
from core.game_options import GameOptions

@pytest.fixture
def tk_root():
    """Erstellt eine einzige, versteckte Tk-Wurzel für alle Integrationstests in dieser Klasse."""
    root = tk.Tk()
    root.withdraw()
    yield root
    if root and root.winfo_exists():
        root.destroy()

@pytest.fixture
def _game_factory(tk_root, monkeypatch):
    """
    Eine "private" Factory-Fixture, die die Erstellung von Spielinstanzen für
    Cricket-Varianten zentralisiert und die Duplizierung von Code reduziert.
    """
    created_games = []

    def _create_game(game_name: str):
        # UI-Utility-Funktionen patchen
        monkeypatch.setattr('core.game.ui_utils.show_message', MagicMock())
        monkeypatch.setattr('core.game.ui_utils.ask_question', MagicMock())

        # Manager-Abhängigkeiten mocken
        mock_sound_manager = MagicMock()
        mock_highscore_manager = MagicMock()
        mock_player_stats_manager = MagicMock()

        player_names = ["Alice", "Bob"]
        game_options = {
            "name": game_name,
            "opt_in": "Single", "opt_out": "Single", "opt_atc": "Single",
            "count_to": 301, "lifes": 3, "rounds": 7
        }
        game_options_obj = GameOptions.from_dict(game_options)
        
        game = Game(
            tk_root, 
            game_options_obj, 
            player_names, 
            mock_sound_manager, 
            mock_highscore_manager, 
            mock_player_stats_manager
        )
        created_games.append(game)
        
        # Scoreboards manuell mocken
        for p in game.players:
            p.sb = MagicMock()

        return game, mock_highscore_manager

    yield _create_game

    # Nach dem Test alle erstellten Spielinstanzen sicher bereinigen
    for game in created_games:
        if game:
            game.destroy()

@pytest.fixture
def game_setup(_game_factory):
    """Richtet für jeden Test eine neue Cricket-Spielinstanz ein."""
    return _game_factory("Cricket")

@pytest.fixture
def cut_throat_game_setup(_game_factory):
    """Richtet für jeden Test eine neue Cut Throat-Spielinstanz ein."""
    return _game_factory("Cut Throat")


class TestGameWithCricket:

    def test_initial_state(self, game_setup):
        """Testet den korrekten Anfangszustand eines Cricket-Spiels."""
        game, _ = game_setup
        assert game.options.name == "Cricket"
        assert len(game.players) == 2
        
        for player in game.players:
            assert player.score == 0
            assert isinstance(player.state['hits'], dict)
            assert player.state['hits'].get('20') == 0
            assert '15' in player.state['hits']
            assert '14' not in player.state['hits']

    def test_hit_records_marks_and_scores_points(self, game_setup):
        """Simuliert das Schließen eines Ziels und das anschließende Punkten."""
        game, _ = game_setup
        alice = game.current_player()
        
        # 1. Wurf: Alice trifft T20 und schließt damit die 20
        game.throw("Triple", 20)
        assert alice.state['hits']['20'] == 3
        assert alice.score == 0

        # 2. Wurf: Alice trifft S20 und punktet, da die 20 bei Bob noch offen ist
        game.throw("Single", 20)
        assert alice.state['hits']['20'] == 4
        assert alice.score == 20

    def test_win_condition(self, game_setup):
        """Testet die Gewinnbedingung (alle Ziele zu, höchste Punktzahl)."""
        game, mock_highscore_manager = game_setup
        alice, bob = game.players

        # Simuliere, dass Alice alle Ziele bis auf die 15 geschlossen hat und führt.
        # Sie hat bereits 2 Treffer auf die 15.
        for target in game.targets:
            if target == '15':
                alice.state['hits'][target] = 2
            else:
                alice.state['hits'][target] = 3
        alice.score = 100
        bob.score = 50

        # Der letzte Wurf schließt die 15 und löst damit den Sieg aus.
        game.throw("Single", 15)

        assert game.end is True, "Das Spiel sollte nach dem Gewinnwurf beendet sein."
        assert game.winner == alice, "Der 'winner' wurde nicht gesetzt. Die Cricket-Logik gibt wahrscheinlich nicht den korrekten Gewinn-String zurück."
        # Prüfen, ob der Highscore-Manager mit der korrekten Metrik (MPR) aufgerufen wurde
        # Annahme: Der Gewinnwurf ist der erste Wurf im Spiel (1 Dart, 1 Mark). MPR = (1/1)*3 = 3.0
        # Dies testet auch, ob die Statistik-Updates im Gewinnfall korrekt sind.
        mock_highscore_manager.add_score.assert_called_once_with("Cricket", "Alice", pytest.approx(3.0))

    def test_undo_scoring_hit_restores_state(self, game_setup):
        """Testet, ob das Rückgängigmachen eines punktenden Wurfs den Zustand wiederherstellt."""
        game, _ = game_setup
        alice = game.current_player()
        alice.state['hits']['20'] = 3 # Alice hat die 20 bereits geschlossen

        game.throw("Single", 20) # Alice punktet
        assert alice.score == 20
        assert alice.state['hits']['20'] == 4

        game.undo()
        assert alice.score == 0, "Der Punktestand sollte nach dem Undo zurückgesetzt sein."
        assert alice.state['hits']['20'] == 3, "Die Anzahl der Marks sollte nach dem Undo zurückgesetzt sein."
