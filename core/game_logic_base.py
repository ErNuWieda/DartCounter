"""
Defines the base class for all game logic handlers.
"""

class GameLogicBase:
    """
    Eine abstrakte Basisklasse für alle Spiellogik-Handler.

    Diese Klasse definiert eine gemeinsame Schnittstelle, die von allen spezifischen
    Spiellogik-Klassen (wie X01, Cricket, etc.) implementiert werden muss.
    Sie stellt sicher, dass die Haupt-`Game`-Klasse konsistent mit jeder
    Art von Spiellogik interagieren kann.
    """
    def __init__(self, game):
        """
        Initialisiert die Basis-Spiellogik.

        Args:
            game (Game): Die Haupt-Spielinstanz.
        """
        self.game = game
        self.targets = None

    def get_targets(self):
        """
        Gibt die Liste der Ziele für das Spiel zurück.
        Unterklassen sollten `self.targets` in ihrem `__init__` setzen.
        """
        return self.targets

    def initialize_player_state(self, player):
        """
        Initialisiert den spielspezifischen Zustand für einen Spieler.
        Wird von der Game-Klasse nach der Erstellung des Spielers aufgerufen.
        """
        pass # Standard-Implementierung tut nichts.

    def get_scoreboard_height(self):
        """
        Gibt die empfohlene Höhe für das Scoreboard dieses Spielmodus zurück.
        Die Standardimplementierung berechnet die Höhe basierend auf der Anzahl der Ziele.
        Kann von Unterklassen für spezielle Fälle (z.B. X01) überschrieben werden.
        """
        if self.targets:
            base_height = 220
            num_rows = (len(self.targets) + 1) // 2
            targets_height = 25 + num_rows * 32
            return base_height + targets_height

        # Fallback-Höhe, falls keine Ziele definiert sind und nichts überschrieben wurde.
        return 380

    def _handle_throw(self, player, ring, segment, players):
        """
        Verarbeitet einen einzelnen Wurf. Muss von Unterklassen implementiert werden.
        """
        raise NotImplementedError("Die Methode '_handle_throw' muss in der Unterklasse implementiert werden.")

    def _handle_throw_undo(self, player, ring, segment, players):
        """
        Macht einen Wurf rückgängig. Muss von Unterklassen implementiert werden.
        """
        raise NotImplementedError("Die Methode '_handle_throw_undo' muss in der Unterklasse implementiert werden.")