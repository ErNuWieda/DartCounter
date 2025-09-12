# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Dieses Modul enthält den TournamentManager, der die Logik für den
Turniermodus steuert.
"""
from .save_load_manager import SaveLoadManager
from .tournament_strategies import (
    SingleEliminationStrategy,
    DoubleEliminationStrategy,
)


class TournamentManager:
    """
    Verwaltet den Ablauf eines Turniers.

    Verantwortlichkeiten:
    - Erstellen eines Turnierbaums (Bracket) aus einer Spielerliste.
    - Verfolgen des Turnierfortschritts.
    - Bereitstellen der nächsten anstehenden Spielpaarung.
    - Verarbeiten von Spielergebnissen und Aktualisieren des Baums.
    """

    STRATEGY_MAP = {
        "K.o.": SingleEliminationStrategy,
        "Doppel-K.o.": DoubleEliminationStrategy,
    }

    def __init__(
        self,
        player_names: list[str],
        game_mode: str,
        system: str,
        shuffle: bool = True,
    ):
        """
        Initialisiert ein neues Turnier.

        Args:
            player_names (list[str]): Eine Liste der Namen der teilnehmenden Spieler.
            game_mode (str): Der Spielmodus, der im Turnier gespielt wird (z.B. "501").
            system (str): Das Turniersystem ("K.o." oder "Doppel-K.o.").
            shuffle (bool): Ob die Spielerliste initial gemischt werden soll.
        """
        if len(player_names) < 2:
            raise ValueError("Ein Turnier benötigt mindestens 2 Spieler.")

        strategy_class = self.STRATEGY_MAP.get(system)
        if not strategy_class:
            raise ValueError(f"Unbekanntes Turniersystem: {system}")

        self.player_names = player_names
        self.game_mode = game_mode
        self.system = system
        self.strategy = strategy_class(player_names, shuffle=shuffle)

    @property
    def is_finished(self) -> bool:
        """Gibt True zurück, wenn das Turnier beendet ist (ein Sieger feststeht)."""
        return self.strategy.is_finished

    @property
    def winner(self) -> str | None:
        """Gibt den Namen des Turniersiegers zurück, falls das Turnier beendet ist."""
        return self.strategy.winner

    @property
    def bracket(self) -> dict:
        """Gibt die aktuelle Turnierbaum-Struktur zurück."""
        return self.strategy.bracket

    def get_podium(self) -> dict | None:
        """Delegiert die Podium-Ermittlung an die Strategie."""
        return self.strategy.get_podium()

    def get_next_match(self) -> dict | None:
        """Delegiert die Suche nach dem nächsten Match an die Strategie."""
        return self.strategy.get_next_match()

    def record_match_winner(self, match_to_update: dict, winner_name: str):
        """Delegiert die Verarbeitung des Match-Ergebnisses an die Strategie."""
        self.strategy.record_match_winner(match_to_update, winner_name)

    def to_dict(self) -> dict:
        """Serialisiert den Zustand des Managers in ein Dictionary für das Speichern."""
        return {
            "player_names": self.player_names,
            "game_mode": self.game_mode,
            "system": self.system,
            "bracket": self.bracket,
            "winner": self.strategy.winner,
        }

    def get_save_meta(self) -> dict:
        """
        Gibt die Metadaten für den Speicherdialog zurück.
        Implementiert den zweiten Teil der Speicher-Schnittstelle.
        """
        return {
            "title": "Turnier speichern unter...",
            "filetypes": SaveLoadManager.TOURNAMENT_FILE_TYPES,
            "defaultextension": ".tourn.json",
            "save_type": SaveLoadManager.TOURNAMENT_SAVE_TYPE,
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Erstellt eine TournamentManager-Instanz aus einem Dictionary (für das Laden).
        """
        instance = cls(
            player_names=data["player_names"],
            game_mode=data["game_mode"],
            system=data.get("system", "Doppel-K.o."),  # Fallback für alte Speicherstände
        )
        instance.strategy.bracket = data["bracket"]
        instance.strategy.winner = data.get("winner")
        return instance
