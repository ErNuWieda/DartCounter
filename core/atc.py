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

ATC_TARGET_VALUES = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12, "13": 13, "14": 14, "15": 15, "16": 16, "17": 17, "18": 18, "19": 19, "20": 20, "Bull": 25}

ATC_SEGMENTS_AS_STR = [str(s) for s in range(1, 21)] # "1" bis "20"

class AtC:
	def __init__(self, game):
		self.game = game
		self.opt_atc = game.opt_atc
		self.targets = [k for k in ATC_TARGET_VALUES.keys()]

	def get_targets(self):
		return self.targets
		
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
		player.throws.append((ring, segment))
		if ring == "Bullseye" and self.opt_atc == "Single":
		    ring = "Bull"
		if player.next_target not in (str(segment), ring) or (ring not in ("Bull", "Bullseye", self.opt_atc)): 
		# Wurf war ein Miss oder traf nicht das Ziel-Feld
		    player.sb.update_score(player.score)
		    if player.next_target in ("Bull", "Bullseye") or self.opt_atc == "Single":
		        opt_atc = ""
		    else:
		        opt_atc = self.opt_atc + " "
		    msg = f"{player.name} muss {opt_atc}{player.next_target} treffen!\nNoch {3 - len(player.throws)} verbleibende Darts."
		    messagebox.showerror("Ungültiger Wurf", msg)
		    if len(player.throws) == 3:
		        player.reset_turn()
		        self.game.next_player()            
		    return 

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
		
		if player.next_target == "Bull" and self.opt_atc != "Single":
		    player.next_target = "Bullseye"

		player.sb.update_display(player.hits, player.score) # ATC-Anzeige aktualisieren

		# --- Gewinnbedingung prüfen ---
		if all_targets_closed:
		    self.game.end = True
		    total_darts = (self.game.round - 1) * 3 + len(player.throws)
		    return f"🏆 {player.name} gewinnt {self.game.name} in Runde {self.game.round} mit {total_darts} Darts!"

		# --- Zug beenden / Nächster Spieler ---
		if len(player.throws) == 3:
		    player.reset_turn()
		    self.game.next_player()


