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

class Killer:
	def __init__(self, game):
		self.game = game
		self.players = [] # Wird später über set_players gesetzt
		self.targets = None
	
	def get_targets(self):
		return self.targets

	def set_players(self, players):
		"""Setzt die Spielerliste für das Killer-Spiel."""
		self.players = players
		
	def _get_active_players(self):
		"""Gibt eine Liste aller Spieler zurück, die noch Leben haben."""
		return [p for p in self.players if p.lifes > 0]

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
		"""

		# --- Schritt 1: Möglichen Lebensverlust rückgängig machen ---
		# Wir müssen prüfen, ob der rückgängig gemachte Wurf einem Spieler ein Leben gekostet hat.
		# Das ist der Fall, wenn der Spieler ein Killer war UND ein gültiges Lebensfeld getroffen hat.
		
		# Rekonstruieren, ob der Spieler zum Zeitpunkt des Wurfs ein Killer war.

		if player.can_kill:
			# Finde das potenzielle Opfer
			victim = None
			is_killer_making_throw = False
			for p in self.players:
				life_segment_hit = (p.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or \
											 (str(segment) == p.life_segment and ring == "Double")
				if life_segment_hit:
					if p == player: 
						if player.killer_throws > 0:
							player.killer_throws -= 1
						else:
							is_killer_making_throw = True
							player.can_kill = False
							messagebox.showinfo("Rückgängig", f"{player.name} ist kein Killer mehr.")
					victim = p
					break

			if victim and not is_killer_making_throw:
				if victim.lifes < 3:
					victim.lifes += 1
					victim.sb.update_score(victim.lifes)
					messagebox.showinfo("Rückgängig", f"Leben für {victim.name} wiederhergestellt.")
		# --- Scoreboard des aktuellen Spielers aktualisieren ---
		player.sb.update_score(player.lifes)

	def _handle_throw(self, player, ring, segment, players):
		player.throws.append((ring, segment))
		win_msg = None

		# --- Phase 1: Spieler braucht ein Lebensfeld ---
		if not player.life_segment:
			determined_segment_for_life = ""
			# segment ist der numerische Wert (1-20, 25 für Bull, 50 für Bullseye)
			if ring in ("Bull", "Bullseye"):
				determined_segment_for_life = "Bull"
			elif isinstance(segment, int) and 1 <= segment <= 20:
				determined_segment_for_life = str(segment)
			else:
				msg = "Kein Segment für Lebensfeld"
				messagebox.showwarning("Fehler", msg + f"\nNoch {3 - len(player.throws)} Darts.")
				player.sb.update_score(player.lifes)
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
				messagebox.showwarning("Segment vergeben", msg + f"\nNoch {3 - len(player.throws)} Darts.")
				player.sb.update_score(player.lifes)
				return None
			
			player.life_segment = determined_segment_for_life
			determined = "Bullseye" if ring in ("Bull", "Bullseye") else f"Double {player.life_segment}"
			messagebox.showinfo("Lebensfeld festgelegt!", f"{player.name} hat Lebensfeld: {determined}")
			player.sb.update_score(player.lifes) # Scoreboard mit neuem Lebensfeld aktualisieren
			player.reset_turn() # Zug endet, nachdem das Lebensfeld erfolgreich gesetzt wurde
			self.game.next_player()
			return

		# --- Phase 2: Spieler ist noch kein Killer ---
		elif not player.can_kill:
			# ... (Logik aus vorheriger Antwort kann hier eingefügt werden) ...
			# Beispielhafte Kurzform:
			hit_own_life_segment = (player.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or \
			                       (str(segment) == player.life_segment and ring == "Double")

			if hit_own_life_segment:
				player.can_kill = True
				messagebox.showinfo("Killer Status!", f"{player.name} ist jetzt ein KILLER!")
			else:
				messagebox.showinfo("Daneben", f"{player.name} muss das eigene Lebensfeld treffen um Killer zu werden.")
			player.sb.update_score(player.lifes)

		# --- Phase 3: Spieler ist ein Killer ---
		else:
			player.killer_throws += 1
			victim = None
			for opp in self._get_active_players():
				is_opp_life_segment_hit = (opp.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or (str(segment) == opp.life_segment and opp.life_segment != "Bull")
				if is_opp_life_segment_hit and ring in ("Bull", "Bullseye", "Double"):
					victim = opp
					break

			if victim:
				victim.lifes -= 1
				victim.sb.update_score(victim.lifes)
				if victim == player:
					title = "Eigentor"
					opp_name = "sich selbst"
				else:
					title = "Leben genommen!"
					opp_name = victim.name

				if victim.lifes > 0:
					messagebox.showinfo(title, f"{player.name} nimmt {opp_name} ein Leben!\n{victim.name} hat noch {victim.lifes} Leben.")
				else:
					messagebox.showinfo("Eliminiert!", f"{player.name} hat {opp_name} eliminiert!")
					win_msg = self._check_and_handle_win_condition()

			player.sb.update_score(player.lifes)

		return None