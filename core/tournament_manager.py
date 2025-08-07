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
from .save_load_manager import SaveLoadManager

class TournamentManager:
    """
    Verwaltet den Ablauf eines Turniers.

    Verantwortlichkeiten:
    - Erstellen eines Turnierbaums (Bracket) aus einer Spielerliste.
    - Verfolgen des Turnierfortschritts.
    - Bereitstellen der nächsten anstehenden Spielpaarung.
    - Verarbeiten von Spielergebnissen und Aktualisieren des Baums.
    """
    def __init__(self, player_names: list[str], game_mode: str, system: str = "Doppel-K.o."):
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
        self.system = system
        self.bracket = self._create_initial_bracket(player_names)
        self.winner = None

    @property
    def is_finished(self) -> bool:
        """Gibt True zurück, wenn das Turnier beendet ist (ein Sieger feststeht)."""
        return self.winner is not None

    def _get_match_loser(self, match: dict) -> str | None:
        """Hilfsmethode, um den Verlierer eines beendeten Matches zu ermitteln."""
        winner = match.get('winner')
        if not winner:
            return None
        
        p1, p2 = match.get('player1'), match.get('player2')
        if p1 == winner: return p2
        return p1

    def get_podium(self) -> dict | None:
        """
        Gibt die ersten drei Plätze zurück, wenn das Turnier beendet ist.

        Returns:
            dict or None: Ein Dictionary mit den Schlüsseln 'first', 'second', 'third'
                          oder None, wenn das Turnier noch nicht beendet ist.
        """
        if not self.is_finished:
            return None

        podium = {'first': self.winner}

        if self.system == "Doppel-K.o.":
            # Im Doppel-K.o. ist der 2. Platz der Verlierer des Grand Finals.
            # Der 3. Platz ist der Verlierer des Loser-Bracket-Finales.
            grand_final = self.bracket['final_bracket'][0]
            lb_final = self.bracket['losers'][-1][0]
            podium['second'] = self._get_match_loser(grand_final)
            podium['third'] = self._get_match_loser(lb_final)
        else: # Einfaches K.o.-System
            final_match = self.bracket['winners'][-1][0]
            third_place_match = self.bracket['final_bracket'][0]
            podium['second'] = self._get_match_loser(final_match)
            podium['third'] = third_place_match.get('winner')
        return podium

    def get_next_match(self) -> dict | None:
        """
        Sucht und gibt das nächste ungespielte Match im Turnierbaum zurück.
        Implementiert eine spezielle Logik für Doppel-K.o.-Turniere, um den
        Spielfluss zwischen Winner- und Loser-Bracket zu steuern.

        Returns:
            dict or None: Das nächste Match-Dictionary oder None, wenn alle
                          Matches gespielt wurden.
        """
        wb_rounds = self.bracket.get('winners', [])
        lb_rounds = self.bracket.get('losers', [])

        def find_next_in_list(match_list):
            for match in match_list:
                if match.get('winner') is None and match.get('player1') and match.get('player2'):
                    return match
            return None

        if self.system != "Doppel-K.o.":
            # Standard K.O. system logic
            # 1. Winners Bracket komplett durchsuchen (inkl. Finale)
            next_wb_match = find_next_in_list(match for round_matches in wb_rounds for match in round_matches)
            if next_wb_match:
                return next_wb_match

            # 2. Finalspiele (Spiel um Platz 3) prüfen
            return find_next_in_list(self.bracket.get('final_bracket', []))

        # --- Doppel-K.o. Logic ---

        # Die korrekte Priorität ist, immer zuerst das Winners-Bracket zu durchsuchen,
        # da die Ergebnisse von dort in das Losers-Bracket einfließen.
        # Da die Bracket-Updates jetzt nach jedem einzelnen Match erfolgen,
        # blockiert diese Logik den Turnierfluss nicht mehr.
        
        # 1. Winners Bracket durchsuchen
        for round_matches in wb_rounds:
            next_match = find_next_in_list(round_matches)
            if next_match:
                return next_match

        # 2. Losers Bracket durchsuchen
        for round_matches in lb_rounds:
            next_match = find_next_in_list(round_matches)
            if next_match:
                return next_match

        # Grand Final
        return find_next_in_list(self.bracket.get('final_bracket', []))

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
        self._update_bracket_state()

    def _update_winners_bracket(self):
        """
        Aktualisiert das Winners Bracket Match für Match, anstatt auf ganze Runden zu warten.
        """
        wb_rounds = self.bracket['winners']
        
        for round_idx in range(len(wb_rounds) - 1):
            for match_idx, child_match in enumerate(wb_rounds[round_idx + 1]):
                parent1 = wb_rounds[round_idx][match_idx * 2]
                parent2 = wb_rounds[round_idx][match_idx * 2 + 1]

                # Fülle den ersten Spielerplatz, sobald das erste Eltern-Match beendet ist
                if parent1.get('winner') and not child_match.get('player1'):
                    child_match['player1'] = parent1['winner']
                
                # Fülle den zweiten Spielerplatz, sobald das zweite Eltern-Match beendet ist
                if parent2.get('winner') and not child_match.get('player2'):
                    child_match['player2'] = parent2['winner']

    def _update_losers_bracket(self):
        """
        Aktualisiert das Losers Bracket Match für Match, basierend auf den Ergebnissen
        der Eltern-Matches aus dem WB und LB.
        """
        wb_rounds = self.bracket['winners']
        lb_rounds = self.bracket['losers']
        if not lb_rounds: return

        for lb_round_idx, lb_round in enumerate(lb_rounds):
            for lb_match_idx, match_to_fill in enumerate(lb_round):
                # Gerade Runden (0, 2, 4...) sind "interne" Runden im LB.
                if lb_round_idx % 2 == 0:
                    if lb_round_idx == 0: # Erste LB-Runde, gefüttert von WB R1
                        parent1 = wb_rounds[0][lb_match_idx * 2]
                        parent2 = wb_rounds[0][lb_match_idx * 2 + 1]
                        if parent1.get('winner') and not match_to_fill.get('player1'):
                            loser1 = self._get_match_loser(parent1)
                            if loser1: match_to_fill['player1'] = loser1
                        if parent2.get('winner') and not match_to_fill.get('player2'):
                            loser2 = self._get_match_loser(parent2)
                            if loser2: match_to_fill['player2'] = loser2
                    else: # Andere gerade Runden, gefüttert von vorheriger LB-Runde
                        parent1 = lb_rounds[lb_round_idx - 1][lb_match_idx * 2]
                        parent2 = lb_rounds[lb_round_idx - 1][lb_match_idx * 2 + 1]
                        if parent1.get('winner') and not match_to_fill.get('player1'):
                            match_to_fill['player1'] = parent1['winner']
                        if parent2.get('winner') and not match_to_fill.get('player2'):
                            match_to_fill['player2'] = parent2['winner']
                
                # Ungerade Runden (1, 3, 5...) sind "Feed-in"-Runden.
                else:
                    lb_parent = lb_rounds[lb_round_idx - 1][lb_match_idx]
                    wb_feed_round_idx = (lb_round_idx + 1) // 2
                    wb_parent = wb_rounds[wb_feed_round_idx][lb_match_idx]

                    if lb_parent.get('winner') and not match_to_fill.get('player1'):
                        match_to_fill['player1'] = lb_parent['winner']
                    if wb_parent.get('winner') and not match_to_fill.get('player2'):
                        wb_loser = next((p for p in [wb_parent['player1'], wb_parent['player2']] if p != wb_parent['winner'] and p != 'BYE'), None)
                        if wb_loser:
                            match_to_fill['player2'] = wb_loser
    
    def _update_final_matches(self):
        """Erstellt das Spiel um Platz 2, sobald die Voraussetzungen erfüllt sind."""
        wb_rounds = self.bracket['winners']
        lb_rounds = self.bracket['losers']

        wb_final_match = wb_rounds[-1][0]
        lb_final_match = lb_rounds[-1][0] if lb_rounds and lb_rounds[-1] else None

        # Check if both final matches are finished
        if not (wb_final_match.get('winner') and lb_final_match and lb_final_match.get('winner')):
            return

        # Spieler ermitteln: Verlierer des WB-Finales vs. Sieger des LB-Finales
        wb_final_loser = next((p for p in [wb_final_match['player1'], wb_final_match['player2']] if p != wb_final_match['winner']), None)
        
        # Der "Sieger" des Losers-Brackets ist in diesem System der WB-Final-Verlierer.
        # Sein Gegner im Spiel um Platz 2 ist der Spieler, den er im LB-Finale besiegt hat.
        lb_champion = lb_final_match.get('winner')
        lb_runner_up = next((p for p in [lb_final_match['player1'], lb_final_match['player2']] if p != lb_champion), None)

        # Spiel um Platz 2 erstellen, falls noch nicht geschehen
        second_place_match = self.bracket['second_place_match'][0]
        # Stelle sicher, dass der WB-Verlierer auch der LB-Sieger ist, bevor das Match erstellt wird.
        if wb_final_loser and lb_runner_up and wb_final_loser == lb_champion and not second_place_match.get('player1'):
            self.bracket['second_place_match'] = [{'player1': wb_final_loser, 'player2': lb_runner_up, 'winner': None}]

    def _update_brackets(self):
        """Orchestrates the update process for the entire tournament bracket."""
        if self.is_finished: return

        self._update_winners_bracket()

        if self.system == "Doppel-K.o.":
            self._update_losers_bracket()
            self._update_final_matches()

            # --- Turniersieger feststellen ---
            # Der Sieger des WB ist der Turniersieger. Das Turnier ist beendet,
            # wenn auch das Spiel um Platz 2 gespielt ist.
            wb_final_match = self.bracket['winners'][-1][0]
            second_place_match = self.bracket['second_place_match'][0]

            if wb_final_match.get('winner') and second_place_match.get('winner'):
                self.winner = wb_final_match.get('winner')
        else: # Einfaches K.o.-System
            wb_rounds = self.bracket['winners']
            # --- Spiel um Platz 3 erstellen ---
            if len(wb_rounds) >= 2:
                semifinal_round = wb_rounds[-2]
                third_place_match = self.bracket.get('third_place_match', [{}])[0]
                if len(semifinal_round) == 2:
                    sf1, sf2 = semifinal_round[0], semifinal_round[1]
                    
                    if sf1.get('winner') and not third_place_match.get('player1'):
                        loser1 = next((p for p in [sf1['player1'], sf1['player2']] if p != sf1['winner']), None)
                        if loser1: third_place_match['player1'] = loser1

                    if sf2.get('winner') and not third_place_match.get('player2'):
                        loser2 = next((p for p in [sf2['player1'], sf2['player2']] if p != sf2['winner']), None)
                        if loser2: third_place_match['player2'] = loser2

            # --- Turniersieger feststellen ---
            final_match = wb_rounds[-1][0]
            final_match_finished = final_match.get('winner') is not None
            
            third_place_match = self.bracket.get('third_place_match', [{}])[0]
            third_place_finished = not third_place_match.get('player1') or third_place_match.get('winner') is not None

            if final_match_finished and third_place_finished:
                self.winner = final_match['winner']

    def to_dict(self) -> dict:
        """Serialisiert den Zustand des Managers in ein Dictionary für das Speichern."""
        return {
            'player_names': self.player_names,
            'game_mode': self.game_mode,
            'system': self.system,
            'bracket': self.bracket,
            'winner': self.winner,
        }

    def get_save_meta(self) -> dict:
        """
        Gibt die Metadaten für den Speicherdialog zurück.
        Implementiert den zweiten Teil der Speicher-Schnittstelle.
        """
        return {
            'title': "Turnier speichern unter...",
            'filetypes': SaveLoadManager.TOURNAMENT_FILE_TYPES,
            'defaultextension': ".tourn.json",
            'save_type': SaveLoadManager.TOURNAMENT_SAVE_TYPE
        }


    @classmethod
    def from_dict(cls, data: dict):
        """
        Erstellt eine TournamentManager-Instanz aus einem Dictionary (für das Laden).
        """
        instance = cls(
            player_names=data['player_names'],
            game_mode=data['game_mode'],
            system=data.get('system', 'Doppel-K.o.') # Fallback für alte Speicherstände
        )
        instance.bracket = data['bracket']
        instance.winner = data.get('winner')
        return instance

    def _create_initial_bracket(self, players: list[str], shuffle: bool = True) -> dict:
        """
        Erstellt die komplette initiale Turnierstruktur für das Winners Bracket
        mit Platzhaltern für zukünftige Runden.
        """
        players_to_pair = list(players)
        if shuffle:
            random.shuffle(players_to_pair)
        # --- Komplette Bracket-Struktur im Voraus erstellen ---
        num_players = len(players_to_pair)
        # Nächste Zweierpotenz finden, um die Bracket-Größe zu bestimmen
        bracket_size = 2
        while bracket_size < num_players:
            bracket_size *= 2
        
        # --- Intelligente Verteilung von Freilosen (Byes), um "BYE vs BYE" zu verhindern ---
        num_byes = bracket_size - num_players
        
        # Spieler, die ein Freilos erhalten, werden von denen getrennt, die in Runde 1 spielen.
        players_with_byes = players_to_pair[:num_byes]
        players_for_round1_matches = players_to_pair[num_byes:]

        # Runde 1 erstellen
        # Zuerst die Matches der Spieler, die tatsächlich spielen
        round1_matches = self._create_next_round_matches(players_for_round1_matches)
        
        # Dann die "Matches" für die Spieler mit Freilos hinzufügen, die direkt als Sieger gelten
        for player_with_bye in players_with_byes:
            round1_matches.append({'player1': player_with_bye, 'player2': 'BYE', 'winner': player_with_bye})

        all_rounds = [round1_matches]
        
        # Platzhalter für die restlichen Runden erstellen
        current_round_size = len(round1_matches)
        while current_round_size > 1:
            next_round_size = current_round_size // 2
            next_round_matches = [{'player1': None, 'player2': None, 'winner': None} for _ in range(next_round_size)]
            all_rounds.append(next_round_matches)
            current_round_size = next_round_size

        if self.system == "Doppel-K.o.":
            # Erstelle die Platzhalter-Struktur für das Losers Bracket
            losers_rounds = []
            if len(all_rounds) > 1: # Nur wenn es mehr als eine Runde im WB gibt
                # Die Anzahl der Runden im LB ist 2 * (Anzahl WB-Runden - 1)
                num_lb_rounds = 2 * (len(all_rounds) - 1)
                # Die Anzahl der Matches in der ersten LB-Runde ist die Hälfte der Matches der ersten WB-Runde
                num_matches_in_lb_round = len(all_rounds[0]) // 2

                for i in range(num_lb_rounds):
                    if num_matches_in_lb_round > 0:
                        placeholder_round = [{'player1': None, 'player2': None, 'winner': None} for _ in range(num_matches_in_lb_round)]
                        losers_rounds.append(placeholder_round)
                    
                    # Die Anzahl der Matches halbiert sich alle zwei Runden
                    if (i + 1) % 2 == 0 and num_matches_in_lb_round > 1:
                        num_matches_in_lb_round //= 2
            return {
                'winners': all_rounds,
                'losers': losers_rounds,
                'second_place_match': [{}] # Platzhalter für das neue Spiel um Platz 2
            }
        else: # K.o.-System
            return {
                'winners': all_rounds,
                'losers': [], # Bleibt leer
                'grand_final': [], # Veraltet, aber für Kompatibilität beibehalten
                'second_place_match': [],
                'third_place_match': [{}] # Platzhalter für Spiel um Platz 3
            }

    def _create_next_round_matches(self, players: list) -> list[dict]:
        """
        Hilfsmethode, die aus einer Liste von Spielern eine Liste von Matches erstellt.
        Behandelt automatisch Freilose (Byes) bei ungerader Spielerzahl.
        """
        if not players:
            return []

        matches = []
        players_to_pair = list(players)

        # Pair up players
        while len(players_to_pair) >= 2:
            p1 = players_to_pair.pop(0)
            p2 = players_to_pair.pop(0)
            matches.append({'player1': p1, 'player2': p2, 'winner': None})

        # If one player is left, they are waiting for an opponent from another branch.
        # This is NOT a "bye" (automatic win).
        if players_to_pair:
            p1 = players_to_pair.pop(0)
            matches.append({'player1': p1, 'player2': None, 'winner': None})

        return matches