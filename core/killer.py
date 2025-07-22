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

class Killer(GameLogicBase):
	def __init__(self, game):
		super().__init__(game)
		self.players = [] # Wird später über set_players gesetzt

	def initialize_player_state(self, player):
		"""
		Setzt die Anzahl der Leben für das Killer-Spiel.
		Der 'lifes' Wert wird bereits im Player-Konstruktor über game.lifes gesetzt,
		diese Methode dient der Konsistenz des Designs.
		"""
		player.score = self.game.lifes

	def set_players(self, players):
		"""Setzt die Spielerliste für das Killer-Spiel."""
		self.players = players
		
	def get_scoreboard_height(self):
		"""
		Gibt die spezifische, kleinere Höhe für Killer-Scoreboards zurück.
		"""
		return 240

	def _get_active_players(self):
		"""Gibt eine Liste aller Spieler zurück, die noch Leben haben."""
		return [p for p in self.players if p.score > 0]

	def _check_and_handle_win_condition(self):
		"""Prüft auf Gewinnbedingung und gibt ggf. die Gewinnnachricht zurück."""
		active_players = self._get_active_players()
		if len(active_players) == 1:
			self.game.end = True
			winner = active_players[0]
			return f"🏆 {winner.name} gewinnt Killer in Runde {self.game.round}!"
		elif not active_players and len(self.players) > 0:
			self.game.end = True
			return "Niemand gewinnt! Alle Spieler wurden eliminiert."
		return None

	def _handle_throw_undo(self, player, ring, segment, players):
		"""
		Macht den letzten Wurf rückgängig, indem der Spielzustand wiederhergestellt wird.
		Diese Methode wird aufgerufen, NACHDEM der Wurf bereits aus player.throws entfernt wurde.
		Sie unterscheidet zwischen dem Rückgängigmachen des "Killer-Werdens" und einer
		Aktion als Killer.
		"""
		# --- Fall 1: Der Wurf hat den Spieler zum KILLER gemacht ---
		# Dies ist der Fall, wenn der Spieler aktuell ein Killer ist, aber noch keine
		# Aktion als Killer ausgeführt hat (killer_throws == 0).
		hit_own_life_segment = (player.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or \
							   (str(segment) == player.life_segment and ring == "Double")

		if player.can_kill and player.killer_throws == 0 and hit_own_life_segment:
			player.can_kill = False
			messagebox.showinfo("Rückgängig", f"{player.name} ist kein Killer mehr.", parent=self.game.db.root)
			player.sb.update_score(player.score)
			return # Aufgabe für diesen Fall erledigt.

		# --- Fall 2: Der Wurf war eine Aktion ALS KILLER ---
		# Dies ist der Fall, wenn der Spieler ein Killer ist und bereits geworfen hat.
		if player.can_kill and player.killer_throws > 0:
			# Zuerst immer den Zähler für Killer-Würfe reduzieren.
			player.killer_throws -= 1

			# Prüfen, ob dieser Wurf ein Lebensfeld getroffen und ein Leben gekostet hat.
			victim = None
			for p in self.players:
				is_victim_life_segment_hit = (p.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or \
											 (str(segment) == p.life_segment and ring == "Double")
				if is_victim_life_segment_hit:
					victim = p
					break
			
			if victim:
				# Ein Leben wurde genommen, also wird es wiederhergestellt.
				# self.game.lifes wird anstelle eines festen Werts verwendet.
				if victim.score < self.game.lifes:
					victim.score += 1
					victim.sb.update_score(victim.score)
					messagebox.showinfo("Rückgängig", f"Leben für {victim.name} wiederhergestellt.", parent=self.game.db.root)

		# --- Letzter Schritt: Scoreboard des aktuellen Spielers aktualisieren ---
		# Dies ist in allen Fällen notwendig, um Änderungen widerzuspiegeln (z.B. wenn er sich selbst ein Leben genommen hat).
		player.sb.update_score(player.score)

	def _handle_life_segment_phase(self, player, ring, segment):
		"""Behandelt die Phase, in der ein Spieler sein Lebensfeld bestimmen muss."""
		determined_segment_for_life = ""
		if ring in ("Bull", "Bullseye"):
			determined_segment_for_life = "Bull"
		elif isinstance(segment, int) and 1 <= segment <= 20:
			determined_segment_for_life = str(segment)
		else:
			msg = "Kein gültiges Segment für ein Lebensfeld getroffen."
			messagebox.showwarning("Fehler", msg + f"\nNoch {3 - len(player.throws)} Darts.", parent=self.game.db.root)
			player.sb.update_score(player.score)
			return None

		# Prüfen, ob dieses Segment bereits von einem anderen aktiven Spieler belegt ist
		is_taken = False
		for p_other in self.players:
			if p_other != player and p_other.life_segment == determined_segment_for_life:
				is_taken = True
				occupier = p_other.name
				break
		
		if is_taken:
			msg = f"Das Segment '{determined_segment_for_life}' ist bereits an {occupier} vergeben."
			messagebox.showwarning("Segment vergeben", msg + f"\nNoch {3 - len(player.throws)} Darts.", parent=self.game.db.root)
			player.sb.update_score(player.score)
			return None
		
		player.life_segment = determined_segment_for_life
		determined_display = "Bull" if player.life_segment == "Bull" else f"Double {player.life_segment}"
		messagebox.showinfo("Lebensfeld festgelegt!", f"{player.name} hat Lebensfeld: {determined_display}", parent=self.game.db.root)
		player.sb.update_score(player.score)
		player.reset_turn() # Zug endet, nachdem das Lebensfeld erfolgreich gesetzt wurde
		self.game.next_player()
		return None # Explizit None zurückgeben, da next_player schon aufgerufen wurde

	def _handle_become_killer_phase(self, player, ring, segment):
		"""Behandelt die Phase, in der ein Spieler versucht, Killer zu werden."""
		hit_own_life_segment = (player.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or \
							   (str(segment) == player.life_segment and ring == "Double")

		if hit_own_life_segment:
			player.can_kill = True
			messagebox.showinfo("Killer Status!", f"{player.name} ist jetzt ein KILLER!", parent=self.game.db.root)
		else:
			life_segment_display = "Bull" if player.life_segment == "Bull" else f"Double {player.life_segment}"
			messagebox.showinfo("Daneben", f"{player.name} muss das eigene Lebensfeld ({life_segment_display}) treffen, um Killer zu werden.", parent=self.game.db.root)
		
		player.sb.update_score(player.lifes)
		return None

	def _handle_killer_phase(self, player, ring, segment, players):
		"""Behandelt die Phase, in der ein Spieler als Killer agiert."""
		player.killer_throws += 1
		victim = None
		win_msg = None

		# Finde ein potenzielles Opfer
		for opp in self._get_active_players():
			# Ein Treffer zählt, wenn es das Lebensfeld des Gegners ist UND der richtige Ring getroffen wurde (Double oder Bull/Bullseye)
			is_opp_life_segment_hit = (opp.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or \
									  (str(segment) == opp.life_segment and ring == "Double")
			if is_opp_life_segment_hit:
				victim = opp
				break

		if victim:
			victim.lifes -= 1
			victim.sb.update_score(victim.lifes)
			
			title = "Leben genommen!"
			opp_name = victim.name
			if victim == player:
				title = "Eigentor"
				opp_name = "sich selbst"

			if victim.lifes > 0:
				messagebox.showinfo(title, f"{player.name} nimmt {opp_name} ein Leben!\n{victim.name} hat noch {victim.lifes} Leben.", parent=self.game.db.root)
			else:
				messagebox.showinfo("Eliminiert!", f"{player.name} hat {opp_name} eliminiert!", parent=self.game.db.root)
				win_msg = self._check_and_handle_win_condition()

		player.sb.update_score(player.lifes)
		return win_msg

	def _handle_throw(self, player, ring, segment, players):
		"""
		Verarbeitet einen Wurf, indem er an die Methode für die aktuelle Spielphase delegiert.
		"""
		player.throws.append((ring, segment))

		if not player.life_segment:
			return self._handle_life_segment_phase(player, ring, segment)
		elif not player.can_kill:
			return self._handle_become_killer_phase(player, ring, segment)
		else:
			return self._handle_killer_phase(player, ring, segment, players)