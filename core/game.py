# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Dieses Modul definiert die Hauptlogik für verschiedene Dartspiele.
Es enthält die Game-Klasse, die den Spielablauf und die Spieler verwaltet.
"""
import tkinter as tk
from . import ui_utils
from .game_ui import GameUI
from .player import Player
from .ai_player import AIPlayer
from .x01 import X01
from .cricket import Cricket
from .atc import AtC
from .elimination import Elimination
from .micky import Micky
from .killer import Killer
from .shanghai import Shanghai

#
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
    def __init__(self, root, game_options, player_names, sound_manager=None, highscore_manager=None, player_stats_manager=None, profile_manager=None):
        """
        Initialisiert eine neue Spielinstanz.

        Args:
            root (tk.Tk): Das Hauptfenster der Anwendung, das als Parent dient.
            game_options (dict): Ein Dictionary mit allen Spieloptionen.
            player_names (list): Eine Liste der Namen der teilnehmenden Spieler.
            sound_manager (SoundManager, optional): Instanz zur Soundwiedergabe.
            highscore_manager (HighscoreManager, optional): Instanz zur Verwaltung von Highscores.
            player_stats_manager (PlayerStatsManager, optional): Instanz zur Verwaltung von Spielerstatistiken.
            profile_manager (PlayerProfileManager, optional): Instanz zur Verwaltung von Spielerprofilen.
        """
        self.root = root
        self.sound_manager = sound_manager
        self.highscore_manager = highscore_manager
        self.player_stats_manager = player_stats_manager
        self.profile_manager = profile_manager
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
        self.winner = None
        self.game = self.get_game_logic()
        self.targets = self.game.get_targets()
        
        # Spieler-Instanzen erstellen und Profile zuweisen
        self.players = []
        for name in player_names:
            profile = self.profile_manager.get_profile_by_name(name) if self.profile_manager else None
            if profile and profile.is_ai:
                self.players.append(AIPlayer(name, self, profile=profile))
            else:
                self.players.append(Player(name, self, profile=profile))
        
        # Spielspezifischen Zustand für jeden Spieler initialisieren,
        # indem die Logik an die jeweilige Spielklasse delegiert wird.
        for player in self.players:
            self.game.initialize_player_state(player)

        # Spezifische Initialisierung für Killer nach Erstellung der Spieler
        if self.name == "Killer" and hasattr(self.game, 'set_players'):
            self.game.set_players(self.players)
            
        # --- UI-Setup ---
        # Die Game-Klasse delegiert die Erstellung ihrer UI an den GameUI-Manager.
        self.ui = GameUI(self)

    def destroy(self):
        """Zerstört alle UI-Elemente, die zu diesem Spiel gehören, sicher."""
        if self.ui:
            self.ui.destroy()
        # Setzt die Referenzen zurück, um Memory-Leaks zu vermeiden
        self.ui = None
    
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

        # Zerstöre das Scoreboard des Spielers, bevor er aus der Liste entfernt wird,
        # um hängende UI-Fenster zu vermeiden.
        if player_to_remove.sb and player_to_remove.sb.score_window.winfo_exists():
            try:
                player_to_remove.sb.score_window.destroy()
            except tk.TclError:
                pass # Fenster wurde möglicherweise bereits anderweitig geschlossen

        was_current_player = (player_to_remove_index == self.current)

        # Passe den 'current' Index an, BEVOR der Spieler entfernt wird.
        if player_to_remove_index < self.current:
            self.current -= 1

        # Entferne den Spieler aus der Liste
        self.players.pop(player_to_remove_index)

        # --- Spielzustand nach dem Entfernen prüfen ---

        # Fall 1: Keine Spieler mehr übrig
        if not self.players:
            ui_utils.show_message('info', "Spielende", "Alle Spieler haben das Spiel verlassen.", parent=self.root)
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
        # Wenn das Spiel beendet war, müssen alle Gewinn-Flags zurückgesetzt werden,
        # bevor die Logik des Wurfs selbst rückgängig gemacht wird.
        if self.end:
            self.end = False
            self.winner = None
            self.shanghai_finish = False
        player = self.current_player()
        if player and player.throws:
            popped_throw = player.throws.pop() # This is now a 3-tuple (ring, segment, coords)
            self.game._handle_throw_undo(player, popped_throw[0], popped_throw[1], self.players)
        self.ui.db.clear_last_dart_image_from_canvas()
        # Nach dem Undo die Button-Zustände aktualisieren
        self.ui.db.update_button_states()
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
        Kündigt den Zug des aktuellen Spielers an.
        Für menschliche Spieler wird eine MessageBox angezeigt.
        Für KI-Spieler wird der automatische Zug gestartet.
        """
        player = self.current_player()
        if not player:
            return

        # UI-Aktionen an den UI-Manager delegieren
        self.ui.announce_turn(player)

        # --- Unterscheidung zwischen Mensch und KI ---
        # Diese Logik verbleibt im Controller
        if player.is_ai():
            # Für einen KI-Spieler wird der automatische Zug direkt gestartet.
            # Die take_turn Methode ist asynchron und verwendet root.after().
            player.take_turn()
        else:
            # Für einen menschlichen Spieler wird eine blockierende MessageBox angezeigt.
            # Spezielle Nachricht für den allerersten Wurf des Spiels
            if self.current == 0 and self.round == 1 and not player.throws and self.ui and self.ui.db:
                ui_utils.show_message('info', "Spielstart", f"{player.name} beginnt!", parent=self.ui.db.root)
            
            # Spezifische Nachricht für Killer-Modus
            if self.name == "Killer":
                if not player.state.get('life_segment'): # Prompt to determine life segment
                    ui_utils.show_message('info', "Lebensfeld ermitteln",
                                        f"{player.name}, du musst nun dein Lebensfeld bestimmen.\n"
                                        f"Wirf mit deiner NICHT-dominanten Hand.\n"
                                        "Das Double des getroffenen Segments wird dein Lebensfeld.\n"
                                        "Ein Treffer auf Bull/Bullseye zählt als Lebensfeld 'Bull'.", parent=self.ui.db.root)
                elif player.state['life_segment'] and not player.state['can_kill']: # Prompt to become killer
                    segment_str = "Bull" if player.state['life_segment'] == "Bull" else f"Double {player.state['life_segment']}"
                    ui_utils.show_message('info', "Zum Killer werden",
                                        f"{player.name}, jetzt musst du dein Lebensfeld ({segment_str}) treffen um Killer-Status zu erlangen.", parent=self.ui.db.root)

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
            # Deaktiviere die Hervorhebung für den Spieler, der gerade fertig ist
            if hasattr(current_p, 'sb') and current_p.sb:
                current_p.sb.set_active(False)
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

    def _play_round_end_sound(self, player):
        """Spielt am Ende einer Runde einen speziellen Sound für hohe Scores."""
        if not self.sound_manager or len(player.throws) != 3:
            return

        # Nur für X01-Spiele relevant
        if self.name not in ('301', '501', '701'):
            return

        # Berechne den Score dieser Runde
        round_score = 0
        for r, s, _ in player.throws: # Unpack the 3-tuple, ignoring coords
            round_score += self.get_score(r, s)

        # Spiele den passenden Sound
        if round_score == 180:
            self.sound_manager.play_score_180()
        elif round_score == 100:
            self.sound_manager.play_score_100()

    def _finalize_and_record_stats(self, winner):
        """
        Finalisiert und speichert die Statistiken für alle Spieler am Ende des Spiels.
        """
        if not self.player_stats_manager:
            return

        for p in self.players:
            # Sammle alle Wurfkoordinaten des Spielers aus dem gesamten Spiel
            all_coords = [coords for _, _, coords in p.all_game_throws if coords is not None]

            stats_data = {
                'game_mode': self.name,
                'win': (p == winner),
                'all_throws_coords': all_coords
            }
            if self.name in ('301', '501', '701'):
                stats_data['average'] = p.get_average()
                stats_data['checkout_percentage'] = p.get_checkout_percentage()
                stats_data['highest_finish'] = p.stats.get('highest_finish', 0)
            
            elif self.name in ('Cricket', 'Cut Throat', 'Tactics'):
                stats_data['mpr'] = p.get_mpr()

            self.player_stats_manager.add_game_record(p.name, stats_data)

    def throw(self, ring, segment, coords=None):
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
            coords (tuple, optional): Die (x, y)-Koordinaten des Wurfs für die Heatmap.
        """
        player = self.current_player()
        if len(player.throws) < 3:
            # --- Sofortiges akustisches Feedback für den Wurf ---
            if self.sound_manager:
                if ring == "Bullseye":
                    self.sound_manager.play_bullseye()
                elif ring == "Bull":
                    self.sound_manager.play_bull()
                elif ring == "Miss":
                    self.sound_manager.play_miss()
                elif ring != "Miss": # Für alle anderen Treffer
                    self.sound_manager.play_hit()

            # Wurf immer protokollieren, da jeder Klick ein Wurf ist.
            # Die Spiellogik entscheidet, was mit dem Wurf passiert.
            player.throws.append((ring, segment, coords))

            # Delegiere die Verarbeitung an die spezifische Spiellogik (z.B. X01, Cricket)
            # Die Logik gibt jetzt ein Tupel (status, message) zurück
            throw_result = self.game._handle_throw(player, ring, segment, self.players)
            
            # Entpacke das Ergebnis, wenn es ein Tupel ist, sonst behandle es als Nachricht
            if isinstance(throw_result, tuple):
                status, message = throw_result
            else: # Für ältere Logik-Klassen, die nur eine Nachricht zurückgeben
                status, message = ('win' if throw_result else 'ok', throw_result)
            
            # --- Sound für Rundenende prüfen ---
            if len(player.throws) == 3:
                self._play_round_end_sound(player)

            # Button-Zustände nach jedem Wurf aktualisieren
            self.ui.db.update_button_states()
            
            # --- Event-Verarbeitung ---
            if status == 'win':
                # Füge einen eventuellen "Shanghai"-Prefix hinzu
                if self.shanghai_finish:
                    message = "SHANGHAI-FINISH!\n" + message

                # Finalisiere die Statistiken für das Spiel, bevor die UI blockiert wird
                self._finalize_and_record_stats(winner=player)

                def play_win_and_show_message():
                    """Spielt den Gewinn-Sound und zeigt dann die Nachricht."""
                    if self.sound_manager:
                        if self.shanghai_finish:
                            self.sound_manager.play_shanghai()
                        else:
                            self.sound_manager.play_win()
                    ui_utils.show_message('info', "Spielende", message, parent=self.ui.db.root)

                # Verzögere den Gewinn-Sound und die Nachricht um 500ms,
                # damit der Treffer-Sound ausklingen kann und sich die Effekte nicht überlagern.
                self.root.after(500, play_win_and_show_message)
            elif status in ('info', 'warning', 'error', 'bust', 'invalid_open', 'invalid_target'):
                title_map = {
                    'info': 'Info', 'warning': 'Warnung', 'error': 'Fehler',
                    'bust': 'Bust', 'invalid_open': 'Ungültiger Wurf',
                    'invalid_target': 'Falsches Ziel'
                }
                msg_type = 'error' if status in ('bust', 'invalid_open', 'invalid_target', 'error') else status
                title = title_map.get(status, 'Info')
                if message:
                    ui_utils.show_message(msg_type, title, message, parent=self.ui.db.root)
        else:
            ui_utils.show_message('info', "Zuviel Würfe", "Bitte 'Weiter' klicken!", parent=self.ui.db.root)
            return self.ui.db.clear_last_dart_image_from_canvas()
