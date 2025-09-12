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
Dieses Modul definiert die Hauptlogik für x01 Dartspiele.
Es enthält die x01 Klasse, die den Spielablauf, die Spieler,
Punktestände und Regeln verwaltet.
"""
from .player import Player
from .game_logic_base import GameLogicBase
from .checkout_calculator import CheckoutCalculator


class X01(GameLogicBase):
    """
    Behandelt die spezifische Spiellogik für alle X01-Varianten (z.B. 301, 501, 701).

    Diese Klasse ist verantwortlich für die Verarbeitung von Würfen, die Anwendung von
    Regeln für das Eröffnen (Opt-In) und Schließen (Opt-Out) des Spiels, die
    Erkennung von "Bust"-Bedingungen und die Ermittlung eines Gewinners. Sie
    interagiert mit dem Haupt-`Game`-Objekt, um auf den gemeinsamen Zustand und
    Spielerinformationen zuzugreifen.
    """

    def __init__(self, game):
        """
        Initialisiert den X01-Spiellogik-Handler.

        Args:
            game (Game): Die Haupt-Spielinstanz, die Zugriff auf Spieloptionen
                         und den allgemeinen Zustand bietet.
        """
        super().__init__(game)
        self.opt_in = game.options.opt_in
        self.opt_out = game.options.opt_out
        # self.targets bleibt None aus der Basisklasse

    def get_targets(self):
        """
        Gibt die Zielliste zurück. Für X01 gibt es keine festen Ziele.
        Gibt eine leere Liste zurück, um Kompatibilität zu gewährleisten.
        """
        return []

    def initialize_player_state(self, player: "Player"):
        """
        Setzt den Anfangs-Score für X01-Spiele und initialisiert den 'opened'-Status.
        """
        player.score = int(self.game.options.name)
        # 'has_opened' wird im state-Dictionary des Spielers gespeichert,
        # das bereits in der Player-Klasse initialisiert wird.
        player.has_opened = False
        # Setzt Leg-spezifische Statistiken wie den Average zurück.
        player.reset_leg_stats()

    def get_scoreboard_height(self):
        """
        Gibt die spezifische Höhe für X01-Scoreboards zurück (für Stats und Finish-Vorschläge).
        """
        return 430

    def _is_valid_opening_throw(self, ring: str) -> bool:
        """Prüft, ob ein Wurf die aktuelle Opt-In-Bedingung erfüllt."""
        if self.opt_in == "Single":
            return True
        if self.opt_in == "Double":
            return ring in ("Double", "Bullseye")
        if self.opt_in == "Masters":
            return ring in ("Double", "Triple", "Bullseye")
        return False

    def _handle_throw_undo(self, player: "Player", ring, segment, players):
        """
        Macht den letzten Wurf für einen Spieler rückgängig.

        Stellt den Zustand des Spielers vor dem letzten Wurf wieder her. Dies
        umfasst die Neuberechnung des Punktestands und die Korrektur von
        Statistiken wie Checkout-Möglichkeiten und dem 3-Dart-Average.

        Args:
            player (Player): Der Spieler, dessen Wurf rückgängig gemacht wird.
            ring (str): Der Ring des rückgängig zu machenden Wurfs.
            segment (int): Das Segment des rückgängig zu machenden Wurfs.
            players (list[Player]): Die Liste aller Spieler (in dieser Methode ungenutzt).
        """
        # 1. Wurf- und Score-Werte berechnen
        throw_score = self.game.get_score(ring, segment)
        if throw_score == 0:  # Miss-Wurf, nichts zu tun außer UI-Update
            # Der Wurf ist bereits aus player.throws entfernt, also ist die Anzahl der Darts für den Vorschlag korrekt.
            preferred_double = player.profile.preferred_double if player.profile else None
            darts_remaining = 3 - len(player.throws)
            suggestion = CheckoutCalculator.get_checkout_suggestion(
                player.score,
                self.opt_out,
                darts_left=darts_remaining,
                preferred_double=preferred_double,
            )
            player.sb.update_checkout_suggestion(suggestion)
            player.sb.update_score(player.score)
            return

        score_after_throw = player.score
        score_before_throw = score_after_throw + throw_score
        was_winning_throw = score_after_throw == 0

        # 2. Statistiken zurücksetzen (muss vor der Score-Änderung geschehen)
        player.stats["total_darts_thrown"] -= 1
        player.stats["total_score_thrown"] -= throw_score

        # Checkout-Statistiken zurücksetzen, falls es eine Checkout-Möglichkeit war
        if score_before_throw == throw_score and self.opt_out != "Single":
            player.stats["checkout_opportunities"] -= 1
            if was_winning_throw:
                player.stats["checkouts_successful"] -= 1
                finishes = player.stats.get("successful_finishes", [])
                if score_before_throw in finishes:
                    finishes.remove(score_before_throw)
                player.stats["highest_finish"] = max(finishes) if finishes else 0

        # 3. Spieler-Zustand (Score und 'has_opened') wiederherstellen
        was_opening_throw = (
            player.has_opened
            and score_before_throw == int(player.game.options.name)
            and self._is_valid_opening_throw(ring)
        )
        if was_opening_throw:
            player.has_opened = False
        player.score = score_before_throw

        # 4. UI aktualisieren
        preferred_double = player.profile.preferred_double if player.profile else None
        darts_remaining = 3 - len(player.throws)
        suggestion = CheckoutCalculator.get_checkout_suggestion(
            player.score,
            self.opt_out,
            darts_left=darts_remaining,
            preferred_double=preferred_double,
        )
        player.sb.update_checkout_suggestion(suggestion)
        player.sb.update_score(player.score)

    def _validate_opt_in(self, player, ring, segment):
        """# noqa: E501
        Prüft, ob der Wurf die 'Opt-In'-Bedingung erfüllt und den Spieler öffnet.

        Args:
            player (Player): Der Spieler, der den Wurf gemacht hat.
            ring (str): Der getroffene Ring.
            segment (int): Das getroffene Segment.

        Returns:
            bool: True, wenn der Wurf gültig ist (oder der Spieler bereits offen war),
                  False, wenn der Wurf ungültig war.
        """
        if player.state["has_opened"]:
            return True  # Bereits geöffnet, keine Prüfung nötig

        opened_successfully = self._is_valid_opening_throw(ring)

        if opened_successfully:
            player.state["has_opened"] = True
            return True

        # Ungültiger Versuch, Wurf protokollieren und Fehlermeldung anzeigen
        player.sb.update_score(player.score)  # Update display for throw history (now in Game.throw)
        option_text = "Double" if self.opt_in == "Double" else "Double, Triple oder Bullseye"
        msg_base = f"{player.name} braucht ein {option_text} zum Start!"
        remaining_darts = 3 - len(player.throws)
        if len(player.throws) == 3:
            msg = msg_base + "\nLetzter Dart dieser Aufnahme. Bitte 'Weiter' klicken."
            return ("invalid_open", msg)

        return ("invalid_open", msg_base + f"\nNoch {remaining_darts} Darts.")

    def _check_for_bust(self, new_score, ring):
        """
        Prüft, ob der Wurf basierend auf dem neuen Punktestand und den Opt-Out-Regeln
        zu einem 'Bust' führt.

        Args:
            new_score (int): Der hypothetische Punktestand nach dem Wurf.
            ring (str): Der getroffene Ring (wichtig für Double/Masters Out).

        Returns:
            bool: True, wenn der Wurf ein Bust ist, sonst False.
        """
        if new_score < 0:
            return True  # Direkt überworfen

        if self.opt_out == "Double":
            if new_score == 1:
                return True
            if new_score == 0 and ring not in ("Double", "Bullseye"):
                return True
        elif self.opt_out == "Masters":
            if new_score == 1:
                return True
            if new_score == 0 and ring not in ("Double", "Triple", "Bullseye"):
                return True

        return False

    def _is_shanghai_finish(self, player: "Player"):
        """Prüft, ob die drei Würfe des Spielers ein 120er Shanghai-Finish ergeben."""
        if len(player.throws) != 3:
            return False

        # Prüfen auf spezifisches "120 Shanghai-Finish" (T20, S20, D20 in beliebiger Reihenfolge)
        # player.throws enthält Tupel (ring_name, segment, coords)
        all_darts_on_20_segment = True
        rings_hit_on_20 = set()

        for r_name, seg_val, _ in player.throws:  # Coords ignorieren
            if seg_val == 20:  # Muss das Segment 20 sein
                if r_name in ("Single", "Double", "Triple"):
                    rings_hit_on_20.add(r_name)
                else:
                    # Getroffenes Segment 20, aber kein S, D, oder T Ring (sollte nicht vorkommen bei korrekter Segmenterkennung)
                    all_darts_on_20_segment = False
                    break
            else:
                # Ein Wurf war nicht auf Segment 20
                all_darts_on_20_segment = False
                break

        return all_darts_on_20_segment and rings_hit_on_20 == {
            "Single",
            "Double",
            "Triple",
        }

    def _handle_win_condition(self, player: "Player", score_before_throw):
        """Behandelt die Logik, wenn ein Spieler das Spiel gewinnt (Score erreicht 0)."""
        player.stats.setdefault("successful_finishes", []).append(score_before_throw)
        player.stats["checkouts_successful"] += 1
        player.stats["highest_finish"] = max(
            player.stats.get("highest_finish", 0),
            score_before_throw,
        )

        self.game.shanghai_finish = self._is_shanghai_finish(player)

        self.game.end = True
        self.game.winner = player
        total_darts = player.get_total_darts_in_game()

        # Die Nachricht im DartBoard wird "SHANGHAI-FINISH!" voranstellen,
        return f"🏆 {player.name} gewinnt in Runde {self.game.round} mit {total_darts} Darts!"

    def _handle_throw(self, player: "Player", ring: str, segment: int, players: list["Player"]):
        """Verarbeitet einen einzelnen Wurf für einen Spieler in einem X01-Spiel. # noqa

        Args:
            player (Player): Der Spieler, der den Wurf gemacht hat.
            ring (str): Der getroffene Ring (z.B. 'Single', 'Double').
            segment (int): Die getroffene Segmentnummer.
            players (list[Player]): Die Liste aller Spieler im Spiel.

        Returns:
            tuple[str, str | None]: Ein Tupel aus Status-String und optionaler Nachricht.
                                    Mögliche Status: 'ok', 'bust', 'win', 'invalid_open'.
        """
        score = self.game.get_score(ring, segment)
        score_before_throw = player.score

        # --- Checkout-Möglichkeit prüfen ---
        # Wenn der Wurf den Score exakt auf 0 bringen würde, war es eine Checkout-Möglichkeit.
        # Dies wird VOR der Bust-Prüfung gezählt.
        if score_before_throw == score and self.opt_out in ("Double", "Masters"):
            player.stats["checkout_opportunities"] += 1

        # --- Handle Miss separately ---
        if ring == "Miss":
            # No messagebox for simple miss, score is 0.
            # player.update_score_value(score, subtract=True) # score is 0, so no change.
            player.sb.update_score(player.score)

            preferred_double = player.profile.preferred_double if player.profile else None
            # Finish-Vorschlag für die verbleibenden Darts aktualisieren
            darts_remaining = 3 - len(player.throws)
            suggestion = CheckoutCalculator.get_checkout_suggestion(
                player.score,
                self.opt_out,
                darts_left=darts_remaining,
                preferred_double=preferred_double,
            )
            player.sb.update_checkout_suggestion(suggestion)

            if len(player.throws) == 3:
                # Turn ends, user clicks "Weiter"
                return ("ok", None)
            return ("ok", None)  # Throw processed

        # --- Opt-In-Validierung ---
        opt_in_result = self._validate_opt_in(player, ring, segment)
        if opt_in_result is not True:
            return opt_in_result  # Gibt das ('invalid_open', 'message') Tupel zurück

        # --- Bust-Prüfung ---
        new_score = player.score - score
        if self._check_for_bust(new_score, ring):
            player.turn_is_over = True
            player.sb.update_score(player.score)
            return ("bust", f"{player.name} hat überworfen!\nBitte 'Weiter' klicken.")

        # Dies ist ein gültiger, nicht überworfener Wurf. Aktualisiere die Statistik.
        # Dies geschieht NACH den "Open"- und "Bust"-Prüfungen.
        if player.has_opened:
            player.stats["total_darts_thrown"] += 1
            player.stats["total_score_thrown"] += score
        player.update_score_value(score, subtract=True)

        preferred_double = player.profile.preferred_double if player.profile else None
        darts_remaining = 3 - len(player.throws)
        suggestion = CheckoutCalculator.get_checkout_suggestion(
            player.score,
            self.opt_out,
            darts_left=darts_remaining,
            preferred_double=preferred_double,
        )
        player.sb.update_checkout_suggestion(suggestion)

        if player.score == 0:  # Gilt nur für x01
            win_message = self._handle_win_condition(player, score_before_throw)
            self.game._handle_leg_win(player)
            return ("win", win_message)

        if len(player.throws) == 3:
            # Turn ends, user clicks "Weiter"
            return ("ok", None)

        return ("ok", None)  # type: ignore
