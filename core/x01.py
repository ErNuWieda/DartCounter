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
import tkinter as tk 
from tkinter import ttk, messagebox
from . import player 
from .player import Player
from . import scoreboard
from .scoreboard import ScoreBoard
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
        self.opt_in = game.opt_in
        self.opt_out = game.opt_out
        # self.targets bleibt None aus der Basisklasse

    def get_targets(self):
        """
        Gibt die Zielliste zurück. Für X01 gibt es keine festen Ziele.
        Gibt eine leere Liste zurück, um Kompatibilität zu gewährleisten.
        """
        return []
    
    def initialize_player_state(self, player):
        """
        Setzt den Anfangs-Score für X01-Spiele und initialisiert den 'opened'-Status.
        """
        player.score = int(self.game.name)
        # 'has_opened' wird im state-Dictionary des Spielers gespeichert,
        # das bereits in der Player-Klasse initialisiert wird.
        player.has_opened = False

    def get_scoreboard_height(self):
        """
        Gibt die spezifische Höhe für X01-Scoreboards zurück (für Stats und Finish-Vorschläge).
        """
        return 430

    def _handle_throw_undo(self, player, ring, segment, players):
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
        
        throw_score = self.game.get_score(ring, segment)
        score_before_throw = player.score + throw_score

        opt_in = self.game.opt_in
        if opt_in != "Single":
            if (opt_in == "Double" and ring in ("Double", "Bullseye")) or (opt_in == "Masters" and ring in ("Double", "Triple", "Bullseye")):
                if score_before_throw == int(player.game_name):
                    player.state['has_opened'] = False
                    player.score = score_before_throw
        
        player.sb.update_score(player.score) # Update score
                    
        # --- Checkout-Statistik rückgängig machen ---
        # Prüfen, ob der rückgängig gemachte Wurf eine Checkout-Möglichkeit war.
        if score_before_throw == throw_score:
            if player.stats['checkout_opportunities'] > 0:
                player.stats['checkout_opportunities'] -= 1
            # Prüfen, ob es ein erfolgreicher Checkout war.
            if player.score == 0:
                if player.stats['checkouts_successful'] > 0:
                    player.stats['checkouts_successful'] -= 1
                # Das Zurücksetzen des 'highest_finish' ist komplex und wird hier ausgelassen,
                # da es das Speichern einer Liste aller Finishes erfordern würde.

        if player.state['has_opened']:
            player.update_score_value(throw_score, subtract=False)

        # Macht das Update der Statistik für gültige, punktende Würfe rückgängig.
        # Die Logik geht davon aus, dass nur Würfe, die nicht "Bust" waren, zur Statistik hinzugefügt wurden.
        # Wir prüfen auf score > 0, um "Miss"-Würfe auszuschließen.
        if throw_score > 0 and player.game_name in ('301', '501', '701'):
            if player.stats['total_darts_thrown'] > 0:
                player.stats['total_darts_thrown'] -= 1
            if player.stats['total_score_thrown'] >= throw_score:
                player.stats['total_score_thrown'] -= throw_score
        
        # Finish-Vorschlag für den wiederhergestellten Punktestand mit der korrekten Anzahl verbleibender Darts aktualisieren
        darts_remaining = 3 - len(player.throws)
        suggestion = CheckoutCalculator.get_checkout_suggestion(player.score, self.opt_out, darts_left=darts_remaining)
        player.sb.update_checkout_suggestion(suggestion)

    def _validate_opt_in(self, player, ring, segment):
        """
        Prüft, ob der Wurf die 'Opt-In'-Bedingung erfüllt und den Spieler öffnet.

        Args:
            player (Player): Der Spieler, der den Wurf gemacht hat.
            ring (str): Der getroffene Ring.
            segment (int): Das getroffene Segment.

        Returns:
            bool: True, wenn der Wurf gültig ist (oder der Spieler bereits offen war),
                  False, wenn der Wurf ungültig war.
        """
        if player.state['has_opened']:
            return True  # Bereits geöffnet, keine Prüfung nötig

        opened_successfully = False
        if self.opt_in == "Single":
            opened_successfully = True
        elif self.opt_in == "Double" and ring in ("Double", "Bullseye"):
            opened_successfully = True
        elif self.opt_in == "Masters" and ring in ("Double", "Triple", "Bullseye"):
            opened_successfully = True

        if opened_successfully:
            player.state['has_opened'] = True
            return True
        else:
            # Ungültiger Versuch, Wurf protokollieren und Fehlermeldung anzeigen
            player.throws.append((ring, segment))
            player.sb.update_score(player.score)  # Update display for throw history
            option_text = "Double" if self.opt_in == "Double" else "Double, Triple oder Bullseye"
            msg_base = f"{player.name} braucht ein {option_text} zum Start!"
            
            remaining_darts = 3 - len(player.throws)
            if len(player.throws) == 3:
                messagebox.showerror("Ungültiger Wurf", msg_base + "\nLetzter Dart dieser Aufnahme. Bitte 'Weiter' klicken.", parent=self.game.db.root)
            else:
                messagebox.showerror("Ungültiger Wurf", msg_base + f"\nNoch {remaining_darts} Darts.", parent=self.game.db.root)
            return False

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
            if new_score == 1: return True
            if new_score == 0 and ring not in ("Double", "Bullseye"): return True
        elif self.opt_out == "Masters":
            if new_score == 1: return True
            if new_score == 0 and ring not in ("Double", "Triple", "Bullseye"): return True
        
        return False

    def _handle_throw(self, player, ring, segment, players):
        """
        Verarbeitet einen einzelnen Wurf für einen Spieler in einem X01-Spiel.

        Dies ist die Kernmethode, die alle Spielregeln auf einen Wurf anwendet.
        Sie folgt einer Sequenz von Überprüfungen:
        1. Berechnet den Punktwert und prüft auf Checkout-Möglichkeiten.
        2. Delegiert die 'Opt-In'-Validierung an `_validate_opt_in`.
        3. Delegiert die 'Bust'-Validierung an `_check_for_bust`.
        4. Wenn der Wurf gültig ist, werden Punktestand und Statistiken aktualisiert.
        6. Prüft auf eine Gewinnbedingung (Punktestand ist genau null).
        7. Bei einem Gewinn wird auf ein spezielles 'Shanghai'-Finish geprüft und
           der Punktestand an den Highscore-Manager übermittelt.

        Args:
            player (Player): Der Spieler, der den Wurf gemacht hat.
            ring (str): Der getroffene Ring (z.B. 'Single', 'Double').
            segment (int): Die getroffene Segmentnummer.
            players (list[Player]): Die Liste aller Spieler im Spiel.

        Returns:
            str or None: Eine Gewinnnachricht, wenn das Spiel gewonnen wurde, ansonsten None.
        """
        score = self.game.get_score(ring, segment)
        score_before_throw = player.score

        # --- Checkout-Möglichkeit prüfen ---
        # Wenn der Wurf den Score exakt auf 0 bringen würde, war es eine Checkout-Möglichkeit.
        # Dies wird VOR der Bust-Prüfung gezählt.
        if score_before_throw == score and self.opt_out in ("Double", "Masters"):
             player.stats['checkout_opportunities'] += 1

        # --- Handle Miss separately ---
        if ring == "Miss":
            player.throws.append((ring, 0))
            # No messagebox for simple miss, score is 0.
            # player.update_score_value(score, subtract=True) # score is 0, so no change.
            player.sb.update_score(player.score) # Nur Wurfhistorie und Stats aktualisieren
            
            # Finish-Vorschlag für die verbleibenden Darts aktualisieren
            darts_remaining = 3 - len(player.throws)
            suggestion = CheckoutCalculator.get_checkout_suggestion(player.score, self.opt_out, darts_left=darts_remaining)
            player.sb.update_checkout_suggestion(suggestion)

            if len(player.throws) == 3:
                # Turn ends, user clicks "Weiter"
                return None
            return None # Throw processed

        # --- Opt-In-Validierung ---
        if not self._validate_opt_in(player, ring, segment):
            return None  # Wurf war ungültig, Verarbeitung abbrechen

        # --- Bust-Prüfung ---
        new_score = player.score - score
        if self._check_for_bust(new_score, ring):
            player.throws.append((ring, segment)) # Mark the bust throw in history
            player.sb.update_score(player.score) # Update display
            messagebox.showerror("Bust", f"{player.name} hat überworfen!\nBitte 'Weiter' klicken.", parent=self.game.db.root)
            return None # Turn ends due to bust.

        # Dies ist ein gültiger, nicht überworfener Wurf. Aktualisiere die Statistik.
        # Dies geschieht NACH den "Open"- und "Bust"-Prüfungen.
        if player.game_name in ('301', '501', '701'):
            player.stats['total_darts_thrown'] += 1
            player.stats['total_score_thrown'] += score

        player.throws.append((ring, segment))
        player.update_score_value(score, subtract=True)

        # Finish-Vorschlag für den neuen Punktestand mit den verbleibenden Darts berechnen und anzeigen
        darts_remaining = 3 - len(player.throws)
        suggestion = CheckoutCalculator.get_checkout_suggestion(player.score, self.opt_out, darts_left=darts_remaining)
        player.sb.update_checkout_suggestion(suggestion)

        if player.score == 0: # Gilt nur für x01
            # --- Checkout-Statistik bei Gewinn aktualisieren ---
            player.stats['checkouts_successful'] += 1
            # Höchsten Finish aktualisieren
            if score_before_throw > player.stats['highest_finish']:
                player.stats['highest_finish'] = score_before_throw

            self.game.shanghai_finish = False # Standardmäßig kein Shanghai-Finish

            if len(player.throws) == 3:
                # Prüfen auf spezifisches "120 Shanghai-Finish" (T20, S20, D20 in beliebiger Reihenfolge)
                # player.throws enthält Tupel (ring_name, segment_value_oder_punkte)
                # segment_value_oder_punkte ist die Segmentnummer (1-20) oder Punkte (25/50 für Bull/Bullseye)

                all_darts_on_20_segment = True
                rings_hit_on_20 = set()

                for r_name, seg_val_or_pts in player.throws:
                    if seg_val_or_pts == 20: # Muss das Segment 20 sein
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
                
                if all_darts_on_20_segment and rings_hit_on_20 == {"Single", "Double", "Triple"}:
                    # Alle drei Darts auf Segment 20 und die Ringe sind S, D, T.
                    # Die Summe ist implizit 120 (20 + 40 + 60), und da player.score == 0 ist, war es ein 120er Finish.
                    self.game.shanghai_finish = True
            
            self.game.end = True
            total_darts = player.get_total_darts_in_game()
            
            # Zum Highscore hinzufügen, falls Manager vorhanden
            if self.game.highscore_manager:
                self.game.highscore_manager.add_score(self.game.name, player.name, total_darts)

            # Die Nachricht im DartBoard wird "SHANGHAI-FINISH!" voranstellen,
            # wenn self.game.shanghai_finish True ist.
            return f"🏆 {player.name} gewinnt in Runde {self.game.round} mit {total_darts} Darts!"

        if len(player.throws) == 3:
            # Turn ends, user clicks "Weiter"
            return None

        return None
