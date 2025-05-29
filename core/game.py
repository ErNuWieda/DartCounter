"""
Dieses Modul definiert die Hauptlogik für verschiedene Dartspiele.
Es enthält die Game-Klasse, die den Spielablauf und die Spieler verwaltet.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from . import player 
from .player import Player
from . import scoreboard
from .scoreboard import ScoreBoard
 

class Game:
    """
    Verwaltet den Zustand und die Logik eines Dartspiels.
    Dies beinhaltet Spieler, Runden und Punkte.
    """
    def __init__(self, root, game, player_names):
        """
        Initialisiert eine neue Spielinstanz.

        Args:
            root: Das Tkinter-Hauptfenster.
            game (tuple): Ein Tupel mit Spielinformationen (Spielname, Opt-In, Opt-Out, Opt-Atc, Killerleben).
            player_names (list): Eine Liste der Namen der teilnehmenden Spieler.
        """
        self.root = root
        self.name = game[0]
        self.opt_in = game[1]
        self.opt_out = game[2]
        self.opt_atc = game[3]
        self.lifes = int(game[4])
        self.current = 0
        self.round = 1
        self.shanghai_finish = False
        self.end = False
        self.game = self.get_game_logic()
        self.targets = self.game.get_targets()
        self.players = [Player(root, name, self) for name in player_names]
        
        # Spezifische Initialisierung für Killer nach Erstellung der Spieler
        if self.name == "Killer" and hasattr(self.game, 'set_players'):
            self.game.set_players(self.players)
            
        self.db = None # DartBoard-Instanz, wird extern nach Initialisierung gesetzt.
        
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
            player_to_remove_index = player_id - 1
            if 0 <= player_to_remove_index < len(self.players):
                # Wichtig: self.current anpassen, BEVOR der Spieler entfernt wird,
                # falls der entfernte Spieler vor dem aktuellen Spieler in der Liste stand.
                if player_to_remove_index < self.current:
                    self.current -= 1
                
                self.players.pop(player_to_remove_index)

                if not self.players: # Keine Spieler mehr übrig
                    messagebox.showinfo("Spielende", "Alle Spieler haben das Spiel verlassen.")
                    if self.db and self.db.root:
                        try:
                            self.db.root.destroy()
                        except tk.TclError: # Fenster könnte bereits zerstört sein
                            pass
                    self.root.deiconify()
                    self.end = True
                    return

                # Sicherstellen, dass self.current gültig bleibt
                if self.current >= len(self.players):
                    self.current = 0 # Zum ersten Spieler zurück, falls der letzte Spieler entfernt wurde
        
        
    def current_player(self):
        """
        Gibt den Spieler zurück, der aktuell am Zug ist.

        Returns:
            Player: Die Instanz des aktuellen Spielers oder None, wenn keine Spieler vorhanden sind.
        """
        if not self.players:
            return None
        # self.current sollte durch Initialisierung und next_player immer im gültigen Bereich sein
        return self.players[self.current]

    def announce_current_player_turn(self):
        """
        Kündigt den aktuellen Spieler an, bereitet UI vor und zeigt ggf. Killer-spezifische Nachrichten.
        """
        for p in self.players:
            p.is_active = False

        player = self.current_player()
        if not player: # Sollte nicht passieren, wenn Spieler vorhanden sind
            return

        round_info = f"Runde {self.round}."
        player_info = f"{player.name} ist am Zug."
        player.is_active = True
        full_message = f"{round_info}\n{player_info}"
        # Spezielle Nachricht für den allerersten Wurf des Spiels
        if self.current == 0 and self.round == 1 and not player.throws:
            full_message = f"Das Spiel beginnt!\n{full_message}"
        
        messagebox.showinfo("Nächster Zug", full_message)
        
        # Spezifische Nachricht für Killer-Modus, wenn Lebensfeld bestimmt werden muss
        if self.name == "Killer" and not player.life_segment:
            messagebox.showinfo("Lebensfeld ermitteln",
                                f"{player.name}, du musst nun dein Lebensfeld bestimmen.\n"
                                f"Wirf mit deiner NICHT-dominanten Hand.\n"
                                f"Das Double des getroffenen Segments wird dein Lebensfeld.\n"
                                f"Ein Treffer auf Bull/Bullseye zählt als Lebensfeld 'Bull'.")
        elif self.name == "Killer" and not player.can_kill:
            messagebox.showinfo("Zum Killer werden",
                                f"{player.name}, jetzt musst du dein Lebensfeld treffen um Killer-Status zu erlangen.\n"
                                f"Erst dann kannst du andere Spieler eliminieren.\n"
                                f"VORSICHT!\n"
                                f"Triffst du als Killer dein eigenes Lebensfeld, verlierst du selbst ein Leben!")
        
        if self.db:
            self.db.clear_dart_images_from_canvas()
        
        # Sicherstellen, dass Scoreboard existiert und fokussiert werden kann
        if hasattr(player, 'sb') and player.sb and hasattr(player.sb, 'score_window') and player.sb.score_window.winfo_exists():
            player.sb.score_window.focus_force()

    def next_player(self):
        """
        Wechselt zum nächsten Spieler in der Runde oder startet eine neue Runde.
        """
        if not self.players: # Keine Spieler mehr im Spiel
            return

        self.current = (self.current + 1) % len(self.players)
        if self.current == 0:
            self.round += 1
        
        self.announce_current_player_turn()

    def get_game_logic(self):
        match self.name:
            case "301" | "501" | "701":
                from . import x01
                from .x01 import X01
                return X01(self)
            case "Cricket" | "Cut Throat" | "Tactics":
                from . import cricket
                from .cricket import Cricket
                return Cricket(self)
            case "Around the Clock":
                from . import atc
                from .atc import AtC
                return AtC(self)
            case "Micky Mouse":
                from . import micky
                from .micky import Micky
                return Micky(self)
            case "Killer":
                from . import killer
                from .killer import Killer
                return Killer(self) # Spieler werden später via set_players gesetzt

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

    def throw(self, ring, segment):
        """
        Verarbeitet einen Wurf eines Spielers.
        Dies ist der Haupteinstiegspunkt für die Wurflogik. Die Methode delegiert den Wurf an den Handler (_handle_throw) des entsprechenden Spielobjekts (z.B. X01, Cricket, etc.)

        Args:
            player: der aktuelle Spieler.
            ring (str): Der getroffene Ring ("Single", "Double", "Triple", "Bull", "Bullseye", "Miss").
            segment (int/str): Das getroffene Segment (Zahlenwert oder "Bull").

        Returns:
            str or None: Eine Nachricht über den Spielausgang (Gewinn, Bust, etc.)
                         oder None, wenn das Spiel normal weitergeht.
        """
        player = self.current_player()
        return self.game._handle_throw(player, ring, segment, self.players)
