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
Dieses Modul enthält die Strategie-Klassen für die verschiedenen Turniersysteme.
"""
import random


class TournamentStrategyBase:
    """Abstrakte Basisklasse für alle Turniersystem-Strategien."""

    def __init__(self, player_names: list[str], shuffle: bool = True):
        self.player_names = player_names
        # shuffle wird an die konkrete Implementierung weitergegeben
        self.bracket = self._create_initial_bracket(player_names, shuffle=shuffle)
        self.winner = None

    @property
    def is_finished(self) -> bool:
        """Gibt True zurück, wenn das Turnier einen Sieger hat."""
        return self.winner is not None

    def record_match_winner(self, match_to_update: dict, winner_name: str):
        """Trägt den Gewinner eines Matches ein und aktualisiert den Turnierbaum."""
        if winner_name not in (
            match_to_update.get("player1"),
            match_to_update.get("player2"),
        ):
            raise ValueError(
                f"Spieler '{winner_name}' ist kein Teilnehmer dieses Matches."
            )

        match_to_update["winner"] = winner_name
        self._update_bracket_state()

    def _get_match_loser(self, match: dict) -> str | None:
        """Hilfsmethode, um den Verlierer eines beendeten Matches zu ermitteln."""
        winner = match.get("winner")
        if not winner:
            return None
        p1, p2 = match.get("player1"), match.get("player2")
        return p2 if p1 == winner else p1

    def _find_next_in_list(self, match_list: list[dict]) -> dict | None:
        """Sucht das nächste spielbare Match in einer flachen Liste von Matches."""
        for match in match_list:
            if (
                match.get("winner") is None
                and match.get("player1")
                and match.get("player2")
            ):
                return match
        return None

    def _create_matches_from_players(self, players: list) -> list[dict]:
        """Hilfsmethode, die aus einer Liste von Spielern eine Liste von Matches erstellt."""
        matches = []
        players_to_pair = list(players)
        while len(players_to_pair) >= 2:
            p1 = players_to_pair.pop(0)
            p2 = players_to_pair.pop(0)
            matches.append({"player1": p1, "player2": p2, "winner": None})
        return matches

    def _prepare_initial_players(
        self, players: list[str], shuffle: bool = True
    ) -> tuple[list, list]:
        """Bereitet die Spielerliste vor, mischt sie und ermittelt Freilose (Byes)."""
        players_to_pair = list(players)
        if shuffle:
            random.shuffle(players_to_pair)

        num_players = len(players_to_pair)
        bracket_size = 2
        while bracket_size < num_players:
            bracket_size *= 2

        num_byes = bracket_size - num_players
        players_with_byes = players_to_pair[:num_byes]
        players_for_round1_matches = players_to_pair[num_byes:]
        return players_for_round1_matches, players_with_byes

    def _create_initial_bracket(self, players: list[str], shuffle: bool = True) -> dict:
        raise NotImplementedError

    def get_next_match(self) -> dict | None:
        raise NotImplementedError

    def get_podium(self) -> dict | None:
        raise NotImplementedError

    def _update_bracket_state(self):
        raise NotImplementedError


class SingleEliminationStrategy(TournamentStrategyBase):
    """Strategie für ein einfaches K.o.-System."""

    def _create_initial_bracket(self, players: list[str], shuffle: bool = True) -> dict:
        players_for_r1, players_with_byes = self._prepare_initial_players(
            players, shuffle
        )

        round1_matches = self._create_matches_from_players(players_for_r1)
        for player_with_bye in players_with_byes:
            round1_matches.append(
                {
                    "player1": player_with_bye,
                    "player2": "BYE",
                    "winner": player_with_bye,
                }
            )

        all_rounds = [round1_matches]
        current_round_size = len(round1_matches)
        while current_round_size > 1:
            next_round_size = current_round_size // 2
            next_round_matches = [
                {"player1": None, "player2": None, "winner": None}
                for _ in range(next_round_size)
            ]
            all_rounds.append(next_round_matches)
            current_round_size = next_round_size

        return {
            "winners": all_rounds,
            "losers": [],
            "final_bracket": [
                {"player1": None, "player2": None, "winner": None}
            ],  # Spiel um Platz 3
        }

    def _update_bracket_state(self):
        if self.is_finished:
            return

        wb_rounds = self.bracket["winners"]
        for round_idx in range(len(wb_rounds) - 1):
            for match_idx, child_match in enumerate(wb_rounds[round_idx + 1]):
                parent1 = wb_rounds[round_idx][match_idx * 2]
                parent2 = wb_rounds[round_idx][match_idx * 2 + 1]
                if parent1.get("winner") and not child_match.get("player1"):
                    child_match["player1"] = parent1["winner"]
                if parent2.get("winner") and not child_match.get("player2"):
                    child_match["player2"] = parent2["winner"]

        # Spiel um Platz 3 erstellen
        if len(wb_rounds) >= 2:
            semifinal_round = wb_rounds[-2] if len(wb_rounds) > 1 else []
            third_place_match = self.bracket["final_bracket"][0]
            if len(semifinal_round) == 2:
                sf1, sf2 = semifinal_round[0], semifinal_round[1]

                if sf1.get("winner") and third_place_match.get("player1") is None:
                    loser1 = self._get_match_loser(sf1)
                    if loser1:
                        third_place_match["player1"] = loser1

                if sf2.get("winner") and third_place_match.get("player2") is None:
                    loser2 = self._get_match_loser(sf2)
                    if loser2:
                        third_place_match["player2"] = loser2

        # Turniersieger feststellen
        final_match = wb_rounds[-1][0]
        final_match_finished = final_match.get("winner") is not None

        third_place_match = self.bracket["final_bracket"][0]
        # Das Spiel um Platz 3 gilt als "beendet", wenn es entweder einen Sieger hat
        # oder wenn es gar nicht erst stattfinden kann (z.B. bei < 4 Spielern).
        third_place_finished = (
            not third_place_match.get("player1")
            or third_place_match.get("winner") is not None
        )

        if final_match_finished and third_place_finished:
            self.winner = final_match["winner"]

    def get_next_match(self) -> dict | None:
        """Sucht das nächste spielbare Match im K.o.-System."""
        # 1. Winners Bracket komplett durchsuchen (inkl. Finale)
        for round_matches in self.bracket["winners"]:
            if next_match := self._find_next_in_list(round_matches):
                return next_match

        # 2. Finalspiele (Spiel um Platz 3) prüfen
        return self._find_next_in_list(self.bracket["final_bracket"])

    def get_podium(self) -> dict | None:
        """Gibt die ersten drei Plätze für das K.o.-System zurück."""
        if not self.is_finished:
            return None

        final_match = self.bracket["winners"][-1][0]
        third_place_match = self.bracket["final_bracket"][0]

        return {
            "first": self.winner,
            "second": self._get_match_loser(final_match),
            "third": third_place_match.get("winner"),
        }


class DoubleEliminationStrategy(TournamentStrategyBase):
    """Strategie für ein Doppel-K.o.-System mit Grand Final und Bracket-Reset."""

    def _create_initial_bracket(self, players: list[str], shuffle: bool = True) -> dict:
        players_for_r1, players_with_byes = self._prepare_initial_players(
            players, shuffle
        )

        round1_matches = self._create_matches_from_players(players_for_r1)
        for player_with_bye in players_with_byes:
            round1_matches.append(
                {
                    "player1": player_with_bye,
                    "player2": "BYE",
                    "winner": player_with_bye,
                }
            )

        wb_rounds = [round1_matches]
        current_round_size = len(round1_matches)
        while current_round_size > 1:
            next_round_size = current_round_size // 2
            next_round_matches = [
                {"player1": None, "player2": None, "winner": None}
                for _ in range(next_round_size)
            ]
            wb_rounds.append(next_round_matches)
            current_round_size = next_round_size

        # Erstelle die Platzhalter-Struktur für das Losers Bracket
        lb_rounds = []
        if len(wb_rounds) > 1:
            num_lb_rounds = 2 * (len(wb_rounds) - 1)
            num_matches_in_lb_round = len(wb_rounds[0]) // 2
            for i in range(num_lb_rounds):
                if num_matches_in_lb_round > 0:
                    placeholder_round = [
                        {"player1": None, "player2": None, "winner": None}
                        for _ in range(num_matches_in_lb_round)
                    ]
                    lb_rounds.append(placeholder_round)
                if (i + 1) % 2 == 0 and num_matches_in_lb_round > 1:
                    num_matches_in_lb_round //= 2

        return {
            "winners": wb_rounds,
            "losers": lb_rounds,
            "grand_final": [],  # Kann 1 oder 2 Matches enthalten
        }

    def _update_bracket_state(self):
        """Orchestriert den Update-Prozess für das gesamte Doppel-K.o.-Bracket."""
        if self.is_finished:
            return

        self._update_winners_bracket()
        self._update_losers_bracket()
        self._update_grand_final()

    def _update_winners_bracket(self):
        """Aktualisiert das Winners Bracket, indem Gewinner in die nächste Runde vorrücken."""
        wb_rounds = self.bracket["winners"]
        for round_idx in range(len(wb_rounds) - 1):
            for match_idx, child_match in enumerate(wb_rounds[round_idx + 1]):
                parent1 = wb_rounds[round_idx][match_idx * 2]
                parent2 = wb_rounds[round_idx][match_idx * 2 + 1]
                if parent1.get("winner") and not child_match.get("player1"):
                    child_match["player1"] = parent1["winner"]
                if parent2.get("winner") and not child_match.get("player2"):
                    child_match["player2"] = parent2["winner"]

    def _update_losers_bracket(self):
        """Aktualisiert das Losers Bracket, indem Verlierer und Gewinner platziert werden."""
        wb_rounds = self.bracket["winners"]
        lb_rounds = self.bracket["losers"]
        if not lb_rounds:
            return

        for lb_round_idx, lb_round in enumerate(lb_rounds):
            for lb_match_idx, match_to_fill in enumerate(lb_round):
                # Gerade Runden (0, 2, 4...) sind "interne" Runden im LB.
                if lb_round_idx % 2 == 0:
                    if lb_round_idx == 0:  # Erste LB-Runde, gefüttert von WB R1
                        wb_parent1 = wb_rounds[0][lb_match_idx * 2]
                        wb_parent2 = wb_rounds[0][lb_match_idx * 2 + 1]
                        if (
                            wb_parent1.get("winner")
                            and match_to_fill.get("player1") is None
                        ):
                            if loser := self._get_match_loser(wb_parent1):
                                match_to_fill["player1"] = loser
                        if (
                            wb_parent2.get("winner")
                            and match_to_fill.get("player2") is None
                        ):
                            if loser := self._get_match_loser(wb_parent2):
                                match_to_fill["player2"] = loser
                    else:  # Andere gerade Runden, gefüttert von vorheriger LB-Runde
                        lb_parent1 = lb_rounds[lb_round_idx - 1][lb_match_idx * 2]
                        lb_parent2 = lb_rounds[lb_round_idx - 1][lb_match_idx * 2 + 1]
                        if (
                            lb_parent1.get("winner")
                            and match_to_fill.get("player1") is None
                        ):
                            match_to_fill["player1"] = lb_parent1["winner"]
                        if (
                            lb_parent2.get("winner")
                            and match_to_fill.get("player2") is None
                        ):
                            match_to_fill["player2"] = lb_parent2["winner"]
                # Ungerade Runden (1, 3, 5...) sind "Feed-in"-Runden.
                else:
                    lb_parent = lb_rounds[lb_round_idx - 1][lb_match_idx]
                    wb_feed_round_idx = (lb_round_idx + 1) // 2
                    wb_parent = wb_rounds[wb_feed_round_idx][lb_match_idx]
                    if lb_parent.get("winner") and match_to_fill.get("player1") is None:
                        match_to_fill["player1"] = lb_parent["winner"]
                    if wb_parent.get("winner") and match_to_fill.get("player2") is None:
                        if wb_loser := self._get_match_loser(wb_parent):
                            match_to_fill["player2"] = wb_loser

    def _update_grand_final(self):
        """Erstellt das Grand Final und handhabt den Bracket-Reset."""
        wb_final = self.bracket["winners"][-1][0]
        lb_final = self.bracket["losers"][-1][0] if self.bracket["losers"] else None
        grand_final_matches = self.bracket["grand_final"]

        # 1. Erstelle das erste Grand Final Match, wenn die Voraussetzungen erfüllt sind
        if (
            wb_final.get("winner")
            and lb_final
            and lb_final.get("winner")
            and not grand_final_matches
        ):
            grand_final_matches.append(
                {
                    "player1": wb_final["winner"],
                    "player2": lb_final["winner"],
                    "winner": None,
                }
            )

        # 2. Prüfe den Zustand nach dem ersten Grand Final
        if len(grand_final_matches) == 1 and (gf1 := grand_final_matches[0]).get(
            "winner"
        ):
            wb_champion = gf1["player1"]
            lb_champion = gf1["player2"]

            if gf1["winner"] == wb_champion:
                # WB-Champion gewinnt, Turnier ist vorbei
                self.winner = wb_champion
            elif gf1["winner"] == lb_champion:
                # LB-Champion gewinnt, Bracket-Reset -> zweites Finale erstellen
                grand_final_matches.append(
                    {"player1": wb_champion, "player2": lb_champion, "winner": None}
                )

        # 3. Prüfe den Zustand nach dem zweiten Grand Final
        if len(grand_final_matches) == 2 and (gf2 := grand_final_matches[1]).get(
            "winner"
        ):
            self.winner = gf2["winner"]

    def get_next_match(self) -> dict | None:
        """Sucht das nächste spielbare Match im Doppel-K.o.-System."""
        # 1. Winners Bracket durchsuchen
        for round_matches in self.bracket["winners"]:
            if next_match := self._find_next_in_list(round_matches):
                return next_match
        # 2. Losers Bracket durchsuchen
        for round_matches in self.bracket["losers"]:
            if next_match := self._find_next_in_list(round_matches):
                return next_match
        # 3. Grand Final durchsuchen
        return self._find_next_in_list(self.bracket["grand_final"])

    def get_podium(self) -> dict | None:
        """Gibt die ersten drei Plätze für das Doppel-K.o.-System zurück."""
        if not self.is_finished:
            return None

        final_match = self.bracket["grand_final"][-1]
        lb_final = self.bracket["losers"][-1][0] if self.bracket["losers"] else None

        return {
            "first": self.winner,
            "second": self._get_match_loser(final_match),
            "third": self._get_match_loser(lb_final) if lb_final else None,
        }
