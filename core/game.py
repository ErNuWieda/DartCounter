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

CRICKET_TARGET_VALUES = {
    "20": 20, "19": 19, "18": 18, "17": 17, "16": 16, "15": 15, "Bull": 25
}
CRICKET_SEGMENTS_AS_STR = [str(s) for s in range(15, 21)] # "15" bis "20"

ATC_TARGET_VALUES = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, "11": 11, "12": 12, "13": 13, "14": 14, "15": 15, "16": 16, "17": 17, "18": 18, "19": 19, "20": 20, "Bull": 25}
ATC_SEGMENTS_AS_STR = [str(s) for s in range(1, 21)] # "1" bis "20"

class Game:
    """
    Verwaltet den Zustand und die Logik eines Dartspiels.
    Dies beinhaltet Spieler, Runden, Punkte und spielmodusspezifische Regeln.
    """
    def __init__(self, root, game, player_names):
        """
        Initialisiert eine neue Spielinstanz.

        Args:
            root: Das Tkinter-Hauptfenster.
            game (tuple): Ein Tupel mit Spielinformationen (Spielname, Opt-In, Opt-Out, Opt-Atc).
            player_names (list): Eine Liste der Namen der teilnehmenden Spieler.
        """
        self.root = root
        self.name, self.opt_in, self.opt_out, self.opt_atc = game
        self.current = 0
        self.round = 1
        self.players = [Player(root, name, self) for name in player_names]
        self.db = None # DartBoard-Instanz, wird extern nach Initialisierung gesetzt.
        self.end = False
        self.shanghai_finish = False

    def __del__(self):
        """
        Bereinigt Ressourcen, wenn die Spielinstanz gelöscht wird.
        Entfernt die Scoreboards der Spieler und zeigt das Hauptfenster wieder an.
        """
        for player in self.players:
            player.__del__()
            self.root.deiconify()
    
    def leave(self, player_id):
        """
        Entfernt einen Spieler aus dem laufenden Spiel.

        Args:
            player_id (int): Die ID des Spielers, der entfernt werden soll.
                             Die ID ist 1-basiert.
        """
        if player_id > len(self.players):
            player_id = len(self.players)
        if self.players: # Sicherstellen, dass die Liste nicht leer ist
            self.players.pop(player_id-1)
        return
        
    def current_player(self):
        """
        Gibt den Spieler zurück, der aktuell am Zug ist.

        Returns:
            Player: Die Instanz des aktuellen Spielers.
        """
        if self.current >  len(self.players):
            self.current = len(self.players)-1
        return self.players[self.current]

    def next_player(self):
        """
        Wechselt zum nächsten Spieler in der Runde oder startet eine neue Runde.
        Zeigt eine Benachrichtigung an, welcher Spieler am Zug ist,
        bereinigt das Dartboard und setzt den Fokus auf das Scorefenster des neuen Spielers.
        """
        self.current = (self.current + 1) % len(self.players)
        if self.current == 0:
            self.round += 1
        if len(self.players) > 1:
            msg = f"{self.players[self.current].name} ist am Zug."
            messagebox.showinfo("Spielerwechsel", msg)       
        if self.db:
            self.db.clear_dart_images_from_canvas()
        self.players[self.current].sb.score_window.focus_force()
    def get_score(self, ring, segment):
        """
        Berechnet den Punktwert eines Wurfs basierend auf Ring und Segment.
        Diese Methode wird primär für x01-Spiele verwendet.

        Args:
            ring (str): Der getroffene Ring ("Single", "Double", "Triple", "Bull", "Bullseye", "Miss").
            segment (int/str): Das getroffene Segment (Zahlenwert oder "Bull").

        Returns:
            int: Der Punktwert des Wurfs.
        """
        match ring:
            case "Bullseye":
                return 50
            case "Bull":
                return 25
            case "Double":
                return segment * 2
            case "Triple":
                return segment * 3
            case "Single":
                return segment
            case _:  # Default case for "Miss" or any other unexpected ring type
                return 0

    def _get_cricket_target_and_marks(self, ring, segment):
        """
        Ermittelt das Cricket-Ziel und die Anzahl der erzielten Marks für einen Wurf.

        Args:
            ring (str): Der getroffene Ring.
            segment (int/str): Das getroffene Segment.

        Returns:
            tuple: (target_hit, marks_scored) - Das getroffene Cricket-Ziel (str)
                   oder None und die Anzahl der Marks (int).
        """
        if ring == "Miss":
            return None, 0

        # Bullseye und Bull als "Bull" Target behandeln
        if ring == "Bullseye": # Zählt als 2 Marks auf Bull
            return "Bull", 2
        if ring == "Bull": # Zählt als 1 Mark auf Bull
            return "Bull", 1

        segment_str = str(segment)
        if segment_str in CRICKET_SEGMENTS_AS_STR:
            marks = 0
            if ring == "Single":
                marks = 1
            elif ring == "Double":
                marks = 2
            elif ring == "Triple":
                marks = 3
            return segment_str, marks
        
        return None, 0 # Kein Cricket-relevantes Segment getroffen


    def _handle_cricket_throw(self, player, ring, segment):
        """
        Verarbeitet einen Wurf im Cricket- oder Cut Throat Cricket-Modus.
        Aktualisiert die Treffer des Spielers, berechnet Punkte und prüft auf Gewinnbedingungen.

        Args:
            player (Player): Der Spieler, der den Wurf ausgeführt hat.
            ring (str): Der getroffene Ring.
            segment (int/str): Das getroffene Segment.

        Returns:
            str or None: Eine Nachricht über den Spielausgang oder den Wurf,
                         oder None, wenn das Spiel weitergeht.
        """
        target_hit, marks_scored = self._get_cricket_target_and_marks(ring, segment)
        player.throws.append((ring, segment))
        if not target_hit or marks_scored == 0:
            player.sb.update_score(player.score) # Scoreboard aktualisieren (für Wurfanzeige)
            if len(player.throws) == 3:
                player.reset_turn()
                self.next_player()
            return f"{player.name} verfehlt oder trifft kein Cricket-Feld."

        # --- Treffer auf Cricket-Ziel verarbeiten ---
        current_marks_on_target = player.cricket_hits.get(target_hit, 0)
        points_for_this_throw = 0
        for _ in range(marks_scored):
            if player.cricket_hits[target_hit] < 3:
                player.cricket_hits[target_hit] += 1
            else: # Ziel ist bereits vom Spieler geschlossen
                # Prüfen, ob das Ziel für Punktgewinn offen ist (nicht alle Gegner haben es geschlossen)
                can_score_points = False
                for opp in self.players:
                    if opp != player and opp.cricket_hits.get(target_hit, 0) < 3:
                        can_score_points = True
                        break
                if can_score_points:
                    points_for_this_throw += CRICKET_TARGET_VALUES[target_hit]

        if points_for_this_throw > 0:
            if self.name == "Cricket":
                player.update_score_value(points_for_this_throw, subtract=False)
            else:
                for opp in self.players:
                    if opp != player and opp.cricket_hits.get(target_hit, 0) < 3:
                        opp.update_score_value(points_for_this_throw, subtract=False)

        player.sb.update_cricket_display(player.cricket_hits, player.score) # Cricket-Marks und Score aktualisieren

        # --- Gewinnbedingung prüfen ---
        all_targets_closed_by_player = True
        for target in player.cricket_targets:
            if player.cricket_hits.get(target, 0) < 3:
                all_targets_closed_by_player = False
                break
        
        if all_targets_closed_by_player:
            player_has_best_score = True
            for opp in self.players:
                if opp != player:
                    if self.name == "Cricket" and opp.score > player.score:
                        player_has_best_score = False
                        break
                    elif opp.score < player.score:
                        player_has_best_score = False
                        break

            if player_has_best_score:
                self.end = True
                total_darts = (self.round - 1) * 3 + len(player.throws)
                return f"🏆 {player.name} gewinnt {self.name} in Runde {self.round} mit {total_darts} Darts!"

        # --- Zug beenden / Nächster Spieler ---
        if len(player.throws) == 3:
            player.reset_turn()
            self.next_player()
            return  
        
    def _handle_atc_throw(self, player, ring, segment):
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
        if player.atc_next_target not in (str(segment), ring) or (ring not in ("Bull", "Bullseye", self.opt_atc)): 
        # Wurf war ein Miss oder traf nicht das Ziel-Feld
            player.sb.update_score(player.score)
            if player.atc_next_target in ("Bull", "Bullseye"):
                opt_atc = ""
            else:
                opt_atc = self.opt_atc
            msg = f"{player.name} muss {opt_atc} {player.atc_next_target} treffen!\nNoch {3 - len(player.throws)} verbleibende Würfe."
            messagebox.showerror("Ungültiger Wurf", msg)
            if len(player.throws) == 3:
                player.reset_turn()
                self.next_player()            
            return 

        # --- Treffer auf AtC-Ziel verarbeiten ---
        if player.atc_next_target not in ("Bull", "Bullseye"):
            player.atc_hit[str(segment)] = 1
        else:
            player.atc_hit["Bull"] = 1
        
        # Nächstes Ziel bestimmen oder Gewinnbedingung prüfen
        all_targets_closed = True
        for target in player.atc_targets:
            hit = player.atc_hit.get(target, 0)
            if hit == 0:
                all_targets_closed = False
                player.atc_next_target = target
                break
        
        if player.atc_next_target == "Bull" and self.opt_atc != "Single":
            player.atc_next_target = "Bullseye"
        
        player.sb.update_atc_display(player.atc_hit, player.score) # ATC-Anzeige aktualisieren

        # --- Gewinnbedingung prüfen ---
        if all_targets_closed:
            self.end = True
            total_darts = (self.round - 1) * 3 + len(player.throws)
            return f"🏆 {player.name} gewinnt Around the Clock in Runde {self.round} mit {total_darts} Darts!"

        # --- Zug beenden / Nächster Spieler ---
        if len(player.throws) == 3:
            player.reset_turn()
            self.next_player()
               

    def throw(self, ring, segment):
        """
        Verarbeitet einen Wurf eines Spielers.
        Dies ist der Haupteinstiegspunkt für die Wurflogik. Die Methode delegiert
        an spielmodusspezifische Handler (_handle_cricket_throw, _handle_atc_throw)
        oder verarbeitet x01-Logik direkt.

        Args:
            ring (str): Der getroffene Ring ("Single", "Double", "Triple", "Bull", "Bullseye", "Miss").
            segment (int/str): Das getroffene Segment (Zahlenwert oder "Bull").

        Returns:
            str or None: Eine Nachricht über den Spielausgang (Gewinn, Bust, etc.)
                         oder None, wenn das Spiel normal weitergeht.
        """
        player = self.current_player()

        if self.name in ("Cricket", "Cut Throat"):
            return self._handle_cricket_throw(player, ring, segment)
        elif self.name == "Around the Clock":
            return self._handle_atc_throw(player, ring, segment)
            
        # --- x01 Logik ---
        score = self.get_score(ring, segment)

        if ring == "Miss":
            player.throws.append((ring, 0))
            messagebox.showerror("Daneben", f"{player.name} verfehlt!")
            player.update_score_value(score, subtract=True) # score ist hier 0 für Miss
            if len(player.throws) == 3:
                player.reset_turn()
                self.next_player()
            return 

        is_x01_game = self.name in ["301", "501", "701"]

        if is_x01_game and not player.has_doubled_in:
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
                    self.next_player()
                messagebox.showerror("Ungültiger Wurf", msg+f"\nNoch {3 - len(player.throws)} verbleibende Würfe.")
                return 


        new_score = player.score - score
        bust = False
        if new_score < 0:
            bust = True # Direkt überworfen
        elif is_x01_game:
            if self.opt_out == "Double":
                if new_score == 1: bust = True
                elif new_score == 0 and not (ring == "Double" or ring == "Bullseye"): bust = True
            elif self.opt_out == "Masters":
                if new_score == 1: bust = True
                elif new_score == 0 and ring not in ("Double", "Triple", "Bullseye"): bust = True
        
        if bust:
            player.throws.append((ring, 0))
            messagebox.showerror("Bust", f"{player.name} hat überworfen! Nächster Spieler.")
            player.reset_turn() # Würfe zurücksetzen, Score bleibt wie vor dem Bust
            self.next_player()
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
            self.end = True
            total_darts = (self.round - 1) * 3 + len(player.throws)
            return f"🏆 {player.name} gewinnt in Runde {self.round} mit {total_darts} Darts!"
        
        if len(player.throws) == 3:
            player.reset_turn()
            self.next_player()
            return None 

        return None
