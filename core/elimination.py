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

class Elimination:

    def __init__(self, game):
        self.game = game
        self.count_to = game.count_to
        self.opt_out = game.opt_out
        self.targets = None


    def get_targets(self):
        return self.targets
    
    def _handle_throw_undo(self, player, ring, segment, players):
        score = self.game.get_score(ring, segment)
        if score > 0:
            for opp in players:
                if opp != player and opp.score == 0:
                    opp.score = player.score
                    opp.sb.score_label.config(text=f"Score: {opp.score}")
                    break
            player.update_score_value(score, subtract=True)
        

    def _handle_throw(self, player, ring, segment, players):
        # --- x01 Logik ---
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
        elif self.opt_out == "Double":
            if new_score == self.count_to - 1: bust = True
            elif new_score == self.count_to and ring not in ("Double", "Bullseye"): bust = True
        
        if bust:
            # The score will be as it was BEFORE this busting throw.
            player.throws.append((ring, segment)) # Mark the bust throw in history
            player.sb.update_score(player.score) # Update display

            messagebox.showerror("Bust", f"{player.name} hat überworfen!\nBitte 'Weiter' klicken.")
            return None # Turn ends due to bust. Player clicks "Weiter".

        player.throws.append((ring, segment))
        player.update_score_value(score, subtract=False)

        for opp in players:
            if opp != player and player.score == opp.score:
                opp.score = 0
                opp.sb.score_label.config(text=f"Score: {opp.score}")
                messagebox.showinfo("Rauswurf", f"{player.name} schickt {opp.name} zurück an den Start!")
                break

        if player.score == self.count_to:            
            self.game.end = True
            total_darts = (self.game.round - 1) * 3 + len(player.throws)
            return f"🏆 {player.name} gewinnt in Runde {self.game.round} mit {total_darts} Darts!"

        if len(player.throws) == 3:
            # Turn ends, user clicks "Weiter"
            return None

        return None
