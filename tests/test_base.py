import unittest
from unittest.mock import patch, MagicMock

from core.game import Game
from core.player import Player
from core.scoreboard import ScoreBoard

class GameLogicTestBase(unittest.TestCase):
    """
    Eine gemeinsame Basisklasse für alle Tests von Spiellogik-Klassen.
    Sie enthält wiederverwendbare setUp-Logik und Hilfsmethoden.
    """
    # Die Unterklasse sollte 'self.logic' in ihrer setUp-Methode auf die
    # Instanz der zu testenden Spiellogik setzen (z.B. self.logic = self.x01_logic).
    logic = None
    logic_class_module = ""

    def setUp(self):
        """Setzt eine kontrollierte, gemeinsame Testumgebung auf."""
        self.mock_game = MagicMock(spec=Game)
        self.mock_game.round = 1
        self.mock_game.end = False
        # Mock für das Dartboard-Fenster, das als Parent für Messageboxen dient.
        self.mock_game.db = MagicMock()
        self.mock_game.db.root = MagicMock()
        self.mock_game.highscore_manager = MagicMock()
        self.mock_game.sound_manager = MagicMock()
        self.mock_game.get_score.side_effect = self._get_score_side_effect
        self.mock_game.targets = [] # Standard-Fallback

        # Patch für messagebox, wird von allen Logik-Tests benötigt
        # Die Unterklasse muss 'self.logic_class_module' definieren.
        patcher = patch(f'core.{self.logic_class_module}.messagebox')
        self.mock_messagebox = patcher.start()
        self.addCleanup(patcher.stop)

    def _create_player(self, name="Tester", **kwargs):
        """
        Erstellt eine echte Player-Instanz, initialisiert sie mit der Spiellogik
        und setzt Standardwerte oder übergebene Attribute.

        Args:
            name (str): Der Name des Spielers.
            **kwargs: Schlüssel-Wert-Paare, die auf dem Spieler gesetzt werden sollen
                      (z.B. score=100, state={'has_opened': False}).
        """
        player = Player(name=name, game=self.mock_game)

        # Initialisiere den Spieler mit der spezifischen Logik der Testklasse.
        # Die Unterklasse muss self.logic in ihrer setUp-Methode gesetzt haben.
        if self.logic and hasattr(self.logic, 'initialize_player_state'):
            self.logic.initialize_player_state(player)

        # Überschreibe Standardwerte mit den übergebenen kwargs.
        for key, value in kwargs.items():
            if key == 'state' and isinstance(value, dict):
                # State-Werte zusammenführen, anstatt sie komplett zu überschreiben.
                player.state.update(value)
            else:
                setattr(player, key, value)

        # Mock für das Scoreboard, das vom Spieler referenziert wird.
        player.sb = MagicMock(spec=ScoreBoard)
        return player

    def _get_score_side_effect(self, ring, segment):
        """Simuliert die get_score Methode der Game-Klasse für die Tests."""
        if ring == "Bullseye": return 50
        if ring == "Bull": return 25

        try:
            segment_val = int(segment)
        except (ValueError, TypeError):
            return 0 # Ungültiges Segment wie 'Miss'

        if ring == "Triple": return segment * 3
        if ring == "Double": return segment * 2
        if ring == "Single": return segment
        return 0