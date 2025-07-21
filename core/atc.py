"""
Dieses Modul definiert die Hauptlogik für verschiedene Dartspiele.
Es enthält die Game-Klasse, die den Spielablauf, die Spieler,
Punktestände und Regeln verwaltet.
"""
import tkinter as tk 
from tkinter import ttk, messagebox
from . import player 
from .player import Player
from . import scoreboard
from .scoreboard import ScoreBoard
from .game_logic_base import GameLogicBase

ATC_TARGET_VALUES = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12, "13": 13, "14": 14, "15": 15, "16": 16, "17": 17, "18": 18, "19": 19, "20": 20, "Bull": 25}

ATC_SEGMENTS_AS_STR = [str(s) for s in range(1, 21)] # "1" bis "20"

class AtC(GameLogicBase):
	def __init__(self, game):
		super().__init__(game)
		self.opt_atc = game.opt_atc
		self.targets = [k for k in ATC_TARGET_VALUES.keys()]

	def initialize_player_state(self, player):
		"""
		Setzt den Anfangs-Score auf 0, initialisiert die Treffer-Map und das erste Ziel.
		"""
		player.score = 0
		if self.targets:
			player.next_target = self.targets[0]
			for target in self.targets:
				player.hits[target] = 0

	def _handle_throw_undo(self, player, ring, segment, players):
		# --- Treffer auf AtC-Ziel verarbeiten ---
		if player.next_target not in ("Bull", "Bullseye"):
		    player.hits[str(segment)] = 0
		else:
		    player.hits["Bull"] = 0
		
		# Nächstes Ziel zurücksetzen
		all_targets_closed = True
		for target in player.targets:
		    hit = player.hits.get(target, 0)
		    if hit == 0:
		        all_targets_closed = False
		        player.next_target = target
		        break
		
		player.sb.update_display(player.hits, player.score) # Update display after successful hit
		
		return

		
	def _handle_throw(self, player, ring, segment, players):
		"""
		Verarbeitet einen Wurf im "Around the Clock" (ATC) Modus.
		Prüft, ob das korrekte Ziel getroffen wurde, aktualisiert den Fortschritt
		und prüft auf Gewinnbedingungen.

		Args:
		    player (Player): Der Spieler, der den Wurf ausgeführt hat.
		    ring (str): Der getroffene Ring.
		    segment (int/str): Das getroffene Segment.

		Returns:
		    str or None: Eine Nachricht über den Spielausgang oder den Wurf, oder None.
		"""
		player.throws.append((ring, segment)) # Append throw at the beginning

        # Determine if the throw is valid for the current target
		is_valid_hit = False
		current_target_is_bull_type = player.next_target in ("Bull", "Bullseye")

		if current_target_is_bull_type:
			if player.next_target == "Bull" and ring == "Bull": # Single Bull for "Bull" target
				is_valid_hit = True
			elif player.next_target == "Bullseye" and ring == "Bullseye": # Bullseye for "Bullseye" target
				is_valid_hit = True
            # If opt_atc is "Single", Bullseye counts as Bull if target is Bull
			elif self.opt_atc == "Single" and player.next_target == "Bull" and ring == "Bullseye":
				ring = "Bull" # Treat as Bull hit for logic below, actual ring was Bullseye
				is_valid_hit = True
		else: # Target is a number segment
			if str(segment) == player.next_target: # Correct number segment
				if self.opt_atc == "Single" and ring == "Single":
					is_valid_hit = True
				elif self.opt_atc == "Double" and ring == "Double":
					is_valid_hit = True
				elif self.opt_atc == "Triple" and ring == "Triple":
					is_valid_hit = True
        
		if not is_valid_hit:
			player.sb.update_score(player.score) # Update display for throw history
            
			opt_atc_display = ""
			if not current_target_is_bull_type and self.opt_atc != "Single":
				opt_atc_display = self.opt_atc + " "
            
			base_msg = f"{player.name} muss {opt_atc_display}{player.next_target} treffen!"
            
			remaining_darts = 3 - len(player.throws)
			if remaining_darts > 0:
				messagebox.showerror("Ungültiger Wurf", base_msg + f"\nNoch {remaining_darts} verbleibende Darts.", parent=self.game.db.root)
			else: # Last dart of the turn
				messagebox.showerror("Ungültiger Wurf", base_msg + "\nLetzter Dart dieser Aufnahme. Bitte 'Weiter' klicken.", parent=self.game.db.root)
			return None # End processing for this throw

		# --- Treffer auf AtC-Ziel verarbeiten ---
		if player.next_target not in ("Bull", "Bullseye"):
		    player.hits[str(segment)] = 1
		else:
		    player.hits["Bull"] = 1
		
		# Nächstes Ziel bestimmen oder Gewinnbedingung prüfen
		all_targets_closed = True
		for target in player.targets:
		    hit = player.hits.get(target, 0)
		    if hit == 0:
		        all_targets_closed = False
		        player.next_target = target
		        break
		
		# Logic for advancing from Bull to Bullseye if not single
		if player.next_target == "Bull" and self.opt_atc != "Single" and player.hits.get("Bull", 0) == 1 and not all_targets_closed :
			if "Bullseye" in player.targets: # Ensure Bullseye is a target
				player.next_target = "Bullseye"

		player.sb.update_display(player.hits, player.score) # Update display after successful hit

		# --- Gewinnbedingung prüfen ---
		if all_targets_closed:
		    self.game.end = True
		    total_darts = (self.game.round - 1) * 3 + len(player.throws)
		    return f"🏆 {player.name} gewinnt {self.game.name} in Runde {self.game.round} mit {total_darts} Darts!"

		# --- Weiter / Nächster Spieler ---
		if len(player.throws) == 3:
            # Turn ends
			return None
        
		return None # Throw processed, turn continues
