import pytest
from unittest.mock import MagicMock
from core.split_score import SplitScore
from core.player import Player

@pytest.fixture
def split_logic(mock_game):
    """Fixture für die Split Score Logik mit Standard-Startscore 40."""
    mock_game.options.opt_split_score_target = 40
    logic = SplitScore(mock_game)
    mock_game.game = logic
    return logic

@pytest.fixture
def player(mock_game, split_logic):
    """Erstellt einen initialisierten Spieler."""
    p = Player("Alice", mock_game)
    split_logic.initialize_player_state(p)
    p.sb = MagicMock()
    return p

def test_initialization(player):
    """Prüft, ob der Start-Score korrekt gesetzt wird."""
    assert player.score == 40
    assert player.state.get('halved_in_round') is None

def test_hit_adds_points(split_logic, player, mock_game):
    """Prüft, ob Treffer auf das Rundenziel Punkte addieren."""
    mock_game.round = 1 # Ziel: S15
    split_logic._handle_throw(player, "Single", 15, [])
    assert player.score == 55 # 40 + 15
    
    # Double Treffer prüfen
    mock_game.round = 3 # Ziel: D17
    split_logic._handle_throw(player, "Double", 17, [])
    assert player.score == 55 + 34 # 89

def test_halving_on_miss(split_logic, player, mock_game):
    """Prüft, ob der Score halbiert wird, wenn kein Pfeil das Ziel trifft."""
    player.score = 40
    mock_game.round = 1 # S15
    player.throws = [("Single", 1, None), ("Single", 2, None), ("Single", 3, None)]
    
    split_logic.handle_end_of_turn(player)
    
    assert player.score == 20
    assert player.state['halved_in_round'] == 1
    assert player.state['score_before_halving'] == 40

def test_halving_rounding_odd_numbers(split_logic, player, mock_game):
    """Prüft, ob bei ungeraden Zahlen korrekt aufgerundet wird (z.B. 41 -> 21)."""
    player.score = 41
    mock_game.round = 1
    player.throws = [("Single", 1, None)]
    
    split_logic.handle_end_of_turn(player)
    
    # (41 + 1) // 2 = 21
    assert player.score == 21

def test_undo_restores_addition(split_logic, player, mock_game):
    """Prüft, ob Undo addierte Punkte korrekt wieder abzieht."""
    player.score = 40
    mock_game.round = 1
    
    split_logic._handle_throw(player, "Single", 15, [])
    assert player.score == 55
    
    split_logic._handle_throw_undo(player, "Single", 15, [])
    assert player.score == 40

def test_undo_restores_halving(split_logic, player, mock_game):
    """Prüft das kritische Szenario: Undo stellt den Score vor einer Halbierung wieder her."""
    player.score = 40
    mock_game.round = 1
    player.throws = [("Single", 1, None)]
    
    # Runde wird beendet -> Score wird halbiert
    split_logic.handle_end_of_turn(player)
    assert player.score == 20
    
    # User klickt Undo (GameController würde den Wurf poppen und undo aufrufen)
    split_logic._handle_throw_undo(player, "Single", 1, [])
    
    assert player.score == 40
    assert player.state['halved_in_round'] is None

def test_win_condition_last_round(split_logic, mock_game, player):
    """Prüft, ob am Ende von Runde 7 der Gewinner korrekt ermittelt wird."""
    p1 = player # Jetzt korrekt über Fixture-Argument
    p2 = Player("Bob", mock_game)
    split_logic.initialize_player_state(p2)
    p2.sb = MagicMock()
    mock_game.players = [p1, p2]
    
    mock_game.round = 7
    mock_game.current = 1 # Bob ist der letzte Spieler der Runde
    p1.score = 100
    p2.score = 80
    
    p2.throws = [("Single", 1, None)] # Bob verfehlt
    split_logic.handle_end_of_turn(p2)
    
    assert mock_game.end is True
    assert mock_game.winner == p1

def test_halving_one_point_stays_one(split_logic, player, mock_game):
    """Prüft, ob 1 Punkt bei Halbierung 1 Punkt bleibt (wegen Aufrundung)."""
    player.score = 1
    mock_game.round = 1
    # Spieler wirft, trifft aber das Ziel nicht
    player.throws = [("Single", 1, None)] 
    
    split_logic.handle_end_of_turn(player)
    
    assert player.score == 1 # (1 + 1) // 2 = 1