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

    def _handle_throw(self, player, ring, segment, players):
        """
        Verarbeitet einen einzelnen Wurf für einen Spieler in einem X01-Spiel.

        Dies ist die Kernmethode, die alle Spielregeln auf einen Wurf anwendet.
        Sie folgt einer Sequenz von Überprüfungen:
        1. Berechnet den Punktwert des Wurfs.
        2. Prüft, ob der Wurf eine Checkout-Möglichkeit darstellt.
        3. Validiert die 'Opt-In'-Regel, falls der Spieler noch nicht eröffnet hat.
        4. Validiert 'Bust'-Bedingungen basierend auf dem Restpunktestand und den
           'Opt-Out'-Regeln.
        5. Wenn der Wurf gültig ist, werden Punktestand und Statistiken des Spielers aktualisiert.
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
        # --- x01 Logik ---
        score = self.game.get_score(ring, segment)
        score_before_throw = player.score

        # Ein Wurf ist eine Checkout-Möglichkeit, wenn der Wurfscore dem Restscore entspricht.
        if score_before_throw == score:
            player.stats['checkout_opportunities'] += 1

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


        if not player.state['has_opened']:
            opened_successfully = False
            if self.opt_in == "Single":
                opened_successfully = True
            elif self.opt_in == "Double":
                if ring in ("Double", "Bullseye"):
                    opened_successfully = True
            elif self.opt_in == "Masters":
                if ring in ("Double", "Triple", "Bullseye"):
                    opened_successfully = True

            if opened_successfully:
                player.state['has_opened'] = True
            else:
                player.throws.append((ring, segment)) # Record the failed attempt
                player.sb.update_score(player.score) # Update display for throw history
                option_text = "Double" if self.opt_in == "Double" else "Double, Triple oder Bullseye"
                msg_base = f"{player.name} braucht ein {option_text} zum Start!"
                
                remaining_darts = 3 - len(player.throws)
                if len(player.throws) == 3:
                    messagebox.showerror("Ungültiger Wurf", msg_base + "\nLetzter Dart dieser Aufnahme. Bitte 'Weiter' klicken.", parent=self.game.db.root)
                else: # Show for every failed "in" throw
                    messagebox.showerror("Ungültiger Wurf", msg_base+f"\nNoch {remaining_darts} Darts.", parent=self.game.db.root)
                return None # End processing for this throw, turn might end or continue with next dart

        # If player.state['has_opened'] is true, or became true above, proceed to score

        new_score = player.score - score
        bust = False
        if new_score < 0:
            bust = True # Direkt überworfen
        elif self.opt_out == "Double":
            if new_score == 1: bust = True
            elif new_score == 0 and not (ring == "Double" or ring == "Bullseye"): bust = True
            elif self.opt_out == "Masters":
                if new_score == 1: bust = True
                elif new_score == 0 and ring not in ("Double", "Triple", "Bullseye"): bust = True
        
        if bust:
            # The score will be as it was BEFORE this busting throw.
            player.throws.append((ring, segment)) # Mark the bust throw in history
            player.sb.update_score(player.score) # Update display

            messagebox.showerror("Bust", f"{player.name} hat überworfen!\nBitte 'Weiter' klicken.", parent=self.game.db.root)
            return None # Turn ends due to bust. Player clicks "Weiter".

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
            total_darts = (self.game.round - 1) * 3 + len(player.throws)
            
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
