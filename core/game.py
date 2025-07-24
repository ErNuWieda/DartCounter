"""
Dieses Modul definiert die Hauptlogik für verschiedene Dartspiele.
Es enthält die Game-Klasse, die den Spielablauf und die Spieler verwaltet.
"""
import tkinter as tk 
from tkinter import ttk, messagebox
from .player import Player
from .dartboard import DartBoard
from .scoreboard import ScoreBoard
from .x01 import X01
from .cricket import Cricket
from .atc import AtC
from .elimination import Elimination
from .micky import Micky
from .killer import Killer
from .shanghai import Shanghai

# Zentrale Zuordnung von Spielnamen zu den entsprechenden Logik-Klassen.
# Dies ersetzt die dynamischen Imports in der get_game_logic-Methode.
GAME_LOGIC_MAP = {
    "301": X01,
    "501": X01,
    "701": X01,
    "Cricket": Cricket,
    "Cut Throat": Cricket,
    "Tactics": Cricket,
    "Around the Clock": AtC,
    "Elimination": Elimination,
    "Micky Mouse": Micky,
    "Killer": Killer,
    "Shanghai": Shanghai,
}

class Game:
    """
    Die zentrale Steuerungseinheit für eine Dartspiel-Sitzung (Controller).

    Diese Klasse initialisiert und verwaltet den gesamten Spielzustand,
    einschließlich der Spieler, Runden und Spieloptionen. Sie agiert als
    zentraler Controller, der die Interaktionen zwischen den UI-Komponenten
    (DartBoard, ScoreBoard), den Datenmodellen (Player) und den spezialisierten
    Logik-Handlern (z.B. X01, Cricket) koordiniert.

    Verantwortlichkeiten:
    - Initialisierung des Spiels mit den gewählten Optionen und Spielern.
    - Dynamisches Laden der korrekten Spiellogik über eine Factory-Methode.
    - Erstellung und Anordnung der UI-Fenster (Scoreboards).
    - Verwaltung des Spielablaufs (Spielerwechsel, Runden zählen).
    - Entgegennahme von UI-Events (Würfe, Undo, Spieler verlässt Spiel) und
      Delegation an die zuständigen Methoden oder Logik-Handler.
    - Bereinigung aller Ressourcen nach Spielende.
    """
    def __init__(self, root, game_options, player_names, sound_manager=None, highscore_manager=None, player_stats_manager=None):
        """
        Initialisiert eine neue Spielinstanz.

        Args:
            root (tk.Tk): Das Hauptfenster der Anwendung, das als Parent dient.
            game_options (dict): Ein Dictionary mit allen Spieloptionen.
            player_names (list): Eine Liste der Namen der teilnehmenden Spieler.
            sound_manager (SoundManager, optional): Instanz zur Soundwiedergabe.
            highscore_manager (HighscoreManager, optional): Instanz zur Verwaltung von Highscores.
            player_stats_manager (PlayerStatsManager, optional): Instanz zur Verwaltung von Spielerstatistiken.
        """
        self.root = root
        self.sound_manager = sound_manager
        self.highscore_manager = highscore_manager
        self.player_stats_manager = player_stats_manager
        self.name = game_options['name']
        self.opt_in = game_options['opt_in']
        self.opt_out = game_options['opt_out']
        self.opt_atc = game_options['opt_atc']
        self.count_to = int(game_options['count_to'])
        self.lifes = int(game_options['lifes'])
        self.rounds = int(game_options['rounds'])
        self.current = 0
        self.round = 1
        self.shanghai_finish = False
        self.end = False
        self.game = self.get_game_logic()
        self.targets = self.game.get_targets()
        
        # Spieler-Instanzen erstellen (ohne UI-Abhängigkeit)
        self.players = [Player(name, self) for name in player_names]
        
        # Spielspezifischen Zustand für jeden Spieler initialisieren,
        # indem die Logik an die jeweilige Spielklasse delegiert wird.
        for player in self.players:
            self.game.initialize_player_state(player)

        # Spezifische Initialisierung für Killer nach Erstellung der Spieler
        if self.name == "Killer" and hasattr(self.game, 'set_players'):
            self.game.set_players(self.players)
            
        # --- UI-Setup ---
        # Die Game-Klasse ist jetzt selbst für die Erstellung ihrer UI verantwortlich.
        self.db = DartBoard(self)
        self.setup_scoreboards()

    def destroy(self):
        """Zerstört alle UI-Elemente, die zu diesem Spiel gehören, sicher."""
        if self.db and self.db.root:
            try:
                # Zerstört das Dartboard-Fenster
                self.db.root.destroy()
            except tk.TclError:
                # Fängt den Fehler ab, falls das Fenster bereits geschlossen wurde
                pass
        
        for player in self.players:
            if player.sb and player.sb.root:
                try:
                    # Zerstört das Scoreboard-Fenster des Spielers
                    player.sb.root.destroy()
                except tk.TclError:
                    pass
        
        # Setzt die Referenzen zurück, um Memory-Leaks zu vermeiden
        self.db = None

    def setup_scoreboards(self):
        """
        Erstellt und positioniert die Scoreboards für alle Spieler.

        Die Positionierung erfolgt dynamisch relativ zum zentrierten
        Dartboard-Fenster, um eine aufgeräumte und überlappungsfreie
        Anzeige auf verschiedenen Bildschirmgrößen zu gewährleisten.
        """
        if not self.db or not self.db.root.winfo_exists():
            return

        self.db.root.update_idletasks()

        db_x = self.db.root.winfo_x()
        db_y = self.db.root.winfo_y()
        db_width = self.db.root.winfo_width()
        
        scoreboard_width = 340
        # Die Höhe ist jetzt dynamisch und wird für die Positionierung benötigt.
        scoreboard_height = self.game.get_scoreboard_height()
        gap = 10

        # Positionen berechnen (links vom Board, dann rechts vom Board)
        pos_left_x = db_x - scoreboard_width - gap
        pos_right_x = db_x + db_width + gap
        
        pos_top_y = db_y
        pos_bottom_y = db_y + scoreboard_height + gap

        positions = [
            (pos_left_x, pos_top_y),      # Player 1
            (pos_left_x, pos_bottom_y),   # Player 2
            (pos_right_x, pos_top_y),     # Player 3
            (pos_right_x, pos_bottom_y),  # Player 4
        ]

        for i, player in enumerate(self.players):
            if i < len(positions):
                pos_x, pos_y = positions[i]
                player.sb = ScoreBoard(self.root, player, self, pos_x, pos_y, scoreboard_width,scoreboard_height)
    
    def leave(self, player_id):
        """
        Entfernt einen Spieler aus dem laufenden Spiel.
        
        Behandelt verschiedene Szenarien, z.B. wenn der aktuell spielende
        Spieler entfernt wird oder wenn der letzte verbleibende Spieler das
        Spiel verlässt, was zum Spielende führt.

        Args:
            player_id (int): Die eindeutige ID des zu entfernenden Spielers.
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
            messagebox.showinfo("Spielende", "Alle Spieler haben das Spiel verlassen.", parent=self.root)
            self.end = True
            self.destroy()  # Beendet das Spiel und schließt alle Fenster
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
        Macht den letzten Wurf des aktuellen Spielers rückgängig (Undo).

        Holt den letzten Wurf aus der Wurfhistorie, delegiert die komplexe
        Logik zur Wiederherstellung des Spielzustands an die zuständige
        Spiellogik-Klasse und entfernt die Dart-Grafik vom Board.
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
            Player or None: Die Instanz des aktuellen Spielers oder None,
                            wenn keine Spieler mehr im Spiel sind.
        """
        if not self.players:
            return None
        # self.current sollte durch Initialisierung und next_player immer im gültigen Bereich sein
        return self.players[self.current]

    def announce_current_player_turn(self):
        """
        Kündigt den Zug des aktuellen Spielers über die Benutzeroberfläche an.

        Zeigt eine `MessageBox` an, um den Spielerwechsel klar zu signalisieren,
        und bringt das Scoreboard des aktiven Spielers in den Vordergrund.
        Für Spielmodi wie "Killer" werden kontextsensitive Anweisungen
        angezeigt, um den Spieler durch spezielle Phasen zu leiten.
        """
        player = self.current_player()
        if not player: # Sollte nicht passieren, wenn Spieler vorhanden sind
            return

        round_info = f"Runde {self.round}."
        player_info = f"{player.name} ist am Zug."
        
        # Spezielle Nachricht für den allerersten Wurf des Spiels
        if self.current == 0 and self.round == 1 and not player.throws: # Check for no throws as well
            messagebox.showinfo("Spielstart", f"{player.name} beginnt!", parent=self.db.root)
        else:
            messagebox.showinfo("Spielerwechsel", f"{round_info}\n{player_info}", parent=self.db.root)
        
        # Spezifische Nachricht für Killer-Modus, wenn Lebensfeld bestimmt werden muss
        if self.name == "Killer":
            if not player.state['life_segment']:
                messagebox.showinfo("Lebensfeld ermitteln",
                                    f"{player.name}, du musst nun dein Lebensfeld bestimmen.\n"
                                    f"Wirf mit deiner NICHT-dominanten Hand.\n"
                                    "Das Double des getroffenen Segments wird dein Lebensfeld.\n"
                                    "Ein Treffer auf Bull/Bullseye zählt als Lebensfeld 'Bull'.",
                                    parent=self.db.root)
            elif player.state['life_segment'] and not player.state['can_kill']: # Only show if life_segment is set but not yet a killer
                segment_str = "Bull" if player.state['life_segment'] == "Bull" else f"Double {player.state['life_segment']}"
                messagebox.showinfo("Zum Killer werden",
                                    f"{player.name}, jetzt musst du dein Lebensfeld ({segment_str}) treffen um Killer-Status zu erlangen.\n"
                                    "Erst dann kannst du andere Spieler eliminieren.\n"
                                    "VORSICHT!\n"
                                    "Triffst du als Killer dein eigenes Lebensfeld, verlierst du selbst ein Leben!",
                                    parent=self.db.root)
        
        if self.db:
            self.db.clear_dart_images_from_canvas()
        
        # Sicherstellen, dass Scoreboard existiert und fokussiert werden kann
        if hasattr(player, 'sb') and player.sb and hasattr(player.sb, 'score_window') and player.sb.score_window.winfo_exists():
            player.sb.score_window.lift()
            player.sb.score_window.focus_force()

    def next_player(self):
        """
        Wechselt zum nächsten Spieler oder startet eine neue Runde.

        Wird aufgerufen, nachdem ein Spieler seinen Zug beendet hat. Setzt den
        Zeiger (`self.current`) auf den nächsten Spieler in der Liste und erhöht
        den Rundenzähler, falls eine volle Runde abgeschlossen wurde.
        """
        if not self.players: # Keine Spieler mehr im Spiel
            return

        if self.end == True:
            self.destroy()
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
        Factory-Methode zur Auswahl der Spiellogik.

        Basierend auf dem Namen des Spiels (`self.name`) wird die passende
        Logik-Klasse aus einer vordefinierten Zuordnung (GAME_LOGIC_MAP)
        ausgewählt und instanziiert. Dies vermeidet dynamische Imports und
        macht die Abhängigkeiten der Klasse explizit.
        """
        logic_class = GAME_LOGIC_MAP.get(self.name)
        if logic_class:
            return logic_class(self)
        else:
            # Fallback oder Fehlerbehandlung, falls ein unbekannter Spielname übergeben wird
            raise ValueError(f"Unbekannter oder nicht implementierter Spielmodus: {self.name}")


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

    def _finalize_and_record_stats(self, winner):
        """
        Finalisiert und speichert die Statistiken für alle Spieler am Ende des Spiels.
        """
        if not self.player_stats_manager:
            return

        for p in self.players:
            stats_data = {
                'game_mode': self.name,
                'win': (p == winner)
            }
            if self.name in ('301', '501', '701'):
                stats_data['average'] = p.get_average()
                stats_data['checkout_percentage'] = p.get_checkout_percentage()
                stats_data['highest_finish'] = p.stats.get('highest_finish', 0)
            
            elif self.name in ('Cricket', 'Cut Throat', 'Tactics'):
                stats_data['mpr'] = p.get_mpr()

            self.player_stats_manager.add_game_record(p.name, stats_data)

    def throw(self, ring, segment):
        """
        Verarbeitet einen Wurf eines Spielers.
        
        Dies ist der Haupteinstiegspunkt von der UI (`DartBoard`) in die
        Spiellogik. Die Methode prüft, ob der Spieler noch Würfe in seiner
        Runde übrig hat, und delegiert dann die Verarbeitung an die
        `_handle_throw`-Methode der zuständigen Spiellogik-Instanz. Löst bei
        Erfolg auch Soundeffekte aus.

        Args:
            ring (str): Der getroffene Ring (z.B. "Single", "Double").
            segment (int): Das getroffene Segment (Zahlenwert).
        """
        player = self.current_player()
        if len(player.throws) < 3:
            # Soundeffekt für einen Treffer sofort abspielen, BEVOR die Spiellogik
            # aufgerufen wird, da diese blockierende Dialoge (MessageBox) enthalten kann.
            if self.sound_manager and ring != "Miss":
                self.sound_manager.play_hit()

            msg = self.game._handle_throw(player, ring, segment, self.players)
            
            # Soundeffekt für einen Gewinn abspielen.
            # Dies geschieht, bevor die finale Gewinn-MessageBox im Dartboard angezeigt wird.
            if self.sound_manager:
                if msg and "🏆" in msg: # Gewinn-Sound
                    self.sound_manager.play_win()
                    # Statistiken für alle Spieler am Ende des Spiels speichern
                    self._finalize_and_record_stats(winner=player)
            
            return msg
        else:
            messagebox.showinfo("Zuviel Würfe", "Bitte 'Weiter' klicken!", parent=self.db.root)
            return self.db.clear_last_dart_image_from_canvas()
