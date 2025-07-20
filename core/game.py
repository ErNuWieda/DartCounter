"""
Dieses Modul definiert die Hauptlogik für verschiedene Dartspiele.
Es enthält die Game-Klasse, die den Spielablauf und die Spieler verwaltet.
"""
import tkinter as tk 
from tkinter import ttk, messagebox
from .player import Player
from .scoreboard import ScoreBoard
 

class Game:
    """
    Die zentrale Steuerungseinheit für eine Dartspiel-Sitzung.

    Diese Klasse agiert als "Controller" im Model-View-Controller-Muster. Sie
    initialisiert und verwaltet den Spielzustand (Spieler, Runden, Punkte),
    delegiert die spezifische Spiellogik an untergeordnete Handler-Klassen
    (z.B. X01, Cricket) und interagiert mit den UI-Komponenten (DartBoard,
    ScoreBoard) und Managern (Sound, Highscore).

    Attributes:
        root (tk.Tk): Das Hauptfenster der Tkinter-Anwendung.
        sound_manager (SoundManager): Instanz zur Verwaltung von Soundeffekten.
        highscore_manager (HighscoreManager): Instanz zur Verwaltung von Highscores.
        name (str): Der Name des ausgewählten Spiels (z.B. "301", "Cricket").
        players (list[Player]): Eine Liste der am Spiel teilnehmenden Spieler-Objekte.
        current (int): Der Index des aktuellen Spielers in der `players`-Liste.
        round (int): Die aktuelle Spielrunde.
        end (bool): Ein Flag, das anzeigt, ob das Spiel beendet ist.
        game (object): Eine Instanz der spezifischen Spiellogik-Klasse (z.B. X01).
        db (DartBoard): Die Instanz des klickbaren Dartboards.
    """
    def __init__(self, root, game, player_names, sound_manager=None, highscore_manager=None):
        """
        Initialisiert eine neue Spielinstanz.

        Args:
            root (tk.Tk): Das Tkinter-Hauptfenster.
            game (tuple): Ein Tupel mit allen Spieloptionen aus dem GameManager.
            player_names (list): Eine Liste der Namen der teilnehmenden Spieler.
            sound_manager (SoundManager, optional): Instanz zur Soundwiedergabe.
            highscore_manager (HighscoreManager, optional): Instanz zur Verwaltung von Highscores.
        """
        self.root = root
        self.sound_manager = sound_manager
        self.highscore_manager = highscore_manager
        self.name = game[0]
        self.opt_in = game[1]
        self.opt_out = game[2]
        self.opt_atc = game[3]
        self.count_to = int(game[4])
        self.lifes = int(game[5])
        self.rounds = int(game[6])
        self.current = 0
        self.round = 1
        self.shanghai_finish = False
        self.end = False
        self.game = self.get_game_logic()
        self.targets = self.game.get_targets()
        
        # Spieler-Instanzen erstellen (ohne UI-Abhängigkeit)
        self.players = [Player(name, self) for name in player_names]
        # Scoreboards für jeden Spieler erstellen und zuweisen
        for player in self.players:
            player.sb = ScoreBoard(self.root, player, self)
        
        # Spezifische Initialisierung für Killer nach Erstellung der Spieler
        if self.name == "Killer" and hasattr(self.game, 'set_players'):
            self.game.set_players(self.players)
            
        self.db = None # DartBoard-Instanz, wird extern nach Initialisierung gesetzt.
        
    def __del__(self):
        """
        Bereinigt Ressourcen, wenn die Spielinstanz gelöscht wird.

        Diese Methode wird aufgerufen, wenn ein Spiel endet (durch Sieg, Abbruch
        oder Laden eines neuen Spiels). Sie schließt alle zugehörigen Fenster
        (Scoreboards, Dartboard) und zeigt das Hauptfenster wieder an.
        """
        for player in self.players:
            player.__del__()
        
        if self.db:
            self.db.root.destroy()
            self.db = None
        self.root.deiconify()
    
    def leave(self, player_id):
        """
        Entfernt einen Spieler aus dem laufenden Spiel.

        Die Methode behandelt verschiedene Szenarien, z.B. wenn der aktuell
        spielende Spieler entfernt wird oder wenn der letzte Spieler das Spiel verlässt.

        Args:
            player_id (int): Die eindeutige ID des Spielers, der entfernt werden soll.
        """
        player_to_remove = None
        player_to_remove_index = -1

        # Finde den Spieler und seinen Index basierend auf der ID
        for i, p in enumerate(self.players):
            if p.id == player_id:
                player_to_remove = p
                player_to_remove_index = i
                break

        if not player_to_remove:
            return  # Spieler nicht gefunden

        was_current_player = (player_to_remove_index == self.current)

        # Passe den 'current' Index an, BEVOR der Spieler entfernt wird.
        if player_to_remove_index < self.current:
            self.current -= 1

        # Entferne den Spieler aus der Liste
        self.players.pop(player_to_remove_index)

        # --- Spielzustand nach dem Entfernen prüfen ---

        # Fall 1: Keine Spieler mehr übrig
        if not self.players:
            messagebox.showinfo("Spielende", "Alle Spieler haben das Spiel verlassen.")
            self.end = True
            self.__del__()  # Beendet das Spiel und schließt alle Fenster
            return

        # Fall 2: Der Index des aktuellen Spielers ist jetzt außerhalb der Liste
        # (passiert, wenn der letzte Spieler in der Liste entfernt wird).
        if self.current >= len(self.players):
            self.current = 0
            # Wenn der letzte Spieler einer Runde entfernt wurde, beginnt eine neue Runde.
            if was_current_player:
                self.round += 1

        # Fall 3: Der aktuelle Spieler hat das Spiel verlassen.
        # Der nächste Spieler ist nun automatisch am Zug.
        if was_current_player:
            self.announce_current_player_turn()

    def undo(self):
        """
        Macht den letzten Wurf des aktuellen Spielers rückgängig.

        Holt den letzten Wurf aus der Wurfhistorie des Spielers, delegiert die
        Logik zum Rückgängigmachen an die spezifische Spiel-Handler-Klasse
        (z.B. `x01._handle_throw_undo`) und entfernt die Dart-Grafik vom Board.
        """
        if self.end:
            self.end = False
        player = self.current_player()
        if player and player.throws:
            popped_throw = player.throws.pop()
            self.game._handle_throw_undo(player, popped_throw[0], popped_throw[1], self.players)
        self.db.clear_last_dart_image_from_canvas()
        return 
            
    def current_player(self):
        """
        Gibt den Spieler zurück, der aktuell am Zug ist.

        Returns:
            Player or None: Die Instanz des aktuellen Spielers oder None, wenn keine Spieler vorhanden sind.
        """
        if not self.players:
            return None
        # self.current sollte durch Initialisierung und next_player immer im gültigen Bereich sein
        return self.players[self.current]

    def announce_current_player_turn(self):
        """
        Kündigt den Zug des aktuellen Spielers über UI-Elemente an.

        Zeigt eine `MessageBox` an, um den Spielerwechsel zu signalisieren.
        Für spezielle Spielmodi wie "Killer" werden zusätzliche Anweisungen angezeigt.
        Bringt das Scoreboard des aktuellen Spielers in den Vordergrund.
        """
        player = self.current_player()
        if not player: # Sollte nicht passieren, wenn Spieler vorhanden sind
            return

        round_info = f"Runde {self.round}."
        player_info = f"{player.name} ist am Zug."
        
        # Spezielle Nachricht für den allerersten Wurf des Spiels
        if self.current == 0 and self.round == 1 and not player.throws: # Check for no throws as well
            messagebox.showinfo("Spielstart", f"{player.name} beginnt!")
        else:
            messagebox.showinfo("Spielerwechsel", f"{round_info}\n{player_info}")
        
        # Spezifische Nachricht für Killer-Modus, wenn Lebensfeld bestimmt werden muss
        if self.name == "Killer":
            if not player.life_segment:
                messagebox.showinfo("Lebensfeld ermitteln",
                                    f"{player.name}, du musst nun dein Lebensfeld bestimmen.\n"
                                    f"Wirf mit deiner NICHT-dominanten Hand.\n"
                                    f"Das Double des getroffenen Segments wird dein Lebensfeld.\n"
                                    f"Ein Treffer auf Bull/Bullseye zählt als Lebensfeld 'Bull'.")
            elif player.life_segment and not player.can_kill: # Only show if life_segment is set but not yet a killer
                segment_str = "Bull" if player.life_segment == "Bull" else f"Double {player.life_segment}"
                messagebox.showinfo("Zum Killer werden",
                                    f"{player.name}, jetzt musst du dein Lebensfeld ({segment_str}) treffen um Killer-Status zu erlangen.\n"
                                    f"Erst dann kannst du andere Spieler eliminieren.\n"
                                    f"VORSICHT!\n"
                                    f"Triffst du als Killer dein eigenes Lebensfeld, verlierst du selbst ein Leben!")
        
        if self.db:
            self.db.clear_dart_images_from_canvas()
        
        # Sicherstellen, dass Scoreboard existiert und fokussiert werden kann
        if hasattr(player, 'sb') and player.sb and hasattr(player.sb, 'score_window') and player.sb.score_window.winfo_exists():
            player.sb.score_window.lift()
            player.sb.score_window.focus_force()

    def next_player(self):
        """
        Wechselt zum nächsten Spieler in der Runde oder startet eine neue Runde.

        Diese Methode wird typischerweise aufgerufen, nachdem ein Spieler seine
        drei Darts geworfen hat (z.B. durch Klick auf den "Weiter"-Button).
        Sie aktualisiert den `current`-Index und die `round`-Nummer.
        """
        if not self.players: # Keine Spieler mehr im Spiel
            return

        if self.end == True:
            self.__del__()
            return


        current_p = self.current_player()
        if current_p:
            current_p.reset_turn() # Reset throws for the player whose turn just ended

        self.current = (self.current + 1) % len(self.players)
        if self.current == 0: # Moved to next round
            self.round += 1
        
        self.announce_current_player_turn() # Announce the new current player

    def get_game_logic(self):
        """
        Eine Factory-Methode, die die passende Spiellogik-Klasse instanziiert.

        Basierend auf dem `self.name` des Spiels wird die entsprechende Klasse
        dynamisch importiert und eine Instanz davon zurückgegeben. Dies ermöglicht
        eine saubere Trennung der Logik für jeden Spielmodus.

        Returns:
            object: Eine Instanz der jeweiligen Spiellogik-Klasse (z.B. X01, Cricket).
        """
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
            case "Elimination":
                from . import elimination
                from .elimination import Elimination
                return Elimination(self)
            case "Micky Mouse":
                from . import micky
                from .micky import Micky
                return Micky(self)
            case "Killer":
                from . import killer
                from .killer import Killer
                return Killer(self) # Spieler werden später via set_players gesetzt
            case "Shanghai":
                from . import shanghai
                from .shanghai import Shanghai
                return Shanghai(self)


    def get_score(self, ring, segment):
        """
        Berechnet den Punktwert eines Wurfs basierend auf Ring und Segment.

        Args:
            ring (str): Der getroffene Ring ("Single", "Double", "Triple", "Bull", "Bullseye", "Miss").
            segment (int): Der Zahlenwert des getroffenen Segments.

        Returns:
            int: Der berechnete Punktwert des Wurfs.
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

        Dies ist der Haupteinstiegspunkt von der UI (DartBoard) in die Spiellogik.
        Die Methode prüft, ob der Spieler noch Würfe übrig hat, und delegiert dann
        die eigentliche Verarbeitung an die `_handle_throw`-Methode der
        spezifischen Spiellogik-Instanz. Löst auch Soundeffekte aus.

        Args:
            ring (str): Der getroffene Ring ("Single", "Double", "Triple", "Bull", "Bullseye", "Miss").
            segment (int): Das getroffene Segment (Zahlenwert).

        Returns:
            str or None: Eine Nachricht über den Spielausgang (z.B. Gewinnmeldung)
                         oder None, wenn das Spiel normal weitergeht.
        """
        player = self.current_player()
        if len(player.throws) < 3:
            msg = self.game._handle_throw(player, ring, segment, self.players)
            
            # Soundeffekte abspielen
            if self.sound_manager:
                if msg and "🏆" in msg: # Gewinn-Sound
                    self.sound_manager.play_win()
                elif ring != "Miss": # Treffer-Sound für alles außer Miss
                    self.sound_manager.play_hit()
            
            return msg
        else:
            messagebox.showinfo("Zuviel Würfe", "Bitte 'Weiter' klicken!")
            return self.db.clear_last_dart_image_from_canvas()
