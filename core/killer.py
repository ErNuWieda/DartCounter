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
		was_killer_at_time_of_throw = player.can_kill
		is_killer_making_throw = (player.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or \
								 (str(segment) == player.life_segment and player.life_segment != "Bull" and ring in ("Bull", "Bullseye", "Double"))

		if not was_killer_at_time_of_throw and is_killer_making_throw:
			was_killer_at_time_of_throw = True

		if was_killer_at_time_of_throw:
			# Finde das potenzielle Opfer, auch wenn es bereits eliminiert wurde.
			victim = None
			for p in self.players:
				is_victim_life_segment_hit = (p.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or \
											 (str(segment) == p.life_segment and p.life_segment != "Bull")
				
				if is_victim_life_segment_hit and ring in ("Bull", "Bullseye", "Double"):
					victim = p
					break
			
			if victim and victim.lifes < self.game.lifes:
				victim.lifes += 1
				if self.game.end: # Spielende-Status zurücksetzen, falls nötig
					self.game.end = False
				victim.sb.update_score(victim.lifes)
				messagebox.showinfo("Rückgängig", f"Leben für {victim.name} wiederhergestellt.")

		# --- Schritt 2: Killer-Status zurücksetzen, falls nötig ---
		if player.can_kill and is_killer_making_throw:
			# Prüfen, ob noch andere "Killer-Würfe" in der Runde vorhanden sind.
			other_killer_throws_exist = any((player.life_segment == "Bull" and r in ("Bull", "Bullseye")) or (str(s) == player.life_segment and player.life_segment != "Bull" and r in ("Bull", "Bullseye", "Double")) for r, s in player.throws)
			
			if not other_killer_throws_exist:
				player.can_kill = False
				messagebox.showinfo("Rückgängig", f"{player.name} ist kein Killer mehr.")

		# --- Schritt 3: Scoreboard des aktuellen Spielers aktualisieren ---
		player.sb.update_score(player.lifes)

	def _handle_throw(self, player, ring, segment, players):
		player.throws.append((ring, segment))

		# --- Phase 1: Spieler braucht ein Lebensfeld ---
		if not player.life_segment:
			if ring == "Miss":
				msg = f"{player.name}, du musst ein Segment treffen, um dein Lebensfeld festzulegen."
				if len(player.throws) == 3:
					messagebox.showerror("Fehlwurf", msg + "\nLetzter Dart dieser Aufnahme. Bitte 'Zug beenden' klicken.")
				else:
					messagebox.showwarning("Fehlwurf", msg + f"\nNoch {3 - len(player.throws)} Darts.")
				player.sb.update_score(player.lifes) # Wurfhistorie aktualisieren
				return None

			determined_segment_for_life = ""
			# segment ist der numerische Wert (1-20, 25 für Bull, 50 für Bullseye)
			if ring == "Bullseye" or (ring == "Bull" and segment == 25):
				determined_segment_for_life = "Bull"
			elif isinstance(segment, int) and 1 <= segment <= 20:
				determined_segment_for_life = str(segment)
			else:
				# Ungültiger Treffer für Lebensfeldbestimmung
				msg = f"{player.name}, ungültiger Trefferbereich ({ring}, {segment}) für Lebensfeldbestimmung."
				if len(player.throws) == 3:
					messagebox.showerror("Fehler", msg + "\nLetzter Dart dieser Aufnahme. Bitte 'Zug beenden' klicken.")
				else:
					messagebox.showwarning("Fehler", msg + f"\nNoch {3 - len(player.throws)} Darts.")
				player.sb.update_score(player.lifes)
				return None

			# Prüfen, ob dieses Segment bereits von einem anderen aktiven Spieler belegt ist
			is_taken = False
			for p_other in self.players:
				if p_other != player and p_other.lifes > 0 and p_other.life_segment == determined_segment_for_life:
					is_taken = True
					break
			
			if is_taken:
				msg = f"Das Segment '{determined_segment_for_life}' ist bereits vergeben. Bitte ein anderes treffen."
				if len(player.throws) == 3:
					messagebox.showerror("Segment vergeben", msg + "\nLetzter Dart dieser Aufnahme. Bitte 'Zug beenden' klicken.")
				else:
					messagebox.showwarning("Segment vergeben", msg + f"\nNoch {3 - len(player.throws)} Darts.")
				player.sb.update_score(player.lifes)
				return None
			
			player.life_segment = determined_segment_for_life
			messagebox.showinfo("Lebensfeld festgelegt!", f"{player.name} hat Lebensfeld: Double {player.life_segment}")
			player.sb.update_score(player.lifes) # Scoreboard mit neuem Lebensfeld aktualisieren
			player.reset_turn() # Zug endet, nachdem das Lebensfeld erfolgreich gesetzt wurde
			self.game.next_player()
			return

		# --- Phase 2: Spieler ist noch kein Killer ---
		elif not player.can_kill:
			# ... (Logik aus vorheriger Antwort kann hier eingefügt werden) ...
			# Beispielhafte Kurzform:
			hit_own_life_segment = (player.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or \
			                       (str(segment) == player.life_segment and player.life_segment != "Bull" )

			if hit_own_life_segment and ring in ("Bull", "Bullseye", "Double"):
				player.can_kill = True
				messagebox.showinfo("Killer Status!", f"{player.name} ist jetzt ein KILLER!")
			else:
				messagebox.showinfo("Daneben", f"{player.name} muss das eigene Lebensfeld treffen um Killer zu werden.")
			player.sb.update_score(player.lifes)

		# --- Phase 3: Spieler ist ein Killer ---
		elif player.can_kill:
			# ... (Logik aus vorheriger Antwort kann hier eingefügt werden) ...
			# Beispielhafte Kurzform für Treffer auf Gegner:
			opponent_hit = None
			for opp in self._get_active_players():
				is_opp_life_segment_hit = (opp.life_segment == "Bull" and ring in ("Bull", "Bullseye")) or (str(segment) == opp.life_segment and opp.life_segment != "Bull")
				if is_opp_life_segment_hit and ring in ("Bull", "Bullseye", "Double"):
					opponent_hit = opp
					break

			if opponent_hit:
				opponent_hit.lifes -= 1
				if opponent_hit == player:
					title = "Eigentor"
					opp_name = "sich selbst"
				else:
					title = "Leben genommen!"
					opp_name = opponent_hit.name
					
				messagebox.showinfo(title, f"{player.name} nimmt {opp_name} ein Leben!\n{opponent_hit.name} hat noch {opponent_hit.lifes} Leben.")
				opponent_hit.sb.update_score(opponent_hit.lifes)
				if opponent_hit.lifes == 0:
					messagebox.showinfo("Eliminiert!", f"{player.name} hat {opp_name} eliminiert!")
					win_msg = self._check_and_handle_win_condition()
					if win_msg: return win_msg
			player.sb.update_score(player.lifes)
			if player.lifes == 0: # Falls Selbsteliminierung
				win_msg = self._check_and_handle_win_condition()
				if win_msg: return win_msg

		# --- Zugende prüfen (gilt für alle Phasen nach der Lebensfeld-Vergabe, wenn kein return vorher) ---
		if len(player.throws) == 3:
			# Turn ends, user clicks "Zug beenden"
			pass # Let it fall through to return None
		return None # Spiel geht weiter, oder Wurf innerhalb der Runde
