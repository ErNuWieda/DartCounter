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

class X01:

    def __init__(self, game):
        self.game = game
        self.opt_in = game.opt_in
        self.opt_out = game.opt_out
        self.shanghai_finish = False
        self.targets = None


    def get_targets(self):
        return self.targets
    

    def _handle_throw(self, player, ring, segment, players):
        # --- x01 Logik ---
        score = self.game.get_score(ring, segment)

        if ring == "Miss":
            player.throws.append((ring, 0))
            messagebox.showerror("Daneben", f"{player.name} verfehlt!")
            player.update_score_value(score, subtract=True) # score ist hier 0 für Miss
            if len(player.throws) == 3:
                player.reset_turn()
                self.game.next_player()
            return 

        if not player.has_doubled_in:
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
                player.has_doubled_in = True
            else:
                player.throws.append((ring, 0)) 
                option_text = "Double" if self.opt_in == "Double" else "Double, Triple oder Bullseye"
                msg = f"{player.name} braucht ein {option_text} zum Start!"
                if len(player.throws) == 3:
                    messagebox.showerror("Ungültiger Wurf", msg)
                    player.reset_turn()
                    self.game.next_player()
                messagebox.showerror("Ungültiger Wurf", msg+f"\nNoch {3 - len(player.throws)} Darts.")
                return 


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
            player.throws.append((ring, 0))
            messagebox.showerror("Bust", f"{player.name} hat überworfen! Nächster Spieler.")
            player.reset_turn() # Würfe zurücksetzen, Score bleibt wie vor dem Bust
            self.game.next_player()
            return 

        player.throws.append((ring, segment))
        player.update_score_value(score, subtract=True)

        if player.score == 0: # Gilt nur für x01
            if self.opt_out == "Double" and len(player.throws) == 3:
                finish_score = 0
                for throw in player.throws:
                    match throw[0]:
                        case "Single":
                            finish_score += throw[1]
                        case "Double":
                            finish_score += throw[1] * 2
                        case "Triple":
                            finish_score += throw[1] * 3     
                if finish_score == 120:
                    self.shanghai_finish = True
            self.game.end = True
            total_darts = (self.game.round - 1) * 3 + len(player.throws)
            return f"🏆 {player.name} gewinnt in Runde {self.game.round} mit {total_darts} Darts!"
        
        if len(player.throws) == 3:
            player.reset_turn()
            self.game.next_player()
            return None 

        return None
