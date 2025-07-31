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
import random
from tkinter import messagebox

class TournamentManager:
    """
    Verwaltet den Ablauf eines Turniers.

    Verantwortlichkeiten:
    - Erstellen eines Turnierbaums (Bracket) aus einer Spielerliste.
    - Verfolgen des Turnierfortschritts.
    - Bereitstellen der nächsten anstehenden Spielpaarung.
    - Verarbeiten von Spielergebnissen und Aktualisieren des Baums.
    """
    def __init__(self, player_names: list[str], game_mode: str, game_options: dict = None):
        """
        Initialisiert ein neues Turnier.

        Args:
            player_names (list[str]): Eine Liste der Namen der teilnehmenden Spieler.
            game_mode (str): Der Spielmodus, der im Turnier gespielt wird (z.B. "501").
            game_options (dict, optional): Die spezifischen Optionen für die Spiele.
        """
        if len(player_names) < 2:
            raise ValueError("Ein Turnier benötigt mindestens 2 Spieler.")

        self.player_names = player_names
        self.game_mode = game_mode
        self.game_options = game_options or {}
        self.bracket = self._create_bracket(player_names, shuffle=True)
        self.winner = None

    @property
    def is_finished(self) -> bool:
        """Gibt True zurück, wenn das Turnier beendet ist (ein Sieger feststeht)."""
        return self.winner is not None

    @property
    def rounds(self) -> list:
        """Gibt die Liste der Runden aus dem Bracket zurück."""
        return self.bracket.get('rounds', [])

    def get_tournament_winner(self) -> str | None:
        """
        Gibt den Namen des Turniersiegers zurück, falls das Turnier beendet ist.

        Returns:
            str or None: Der Name des Siegers oder None, wenn das Turnier noch läuft.
        """
        return self.winner

    def get_next_match(self) -> dict | None:
        """
        Sucht und gibt das nächste ungespielte Match im Turnierbaum zurück.

        Durchläuft alle Runden und Matches und gibt das erste Match zurück,
        bei dem der 'winner' noch nicht gesetzt ist.

        Returns:
            dict or None: Das nächste Match-Dictionary oder None, wenn alle
                          Matches gespielt wurden.
        """
        # Wir durchsuchen alle Runden nach einem ungespielten Match.
        for round_matches in self.bracket.get('rounds', []):
            for match in round_matches:
                if match.get('winner') is None:
                    return match
        return None

    def record_match_winner(self, match_to_update: dict, winner_name: str):
        """
        Trägt den Gewinner eines Matches in den Turnierbaum ein.

        Args:
            match_to_update (dict): Das Match-Dictionary, das aktualisiert werden soll.
                                    Da Dictionaries in Python 'mutable' sind, wird
                                    die Änderung direkt im Turnierbaum wirksam.
            winner_name (str): Der Name des siegreichen Spielers.

        Raises:
            ValueError: Wenn der `winner_name` nicht einer der beiden Spieler
                        im `match_to_update` ist.
        """
        if winner_name not in (match_to_update.get('player1'), match_to_update.get('player2')):
            raise ValueError(f"Der Spieler '{winner_name}' ist kein Teilnehmer dieses Matches.")
        
        match_to_update['winner'] = winner_name

    def advance_to_next_round(self):
        """
        Erstellt oder aktualisiert die nächste Runde basierend auf den Gewinnern der vorherigen Runde.
        Diese Methode durchläuft den gesamten Turnierbaum und stellt sicher, dass alle Gewinner
        korrekt in die Folgerunden vorrücken. Sie wird nach jedem abgeschlossenen Match aufgerufen.
        """
        # Wenn das Turnier bereits einen Sieger hat, gibt es nichts mehr zu tun.
        if self.is_finished:
            return

        if not self.bracket.get('rounds'):
            return

        # NEU: Prüfen, ob das Turnier gerade beendet wurde, BEVOR die Runden neu berechnet werden.
        # Dies verhindert, dass der Gewinner des Finales überschrieben wird.
        last_round = self.bracket['rounds'][-1]
        if len(last_round) == 1 and last_round[0].get('winner'):
            self.winner = last_round[0]['winner']
            return

        # Wir durchlaufen alle Runden, um Gewinner vorrücken zu lassen.
        # Die Schleife geht bis zur vorletzten Runde, da nur diese eine Folgerunde haben kann.
        for round_idx in range(len(self.bracket['rounds'])):
            current_round = self.bracket['rounds'][round_idx]

            # Verhindere, dass aus einer Finalrunde (die nur ein Match hat)
            # eine neue Runde generiert wird.
            if len(current_round) == 1:
                continue

            # Sammle die Gewinner der aktuellen Runde (einige können None sein)
            winners = [match.get('winner') for match in current_round]

            # Erstelle die Paarungen für die nächste Runde
            next_round_matches = []
            for i in range(0, len(winners), 2):
                p1 = winners[i]
                p2 = winners[i+1] if (i + 1) < len(winners) else 'BYE'
                winner = p1 if p2 == 'BYE' and p1 is not None else None
                next_round_matches.append({'player1': p1, 'player2': p2, 'winner': winner})

            if not next_round_matches:
                continue

            next_round_index = round_idx + 1
            if len(self.bracket['rounds']) == next_round_index:
                self.bracket['rounds'].append(next_round_matches)
            else:
                # Die nächste Runde existiert bereits. Wir aktualisieren sie sorgfältig,
                # um bereits gespielte Ergebnisse nicht zu überschreiben.
                existing_next_round = self.bracket['rounds'][next_round_index]
                for i, generated_match in enumerate(next_round_matches):
                    if i < len(existing_next_round):
                        existing_match = existing_next_round[i]
                        # Aktualisiere die Spieler, behalte aber einen eventuell vorhandenen Gewinner bei.
                        existing_match['player1'] = generated_match['player1']
                        existing_match['player2'] = generated_match['player2']

    def to_dict(self) -> dict:
        """Serialisiert den Zustand des Managers in ein Dictionary für das Speichern."""
        return {
            'player_names': self.player_names,
            'game_mode': self.game_mode,
            'game_options': self.game_options,
            'bracket': self.bracket,
            'winner': self.winner
        }

    @classmethod
    def from_dict(cls, data: dict):
        """
        Erstellt eine TournamentManager-Instanz aus einem Dictionary (für das Laden).
        """
        # Erstelle die Instanz mit den Basis-Argumenten
        instance = cls(
            player_names=data['player_names'],
            game_mode=data['game_mode'],            game_options=data.get('game_options', {}) # Fallback für ältere Speicherstände
        )
        # Überschreibe den Zustand mit den geladenen Daten
        instance.bracket = data['bracket']
        instance.winner = data.get('winner')
        return instance

    def _create_bracket(self, players: list[str], shuffle: bool = True) -> dict:
        """
        Erstellt die initiale Turnierstruktur.
        Für den Anfang implementieren wir ein einfaches K.o.-System.
        
        Diese Methode wird per TDD (Test-Driven Development) entwickelt.
        """
        # Mische die Spielerliste für die erste Runde, um zufällige Paarungen zu erstellen.
        # Es wird eine Kopie erstellt, um die ursprüngliche Reihenfolge in self.player_names nicht zu verändern.
        players_to_pair = list(players)
        if shuffle:
            random.shuffle(players_to_pair)

        round1_matches = []
        
        # Anzahl der Spieler, die in regulären Matches gepaart werden
        num_to_pair = len(players_to_pair)
        if len(players_to_pair) % 2 != 0:
            num_to_pair -= 1 # Den letzten Spieler für das Freilos übrig lassen

        # Wir iterieren über die Spielerliste in 2er-Schritten.
        for i in range(0, num_to_pair, 2):
            match = {
                'player1': players_to_pair[i],
                'player2': players_to_pair[i+1],
                'winner': None
            }
            round1_matches.append(match)

        # Wenn die Spieleranzahl ungerade ist, erhält der letzte Spieler ein Freilos.
        if len(players_to_pair) % 2 != 0:
            last_player = players_to_pair[-1]
            bye_match = {'player1': last_player, 'player2': 'BYE', 'winner': last_player}
            round1_matches.append(bye_match)

        return {'rounds': [round1_matches]}