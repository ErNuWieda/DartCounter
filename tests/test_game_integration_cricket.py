import pytest
from unittest.mock import MagicMock

from core.game import Game
from core.game_options import GameOptions


@pytest.fixture
def _cricket_game_factory(game_factory):
    """Private factory to create a cricket game and mock its scoreboards."""

    def _factory(game_options, player_names):
        game = game_factory(game_options, player_names)
        for p in game.players:
            p.sb = MagicMock()
        return game

    return _factory


@pytest.fixture
def cricket_game(_cricket_game_factory):
    """Richtet für jeden Test eine neue Cricket-Spielinstanz ein."""
    game_options = {
        "name": "Cricket",
        "opt_in": "Single",
        "opt_out": "Single",
        "count_to": 301,
        "legs_to_win": 1,
        "sets_to_win": 1,
        "opt_atc": "Single",
        "lifes": 3,
        "rounds": 7,
    }
    return _cricket_game_factory(game_options, ["Alice", "Bob"])


@pytest.fixture
def cut_throat_game(_cricket_game_factory):
    """Richtet für jeden Test eine neue Cut Throat-Spielinstanz ein."""
    game_options = {
        "name": "Cut Throat",
        "opt_in": "Single",
        "opt_out": "Single",
        "count_to": 301,
        "legs_to_win": 1,
        "sets_to_win": 1,
        "opt_atc": "Single",
        "lifes": 3,
        "rounds": 7,
    }
    return _cricket_game_factory(game_options, ["Alice", "Bob"])


class TestGameWithCricket:

    def test_initial_state(self, cricket_game):
        """Testet den korrekten Anfangszustand eines Cricket-Spiels."""
        game = cricket_game
        assert game.options.name == "Cricket"
        assert len(game.players) == 2

        for player in game.players:
            assert player.score == 0
            assert isinstance(player.state["hits"], dict)
            assert player.state["hits"].get("20") == 0
            assert "15" in player.state["hits"]
            assert "14" not in player.state["hits"]

    def test_hit_records_marks_and_scores_points(self, cricket_game):
        """Simuliert das Schließen eines Ziels und das anschließende Punkten."""
        game = cricket_game
        alice = game.current_player()

        # 1. Wurf: Alice trifft T20 und schließt damit die 20
        game.throw("Triple", 20)
        assert alice.state["hits"]["20"] == 3
        assert alice.score == 0

        # 2. Wurf: Alice trifft S20 und punktet, da die 20 bei Bob noch offen ist
        game.throw("Single", 20)
        assert alice.state["hits"]["20"] == 4
        assert alice.score == 20

    def test_win_condition(self, cricket_game):
        """Testet die Gewinnbedingung (alle Ziele zu, höchste Punktzahl)."""
        game = cricket_game
        mock_highscore_manager = game.highscore_manager
        alice, bob = game.players

        # Simuliere, dass Alice alle Ziele bis auf die 15 geschlossen hat und führt.
        # Sie hat bereits 2 Treffer auf die 15.
        for target in game.targets:
            if target == "15":
                alice.state["hits"][target] = 2
            else:
                alice.state["hits"][target] = 3
        alice.score = 100
        bob.score = 50

        # Der letzte Wurf schließt die 15 und löst damit den Sieg aus.
        game.throw("Single", 15)

        assert game.end is True, "Das Spiel sollte nach dem Gewinnwurf beendet sein."
        assert game.winner == alice, "Der 'winner' wurde nicht gesetzt."
        # Annahme: Der Gewinnwurf ist der erste Wurf im Spiel (1 Dart, 1 Mark). MPR = (1/1)*3 = 3.0
        # Dies testet auch, ob die Statistik-Updates im Gewinnfall korrekt sind.
        mock_highscore_manager.add_score.assert_called_once_with(
            "Cricket", "Alice", pytest.approx(3.0)
        )

    def test_undo_scoring_hit_restores_state(self, cricket_game):
        """Testet, ob das Rückgängigmachen eines punktenden Wurfs den Zustand wiederherstellt."""
        game = cricket_game
        alice = game.current_player()
        alice.state["hits"]["20"] = 3  # Alice hat die 20 bereits geschlossen

        game.throw("Single", 20)  # Alice punktet
        assert alice.score == 20
        assert alice.state["hits"]["20"] == 4

        game.undo()
        assert alice.score == 0, "Der Punktestand sollte nach dem Undo zurückgesetzt sein."
        assert (
            alice.state["hits"]["20"] == 3
        ), "Die Anzahl der Marks sollte nach dem Undo zurückgesetzt sein."

    def test_cut_throat_scoring_adds_points_to_opponent(self, cut_throat_game):
        """Simuliert das Punkten bei Cut Throat, was dem Gegner Punkte hinzufügt."""
        game = cut_throat_game
        alice = game.current_player()
        bob = game.players[1]

        # Alice schließt die 20
        game.throw("Triple", 20)
        assert alice.state["hits"]["20"] == 3
        assert alice.score == 0
        assert bob.score == 0

        # Alice wirft eine weitere S20. Bob sollte die Punkte bekommen.
        game.throw("Single", 20)
        assert alice.score == 0
        assert bob.score == 20
