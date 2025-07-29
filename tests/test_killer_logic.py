import sys
import os
from unittest.mock import MagicMock
import pytest

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.killer import Killer

# --- Mock-Klassen zur Simulation von Abhängigkeiten ---

class MockPlayer:
    """Eine Mock-Klasse für Player, die für Killer-Tests benötigt wird."""
    def __init__(self, name, lifes=3, player_id=None):
        self.name = name
        self.id = player_id
        self.score = lifes # In Killer wird der Score als Lebenszähler verwendet
        self.state = {
            'life_segment': None,
            'can_kill': False,
        }
        self.throws = []
        self.sb = MagicMock() # Mock für das Scoreboard

    def reset_turn(self):
        self.throws = []

class MockGame:
    """Eine Mock-Klasse für Game, um den Spielzustand zu verwalten."""
    def __init__(self):
        self.lifes = 3 # Wird von initialize_player_state benötigt
        self.end = False
        self.round = 1
        # Mocken der next_player Methode, um Aufrufe zu verfolgen
        self.db = MagicMock() # Für messagebox parent
        self.next_player = MagicMock()

@pytest.fixture
def killer_game(monkeypatch):
    """Eine Pytest-Fixture, die die Testumgebung für die Killer-Logik einrichtet."""
    # 1. Mocks einrichten (ersetzt setUp und tearDown)
    mock_messagebox = MagicMock()
    monkeypatch.setattr('core.killer.messagebox', mock_messagebox)

    # 2. Spielobjekte erstellen
    mock_game = MockGame()
    killer_logic = Killer(mock_game)
    
    player1 = MockPlayer("Alice", player_id=1)
    player2 = MockPlayer("Bob", player_id=2)
    players = [player1, player2]
    
    killer_logic.set_players(players)

    # 3. Die eingerichteten Objekte an den Test übergeben
    yield mock_game, killer_logic, player1, player2, players, mock_messagebox


def test_set_life_segment_successfully(killer_game):
    """Testet, ob ein Spieler sein Lebensfeld erfolgreich festlegen kann."""
    mock_game, killer_logic, player1, _, players, _ = killer_game
    assert player1.state['life_segment'] is None
    
    # Alice wirft auf die 17, um ihr Lebensfeld zu bestimmen
    killer_logic._handle_throw(player1, "Single", 17, players)
    
    assert player1.state['life_segment'] == "17"
    # Der Zug sollte nach erfolgreicher Festlegung enden
    assert mock_game.next_player.call_count == 1

def test_undo_set_life_segment(killer_game):
    """Testet, ob das Rückgängigmachen des Setzens eines Lebensfeldes funktioniert."""
    mock_game, killer_logic, player1, _, players, mock_messagebox = killer_game
    # Alice setzt ihr Lebensfeld
    killer_logic._handle_throw(player1, "Single", 17, players)
    assert player1.state['life_segment'] == "17"

    # Mache den Wurf rückgängig
    killer_logic._handle_throw_undo(player1, "Single", 17, players)

    assert player1.state['life_segment'] is None
    mock_messagebox.showinfo.assert_called_with("Rückgängig", "Lebensfeld für Alice zurückgesetzt.", parent=mock_game.db.root)

def test_set_life_segment_fails_if_taken(killer_game):
    """Testet, dass ein Lebensfeld nicht gewählt werden kann, wenn es bereits vergeben ist."""
    mock_game, killer_logic, player1, player2, players, _ = killer_game
    
    # Alice versucht, ebenfalls die 17 zu nehmen
    killer_logic._handle_throw(player1, "Single", 17, players)
    
    assert player1.life_segment == "" # Sollte leer bleiben
    assert not mock_game.next_player.called # Zug endet nicht

def test_become_killer(killer_game):
    """Testet, ob ein Spieler zum Killer wird, wenn er sein Lebensfeld (Double) trifft."""
    _, killer_logic, player1, _, players, _ = killer_game
    player1.life_segment = "16"
    assert not player1.can_kill
    
    # Alice trifft Double 16
    killer_logic._handle_throw(player1, "Double", 16, players)
    
    assert player1.can_kill

def test_undo_become_killer(killer_game):
    """Testet, ob das Rückgängigmachen des Killer-Status korrekt funktioniert und eine Nachricht anzeigt."""
    mock_game, killer_logic, player1, _, players, mock_messagebox = killer_game
    # Spieler 1 wird zum Killer
    player1.life_segment = "16"
    killer_logic._handle_throw(player1, "Double", 16, players)
    assert player1.can_kill

    # Setze den Mock zurück, um nur den Aufruf von der Undo-Aktion zu prüfen
    mock_messagebox.reset_mock()

    # Mache den Wurf rückgängig
    killer_logic._handle_throw_undo(player1, "Double", 16, players)

    assert not player1.can_kill
    mock_messagebox.showinfo.assert_called_once_with("Rückgängig", "Alice ist kein Killer mehr.", parent=mock_game.db.root)

def test_killer_takes_life_from_opponent(killer_game):
    """Testet, ob ein Killer einem Gegner ein Leben nehmen kann."""
    _, killer_logic, player1, player2, players, _ = killer_game
    player1.life_segment = "20"
    player1.can_kill = True
    player2.life_segment = "19"
    
    initial_lifes_bob = player2.score
    
    # Alice (Killer) trifft Double 19 (Bobs Lebensfeld)
    killer_logic._handle_throw(player1, "Double", 19, players)
    
    assert player2.score == initial_lifes_bob - 1

def test_killer_hits_self_and_loses_life(killer_game):
    """Testet, ob ein Killer ein Leben verliert, wenn er sein eigenes Lebensfeld trifft."""
    _, killer_logic, player1, _, players, _ = killer_game
    player1.life_segment = "20"
    player1.can_kill = True
    initial_lifes_alice = player1.score
    
    # Alice (Killer) trifft ihr eigenes Lebensfeld (Double 20)
    killer_logic._handle_throw(player1, "Double", 20, players)
    
    assert player1.score == initial_lifes_alice - 1

def test_win_condition_last_player_standing(killer_game):
    """Testet die Gewinnbedingung, wenn nur noch ein Spieler übrig ist."""
    mock_game, killer_logic, player1, player2, players, _ = killer_game
    player1.life_segment = "20"
    player1.can_kill = True
    player2.life_segment = "19"
    player2.score = 1 # Bob hat nur noch ein Leben
    
    # Alice eliminiert Bob
    result = killer_logic._handle_throw(player1, "Double", 19, players)
    assert player2.score == 0
    assert mock_game.end
    assert "gewinnt Killer" in result

def test_undo_life_loss(killer_game):
    """Testet, ob die Undo-Funktion einen Lebensverlust korrekt rückgängig macht."""
    mock_game, killer_logic, player1, player2, players, mock_messagebox = killer_game
    player1.life_segment = "20"; player1.can_kill = True
    player2.life_segment = "19"; player2.score = 3

    # Alice nimmt Bob ein Leben
    killer_logic._handle_throw(player1, "Double", 19, players)
    assert player2.score == 2

    # Setze den Mock zurück, um nur den Aufruf von der Undo-Aktion zu prüfen
    mock_messagebox.reset_mock()

    # Der Wurf wird rückgängig gemacht
    killer_logic._handle_throw_undo(player1, "Double", 19, players)
    assert player2.score == 3

    # Prüfen, ob die korrekte Nachricht angezeigt wurde
    mock_messagebox.showinfo.assert_called_once_with("Rückgängig", "Leben für Bob wiederhergestellt.", parent=mock_game.db.root)

def test_fail_to_become_killer(killer_game):
    """Testet, dass ein Spieler nicht zum Killer wird, wenn er das falsche Segment trifft."""
    _, killer_logic, player1, _, players, mock_messagebox = killer_game
    player1.life_segment = "16"
    assert not player1.can_kill

    # Alice muss Double 16 treffen, trifft aber Single 16
    killer_logic._handle_throw(player1, "Single", 16, players)

    assert not player1.can_kill
    # Eine Info-Box sollte angezeigt werden, die den Fehlschlag meldet
    mock_messagebox.showinfo.assert_called_once()

def test_killer_hits_neutral_segment(killer_game):
    """Testet, dass nichts passiert, wenn ein Killer ein neutrales Feld trifft."""
    _, killer_logic, player1, player2, players, _ = killer_game
    player1.life_segment = "20"; player1.can_kill = True
    player2.life_segment = "19"
    
    initial_lifes_alice = player1.score
    initial_lifes_bob = player2.score

    # Alice (Killer) trifft die 18, die niemandem gehört
    killer_logic._handle_throw(player1, "Double", 18, players)

    # Die Leben sollten sich nicht geändert haben
    assert player1.score == initial_lifes_alice
    assert player2.score == initial_lifes_bob

def test_undo_killer_hitting_self(killer_game):
    """Testet das Rückgängigmachen eines Treffers auf das eigene Lebensfeld."""
    mock_game, killer_logic, player1, _, players, mock_messagebox = killer_game
    player1.life_segment = "20"; player1.can_kill = True
    initial_lifes = player1.score

    # Alice trifft sich selbst
    killer_logic._handle_throw(player1, "Double", 20, players)
    assert player1.score == initial_lifes - 1

    mock_messagebox.reset_mock()

    # Mache den Wurf rückgängig
    killer_logic._handle_throw_undo(player1, "Double", 20, players)
    assert player1.score == initial_lifes
    mock_messagebox.showinfo.assert_called_once_with("Rückgängig", "Leben für Alice wiederhergestellt.", parent=mock_game.db.root)

def test_no_winner_if_last_player_eliminates_self(killer_game):
    """Testet, dass niemand gewinnt, wenn der letzte Spieler sich selbst eliminiert."""
    mock_game, killer_logic, player1, player2, players, _ = killer_game
    # Bob ist bereits eliminiert
    player2.score = 0
    
    # Alice ist die letzte Spielerin, ist Killer und hat nur noch 1 Leben
    player1.life_segment = "20"; player1.can_kill = True; player1.score = 1

    # Alice trifft ihr eigenes Lebensfeld und eliminiert sich selbst
    result = killer_logic._handle_throw(player1, "Double", 20, players)

    assert player1.score == 0
    assert mock_game.end
    assert "Niemand gewinnt" in result