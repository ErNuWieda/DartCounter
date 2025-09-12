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
Dieses Modul definiert die Hauptlogik für verschiedene Dartspiele.
Es enthält die Game-Klasse, die den Spielablauf, die Spieler,
Punktestände und Regeln verwaltet.
"""
from .game_logic_base import GameLogicBase


class Killer(GameLogicBase):
    def __init__(self, game):
        super().__init__(game)
        self.players = []
        # Ein Protokoll, um Aktionen innerhalb eines Zugs für ein robustes Undo zu speichern.
        self.turn_log = []

    def initialize_player_state(self, player):
        """
        Setzt die Anzahl der Leben für das Killer-Spiel.
        """
        player.score = self.game.options.lifes
        player.state["life_segment"] = None
        player.state["can_kill"] = False

    def set_players(self, players):
        self.players = players

    def get_scoreboard_height(self):
        return 240

    def get_targets(self):
        return []

    def get_turn_start_message(self, player):
        """Gibt die passende Anweisung für die aktuelle Phase des Killer-Spiels zurück."""
        if not player.state.get("life_segment"):
            return (
                "info",
                "Lebensfeld ermitteln",
                (
                    f"{player.name}, du musst nun dein Lebensfeld bestimmen.\n"
                    "Wirf mit deiner NICHT-dominanten Hand.\n"
                    "Das Double des getroffenen Segments wird dein Lebensfeld.\n"
                ),
            )

        if not player.state.get("can_kill"):
            segment_str = (
                "Bull"
                if player.state["life_segment"] == "Bull"
                else f"Double {player.state['life_segment']}"
            )
            return (
                "info",
                "Zum Killer werden",
                (
                    f"{player.name}, jetzt musst du dein Lebensfeld ({segment_str}) treffen, "
                    "um Killer-Status zu erlangen."
                ),
            )

        return None  # In der Killer-Phase gibt es keine spezielle Nachricht.

    def _get_active_players(self):
        return [p for p in self.players if p.score > 0]

    def _check_and_handle_win_condition(self):
        active_players = self._get_active_players()
        if len(active_players) == 1:
            self.game.end = True
            winner = active_players[0]
            return ("win", f"🏆 {winner.name} gewinnt Killer in Runde {self.game.round}!")
        elif not active_players and len(self.players) > 0:
            self.game.end = True
            return "Niemand gewinnt! Alle Spieler wurden eliminiert."
        return None

    # --- UNDO LOGIK ---

    def _undo_set_life_segment(self, log_entry):
        """Macht das Setzen eines Lebensfeldes rückgängig."""
        player = log_entry["player"]
        player.state["life_segment"] = None
        return ("info", f"Lebensfeld für {player.name} zurückgesetzt.")

    def _undo_become_killer(self, log_entry):
        """Macht das Werden zum Killer rückgängig."""
        player = log_entry["player"]
        player.state["can_kill"] = False
        return ("info", f"{player.name} ist kein Killer mehr.")

    def _undo_take_life(self, log_entry):
        """Macht das Nehmen eines Lebens von einem Opfer (oder sich selbst) rückgängig."""
        victim = log_entry["victim"]
        if victim.score < self.game.options.lifes:
            victim.score += 1
            victim.sb.set_score_value(victim.score)
            return ("info", f"Leben für {victim.name} wiederhergestellt.")
        return ("ok", None)

    def _handle_throw_undo(self, player, ring, segment, players):
        """
        Macht einen Wurf rückgängig, indem die letzte protokollierte Aktion umgekehrt wird.
        """
        if not self.turn_log:
            player.sb.update_score(player.score)
            return ("ok", None)

        last_action = self.turn_log.pop()
        action_type = last_action.get("action")

        if action_type == "set_life_segment":
            return self._undo_set_life_segment(last_action)
        elif action_type == "become_killer":
            return self._undo_become_killer(last_action)
        elif action_type == "take_life":
            return self._undo_take_life(last_action)

        player.sb.update_score(player.score)

    # --- THROW HANDLING LOGIK ---

    def _handle_life_segment_phase(self, player, ring, segment, players):
        """Behandelt die Phase, in der ein Spieler sein Lebensfeld bestimmen muss."""
        determined_segment = ""
        if ring in ("Bull", "Bullseye"):
            determined_segment = "Bull"
        elif isinstance(segment, int) and 1 <= segment <= 20:
            determined_segment = str(segment)
        else:
            return ("warning", "Kein gültiges Segment für ein Lebensfeld getroffen.")

        is_taken = any(
            p != player and p.state["life_segment"] == determined_segment for p in players
        )
        if is_taken:
            occupier = next(
                p.name for p in players if p.state["life_segment"] == determined_segment
            )
            return (
                "warning",
                f"Das Segment '{determined_segment}' ist bereits an {occupier} vergeben.",
            )

        player.state["life_segment"] = determined_segment
        self.turn_log.append({"action": "set_life_segment", "player": player})

        determined_display = (
            "Bull" if determined_segment == "Bull" else f"Double {determined_segment}"
        )

        # KORREKTUR: Anstatt den Spielerwechsel direkt zu erzwingen, wird der Game-Klasse
        # signalisiert, dass der Zug beendet ist. Der Benutzer klickt dann auf "Weiter".
        # Dies hält die Undo-Kette intakt.
        player.turn_is_over = True
        return (
            "info",
            (f"{player.name} hat Lebensfeld: {determined_display}\nBitte 'Weiter' klicken."),
        )

    def _handle_become_killer_phase(self, player, ring, segment):
        """Behandelt die Phase, in der ein Spieler versucht, Killer zu werden."""
        is_hit_on_own_life_segment = (
            player.state["life_segment"] == "Bull" and ring in ("Bull", "Bullseye")
        ) or (str(segment) == player.state["life_segment"] and ring == "Double")

        if is_hit_on_own_life_segment:
            player.state["can_kill"] = True
            self.turn_log.append({"action": "become_killer", "player": player})
            return ("info", f"{player.name} ist jetzt ein KILLER!")
        else:
            life_segment_display = (
                "Bull"
                if player.state["life_segment"] == "Bull"
                else f"Double {player.state['life_segment']}"
            )
            player.sb.update_score(player.score)
            return (
                "info",
                f"{player.name} muss das eigene Lebensfeld ({life_segment_display}) treffen.",
            )

    def _handle_killer_phase(self, player, ring, segment, players):
        """Behandelt die Phase, in der ein Spieler als Killer agiert."""
        victim = None

        for p in self._get_active_players():
            is_hit_on_life_segment = (
                p.state["life_segment"] == "Bull" and ring in ("Bull", "Bullseye")
            ) or (str(segment) == p.state["life_segment"] and ring == "Double")
            if is_hit_on_life_segment:
                victim = p
                break

        if victim:
            victim.score -= 1
            self.turn_log.append({"action": "take_life", "victim": victim})
            victim.sb.set_score_value(victim.score)
            if victim == player:
                opp_name = "sich selbst"
            else:
                opp_name = victim.name

            if victim.score > 0:
                return (
                    "info",
                    f"{player.name} nimmt {opp_name} ein Leben!\n"
                    f"{victim.name} hat noch {victim.score} Leben.",
                )
            else:
                win_result = self._check_and_handle_win_condition()
                if win_result:
                    return win_result
                return ("info", f"{player.name} hat {opp_name} eliminiert!")

        player.sb.update_score(player.score)
        return ("ok", None)

    def _handle_throw(self, player, ring, segment, players):
        """
        Verarbeitet einen Wurf, indem er an die Methode für die aktuelle Spielphase delegiert.
        """
        if not player.throws:  # Erster Wurf des Zugs
            self.turn_log.clear()

        if not player.state.get("life_segment"):
            return self._handle_life_segment_phase(player, ring, segment, players)
        elif not player.state.get("can_kill"):
            return self._handle_become_killer_phase(player, ring, segment)
        else:
            return self._handle_killer_phase(player, ring, segment, players)
