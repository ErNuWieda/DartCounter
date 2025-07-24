"""
Dieses Modul definiert die Hauptlogik für das Spiel "Elimination".
Es enthält die Elimination-Klasse, die den Spielablauf und die Regeln verwaltet.
"""
import tkinter as tk 
from tkinter import ttk, messagebox
from . import player 
from .player import Player
from . import scoreboard
from .scoreboard import ScoreBoard
from .game_logic_base import GameLogicBase

class Elimination(GameLogicBase):

    def __init__(self, game):
        super().__init__(game)
        self.count_to = game.count_to
        self.opt_out = game.opt_out
        # Ein transientes Protokoll, um Eliminierungen für die Undo-Funktion zu speichern.
        self.elimination_log = []
        # self.targets bleibt None aus der Basisklasse

    def initialize_player_state(self, player):
        """
        Setzt den Anfangs-Score für Elimination auf 0.
        """
        player.score = 0

    def get_scoreboard_height(self):
        """
        Gibt die spezifische, kleinere Höhe für Elimination-Scoreboards zurück.
        """
        return 240

    def get_targets(self):
        """
        Gibt die Zielliste zurück. Für Elimination gibt es keine festen Ziele.
        Gibt eine leere Liste zurück, um Kompatibilität zu gewährleisten.
        """
        return []
    
    def _handle_throw_undo(self, player, ring, segment, players):
        """Macht einen Wurf im Elimination-Modus rückgängig, inklusive Eliminierungen."""
        # 1. Prüfen, ob dieser Wurf eine Eliminierung ausgelöst hat.
        # Dies muss VOR der Korrektur des Werfer-Scores geschehen, da wir den
        # Zustand zum Zeitpunkt der Eliminierung benötigen.
        score_after_throw = player.score
        if self.elimination_log:
            last_elimination = self.elimination_log[-1]
            # Prüfen, ob die letzte Eliminierung vom aktuellen Spieler verursacht wurde
            # und sein aktueller Punktestand dem des Opfers vor der Eliminierung entspricht.
            if last_elimination['thrower_id'] == player.id and last_elimination['victim_score_before'] == score_after_throw:
                elimination_event = self.elimination_log.pop()
                
                # Finde das Opfer und stelle seinen Score wieder her
                victim = next((p for p in players if p.id == elimination_event['victim_id']), None)
                if victim:
                    victim.score = elimination_event['victim_score_before']
                    victim.sb.set_score_value(victim.score)

        # 2. Punktzahl des Werfers korrigieren
        score_to_undo = self.game.get_score(ring, segment)
        player.update_score_value(score_to_undo, subtract=True)

    def _handle_throw(self, player, ring, segment, players):
        score = self.game.get_score(ring, segment)

        if ring == "Miss":
            player.throws.append((ring, 0))
            # No messagebox for simple miss, score is 0.
            # player.update_score_value(score, subtract=True) # score is 0, so no change.
            player.sb.update_score(player.score) # Update display for throw history
            if len(player.throws) == 3:
                # Turn ends, user clicks "Weiter"
                return None
            return None # Throw processed


        new_score = player.score + score
        bust = False
        if new_score > self.count_to:
            bust = True # Direkt überworfen
        elif self.opt_out == "Double" and new_score == self.count_to and ring not in ("Double", "Bullseye"):
            bust = True # Gewinnwurf muss ein Double sein
        
        if bust:
            # The score will be as it was BEFORE this busting throw.
            player.throws.append((ring, segment)) # Mark the bust throw in history
            player.sb.update_score(player.score) # Update display

            messagebox.showerror("Bust", f"{player.name} hat überworfen!\nBitte 'Weiter' klicken.", parent=self.game.db.root)
            return None # Turn ends due to bust. Player clicks "Weiter".

        player.throws.append((ring, segment))
        player.update_score_value(score, subtract=False)

        # Prüfen, ob ein Gegner eliminiert wurde
        for opp in players:
            # Ein Gegner wird eliminiert, wenn sein Score mit dem des Werfers übereinstimmt
            # und der Score nicht 0 ist (man kann niemanden bei 0 eliminieren).
            if opp != player and player.score == opp.score and opp.score != 0:
                # Protokolliere den Zustand des Opfers VOR der Eliminierung
                self.elimination_log.append({
                    'thrower_id': player.id,
                    'victim_id': opp.id,
                    'victim_score_before': opp.score
                })
                
                # Eliminiere das Opfer
                opp.score = 0
                opp.sb.set_score_value(opp.score)
                messagebox.showinfo("Rauswurf", f"{player.name} schickt {opp.name} zurück an den Start!", parent=self.game.db.root)
                break # Es kann nur ein Gegner pro Wurf eliminiert werden

        if player.score == self.count_to:            
            self.game.end = True
            total_darts = player.get_total_darts_in_game()
            return f"🏆 {player.name} gewinnt in Runde {self.game.round} mit {total_darts} Darts!"

        if len(player.throws) == 3:
            # Turn ends, user clicks "Weiter"
            return None

        return None
