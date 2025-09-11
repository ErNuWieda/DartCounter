import pytest
from unittest.mock import MagicMock, Mock
from core.cricket import Cricket
from core.game_options import GameOptions

# --- Fixtures ---


@pytest.fixture
def mock_players():
    """Erstellt eine Liste von zwei gemockten Spielern."""
    alice = MagicMock()
    alice.name = "Alice"
    alice.score = 0
    alice.state = {"hits": {}}
    alice.stats = {"total_marks_scored": 0}
    alice.sb = MagicMock()

    # Mock für update_score_value, um den Score zu ändern
    def update_alice_score(score, subtract=False):
        if subtract:
            alice.score -= score
        else:
            alice.score += score

    alice.update_score_value = Mock(side_effect=update_alice_score)

    bob = MagicMock()
    bob.name = "Bob"
    bob.score = 0
    bob.state = {"hits": {}}
    bob.stats = {"total_marks_scored": 0}
    bob.sb = MagicMock()

    def update_bob_score(score, subtract=False):
        if subtract:
            bob.score -= score
        else:
            bob.score += score

    bob.update_score_value = Mock(side_effect=update_bob_score)

    return [alice, bob]


@pytest.fixture
def cricket_logic():
    """Erstellt eine Cricket-Logik-Instanz für Standard-Cricket."""
    game = MagicMock()
    game.end = False
    game.options = GameOptions(name="Cricket", opt_in="Single", opt_out="Single", count_to=301, opt_atc="Single", lifes=3, rounds=7, legs_to_win=1, sets_to_win=1)  # type: ignore
    return Cricket(game)


@pytest.fixture
def cut_throat_logic():
    """Erstellt eine Cricket-Logik-Instanz für Cut Throat Cricket."""
    game = MagicMock()
    game.end = False
    game.options = GameOptions(name="Cut Throat", opt_in="Single", opt_out="Single", count_to=301, opt_atc="Single", lifes=3, rounds=7, legs_to_win=1, sets_to_win=1)  # type: ignore
    return Cricket(game)


# --- Cricket Logic Tests ---


class TestCricketLogic:

    def test_initialization(self, cricket_logic, mock_players):
        """Testet, ob die Spieler-Zustände korrekt initialisiert werden."""
        player = mock_players[0]
        cricket_logic.initialize_player_state(player)

        assert player.score == 0
        assert "20" in player.state["hits"]
        assert player.state["hits"]["20"] == 0
        assert "15" in player.state["hits"]
        assert "Bull" in player.state["hits"]
        assert "14" not in player.state["hits"]

    def test_handle_throw_simple_mark(self, cricket_logic, mock_players):
        """Testet, ob ein Treffer auf ein offenes Ziel nur die Marks erhöht."""
        alice = mock_players[0]
        cricket_logic.initialize_player_state(alice)

        cricket_logic._handle_throw(alice, "Double", 20, mock_players)

        assert alice.state["hits"]["20"] == 2
        assert alice.score == 0
        assert alice.stats["total_marks_scored"] == 2

    def test_handle_throw_scoring_hit(self, cricket_logic, mock_players):
        """Testet, ob ein Treffer auf ein geschlossenes Ziel Punkte gibt."""
        alice, bob = mock_players
        cricket_logic.initialize_player_state(alice)
        cricket_logic.initialize_player_state(bob)

        # Alice schließt die 20
        alice.state["hits"]["20"] = 3
        # Bob hat die 20 noch offen
        bob.state["hits"]["20"] = 1

        # Alice wirft eine weitere T20
        cricket_logic._handle_throw(alice, "Triple", 20, mock_players)

        assert alice.state["hits"]["20"] == 6  # 3 (initial) + 3 (throw)
        assert alice.score == 60  # 3 * 20
        alice.update_score_value.assert_called_once_with(60, subtract=False)

    def test_handle_throw_no_scoring_if_all_opponents_closed(
        self, cricket_logic, mock_players
    ):
        """Testet, dass keine Punkte vergeben werden, wenn alle Gegner das Ziel geschlossen haben."""
        alice, bob = mock_players
        cricket_logic.initialize_player_state(alice)
        cricket_logic.initialize_player_state(bob)

        # Beide Spieler haben die 20 geschlossen
        alice.state["hits"]["20"] = 3
        bob.state["hits"]["20"] = 4

        # Alice wirft eine weitere S20
        cricket_logic._handle_throw(alice, "Single", 20, mock_players)

        assert alice.state["hits"]["20"] == 4
        assert alice.score == 0  # Keine Punkte
        alice.update_score_value.assert_not_called()

    def test_win_condition_met(self, cricket_logic, mock_players):
        """Testet die Gewinnbedingung (alle Ziele zu und höchste Punktzahl)."""
        alice, bob = mock_players
        cricket_logic.initialize_player_state(alice)
        cricket_logic.initialize_player_state(bob)

        # Alice hat alle Ziele bis auf 15 geschlossen und führt
        for target in cricket_logic.get_targets():
            if target != "15":
                alice.state["hits"][target] = 3
        alice.score = 100
        bob.score = 50

        # Alice schließt die 15
        status, msg = cricket_logic._handle_throw(alice, "Triple", 15, mock_players)

        assert status == "win"
        assert "gewinnt" in msg
        assert cricket_logic.game.end is True
        assert cricket_logic.game.winner == alice

    def test_win_condition_not_met_lower_score(self, cricket_logic, mock_players):
        """Testet, dass das Spiel nicht endet, wenn der Spieler zwar alle Ziele schließt, aber weniger Punkte hat."""
        alice, bob = mock_players
        cricket_logic.initialize_player_state(alice)
        cricket_logic.initialize_player_state(bob)

        # Alice schließt alle Ziele, hat aber weniger Punkte als Bob
        for target in cricket_logic.get_targets():
            alice.state["hits"][target] = 3
        alice.score = 50
        bob.score = 100

        # Alice trifft ein bereits geschlossenes Ziel, was die Gewinnprüfung auslöst
        status, msg = cricket_logic._handle_throw(alice, "Single", 20, mock_players)

        assert (
            status == "ok"
        ), "Spiel sollte nicht enden, wenn der Spieler weniger Punkte hat."
        assert (
            cricket_logic.game.end is False
        ), "Die 'end'-Flagge sollte nicht gesetzt werden."

    def test_undo_simple_mark(self, cricket_logic, mock_players):
        """Testet das Rückgängigmachen eines einfachen Treffers."""
        alice = mock_players[0]
        cricket_logic.initialize_player_state(alice)

        cricket_logic._handle_throw(alice, "Double", 20, mock_players)
        assert alice.state["hits"]["20"] == 2
        assert alice.stats["total_marks_scored"] == 2

        cricket_logic._handle_throw_undo(alice, "Double", 20, mock_players)

        assert alice.state["hits"]["20"] == 0
        assert alice.stats["total_marks_scored"] == 0

    def test_undo_scoring_mark(self, cricket_logic, mock_players):
        """Testet das Rückgängigmachen eines punktenden Treffers."""
        alice, bob = mock_players
        cricket_logic.initialize_player_state(alice)
        cricket_logic.initialize_player_state(bob)

        alice.state["hits"]["20"] = 3
        cricket_logic._handle_throw(alice, "Single", 20, mock_players)
        assert alice.score == 20
        assert alice.state["hits"]["20"] == 4

        cricket_logic._handle_throw_undo(alice, "Single", 20, mock_players)

        assert alice.score == 0
        assert alice.state["hits"]["20"] == 3
        alice.update_score_value.assert_called_with(20, subtract=True)


# --- Cut Throat Logic Tests ---


class TestCutThroatLogic:

    def test_cut_throat_scoring(self, cut_throat_logic, mock_players):
        """Testet die spezielle Punktevergabe bei Cut Throat."""
        alice, bob = mock_players
        cut_throat_logic.initialize_player_state(alice)
        cut_throat_logic.initialize_player_state(bob)

        # Alice schließt die 20, Bob hat sie noch offen.
        alice.state["hits"]["20"] = 3
        bob.state["hits"]["20"] = 1

        # Alice wirft eine weitere S20
        cut_throat_logic._handle_throw(alice, "Single", 20, mock_players)

        # Alice's Score bleibt 0, Bob bekommt 20 Strafpunkte
        assert alice.score == 0
        assert bob.score == 20

    def test_cut_throat_win_condition(self, cut_throat_logic, mock_players):
        """Testet die Gewinnbedingung bei Cut Throat (alle Ziele zu, niedrigster Score)."""
        alice, bob = mock_players
        cut_throat_logic.initialize_player_state(alice)
        cut_throat_logic.initialize_player_state(bob)

        # Alice schließt alle Ziele und hat weniger Punkte als Bob
        for target in cut_throat_logic.get_targets():
            alice.state["hits"][target] = 3
        alice.score = 50
        bob.score = 100

        # Alice trifft ein bereits geschlossenes Ziel, was die Gewinnprüfung auslöst
        status, msg = cut_throat_logic._handle_throw(alice, "Single", 20, mock_players)

        assert status == "win"
        assert "gewinnt" in msg
        assert cut_throat_logic.game.winner == alice

    def test_undo_cut_throat_scoring(self, cut_throat_logic, mock_players):
        """Testet das Rückgängigmachen eines punktenden Wurfs bei Cut Throat."""
        alice, bob = mock_players
        cut_throat_logic.initialize_player_state(alice)
        cut_throat_logic.initialize_player_state(bob)

        alice.state["hits"]["20"] = 3
        cut_throat_logic._handle_throw(alice, "Single", 20, mock_players)
        assert bob.score == 20

        cut_throat_logic._handle_throw_undo(alice, "Single", 20, mock_players)

        assert bob.score == 0
        bob.update_score_value.assert_called_with(20, subtract=True)
