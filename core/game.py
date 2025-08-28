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
from .game_options import GameOptions
from .player import Player
from .ai_player import AIPlayer
from .x01 import X01
from .throw_result import ThrowResult
from .save_load_manager import SaveLoadManager
from .cricket import Cricket
from .atc import AtC
from .elimination import Elimination
from .micky import Micky
from .killer import Killer
from .shanghai import Shanghai
from .dartboard import DartBoard
from .scoreboard import setup_scoreboards

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
    def __init__(self, root, game_options: GameOptions, player_names, on_throw_processed_callback, highscore_manager=None, player_stats_manager=None, profile_manager=None, settings_manager=None, is_tournament_match=False):
        """
        Initialisiert eine neue Spielinstanz.

        Args:
            root (tk.Tk): Das Hauptfenster der Anwendung, das als Parent dient.
            game_options (dict): Ein Dictionary mit allen Spieloptionen.
            player_names (list): Eine Liste der Namen der teilnehmenden Spieler.
            on_throw_processed_callback (callable): Callback-Funktion, die nach einem Wurf aufgerufen wird.
            highscore_manager (HighscoreManager, optional): Instanz zur Verwaltung von Highscores.
            player_stats_manager (PlayerStatsManager, optional): Instanz zur Verwaltung von Spielerstatistiken.
            profile_manager (PlayerProfileManager, optional): Instanz zur Verwaltung von Spielerprofilen.
            settings_manager (SettingsManager, optional): Instanz zur Verwaltung von App-Einstellungen.
            is_tournament_match (bool): True, wenn das Spiel Teil eines Turniers ist.
        """
        self.root = root
        self.on_throw_processed = on_throw_processed_callback
        self.highscore_manager = highscore_manager
        self.player_stats_manager = player_stats_manager
        self.profile_manager = profile_manager
        self.settings_manager = settings_manager
        self.options = game_options
        self.current = 0
        self.round = 1
        self.shanghai_finish = False
        self.is_tournament_match = is_tournament_match
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

        # Spieler-
        # --- Legs & Sets Konfiguration ---
        self.legs_to_win = self.options.legs_to_win
        self.sets_to_win = self.options.sets_to_win
        self.is_leg_set_match = self.legs_to_win > 1 or self.sets_to_win > 1

        if self.is_leg_set_match:
            self.player_leg_scores = {p.id: 0 for p in self.players}
            self.player_set_scores = {p.id: 0 for p in self.players}
            self.leg_start_player_index = 0
            self.current = self.leg_start_player_index
        
        # Spielspezifischen Zustand für jeden Spieler initialisieren,
        # indem die Logik an die jeweilige Spielklasse delegiert wird.
        for player in self.players:
            self.game.initialize_player_state(player)

        # Spezifische Initialisierung für Killer nach Erstellung der Spieler
        if self.options.name == "Killer" and hasattr(self.game, 'set_players'):
            self.game.set_players(self.players)
            
        # --- UI-Setup: Die Game-Klasse erstellt und verwaltet ihre UI-Komponenten direkt ---
        self.dartboard = DartBoard(self)
        # Die Erstellung und Positionierung der Scoreboards wird an eine Hilfsfunktion ausgelagert.
        self.scoreboards = setup_scoreboards(self)

    def destroy(self):
        """Zerstört alle UI-Elemente, die zu diesem Spiel gehören, sicher."""
        # Das Zerstören des Dartboard-Fensters zerstört automatisch alle untergeordneten
        # Scoreboard-Fenster.
        if self.dartboard and self.dartboard.root and self.dartboard.root.winfo_exists():
            self.dartboard.root.destroy()
        # Setzt die Referenzen zurück, um Speicherlecks zu vermeiden.
        self.dartboard = None
        self.scoreboards = []
    
    def leave(self, player_to_remove: Player):
        """
        Entfernt einen Spieler aus dem laufenden Spiel.
        
        Behandelt verschiedene Szenarien, z.B. wenn der aktuell spielende
        Spieler entfernt wird oder wenn der letzte verbleibende Spieler das
        Spiel verlässt, was zum Spielende führt.
        """
        try:
            player_to_remove_index = self.players.index(player_to_remove)
        except ValueError:
            return # Spieler wurde nicht in der Liste gefunden, nichts zu tun.

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
        
        # NEU: Passe auch den Startspieler-Index für das nächste Leg an.
        if self.is_leg_set_match and player_to_remove_index < self.leg_start_player_index:
            self.leg_start_player_index -= 1

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
        self.dartboard.clear_last_dart_image_from_canvas()
        # Nach dem Undo die Button-Zustände aktualisieren
        self.dartboard.update_button_states()
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

    def _update_ui_for_new_turn(self, player: Player):
        """
        Aktualisiert alle UI-Komponenten, um den Beginn eines neuen Zugs widerzuspiegeln.
        Kapselt die direkte UI-Manipulation.
        """
        if not player:
            return

        # Dart-Farbe und Buttons auf dem Dartboard aktualisieren
        if self.dartboard:
            dart_color = player.profile.dart_color if player.profile else "#ff0000"
            self.dartboard.update_dart_image(dart_color)
            self.dartboard.clear_dart_images_from_canvas()
            self.dartboard.update_button_states()

        # Scoreboards aktualisieren (aktiven Spieler hervorheben)
        for p in self.players:
            if p.sb and hasattr(p.sb, 'set_active'):
                is_active = p.id == player.id
                p.sb.set_active(is_active)
                if is_active and p.sb.score_window.winfo_exists():
                    p.sb.score_window.lift()
                    p.sb.score_window.focus_force()

    def announce_current_player_turn(self):
        """
        Kündigt den Zug des aktuellen Spielers an.
        Aktualisiert die UI und startet dann entweder den KI-Zug oder zeigt
        eine Nachricht für einen menschlichen Spieler an.
        """
        player = self.current_player()
        if not player:
            return

        # Schritt 1: UI für den neuen Zug aktualisieren
        self._update_ui_for_new_turn(player)

        # Schritt 2: Den eigentlichen Zug starten (Mensch vs. KI)
        if player.is_ai():
            # Für einen KI-Spieler wird der automatische Zug direkt gestartet.
            player.take_turn()
        else:
            # Für einen menschlichen Spieler wird eine blockierende MessageBox angezeigt.
            if self.current == 0 and self.round == 1 and not player.throws and self.dartboard:
                ui_utils.show_message('info', "Spielstart", f"{player.name} beginnt!", parent=self.dartboard.root)
            
            # Hole eine spielspezifische Nachricht vom Logik-Handler
            turn_message_data = self.game.get_turn_start_message(player) # type: ignore
            if turn_message_data and self.dartboard:
                msg_type, title, message = turn_message_data
                ui_utils.show_message(msg_type, title, message, parent=self.dartboard.root)

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
        logic_class = GAME_LOGIC_MAP.get(self.options.name)
        if logic_class:
            return logic_class(self)
        else:
            # Fallback oder Fehlerbehandlung, falls ein unbekannter Spielname übergeben wird
            raise ValueError(f"Unbekannter oder nicht implementierter Spielmodus: {self.options.name}")


    @staticmethod
    def get_score(ring, segment):
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

    def _determine_sound_for_throw(self, result: "ThrowResult", player: Player, ring: str) -> str | None:
        """
        Bestimmt den passenden Sound für das Ergebnis eines Wurfs.
        Kapselt die Sound-Auswahl-Logik.
        """
        if result.status == 'win':
            return 'shanghai' if self.shanghai_finish else 'win'
        if result.status == 'bust':
            return 'bust'
        
        # Sound für Rundenende (nur bei X01)
        if len(player.throws) == 3 and self.options.name in ('301', '501', '701'):
            # Unpack the 3-tuple, ignoring coords
            round_score = sum(Game.get_score(r, s) for r, s, _ in player.throws)
            score_sounds = {180: "score_180", 160: "score_160", 140: "score_140", 120: "score_120", 100: "score_100"}
            if sound := score_sounds.get(round_score):
                return sound

        # Standard-Treffer-Sound
        hit_sounds = {"Bullseye": "bullseye", "Bull": "bull", "Miss": "miss"}
        return hit_sounds.get(ring, "hit")

    def _finalize_and_record_stats(self, winner: Player):
        """
        Finalisiert und speichert die Statistiken für alle Spieler am Ende des Spiels.
        """
        if not self.player_stats_manager:
            return

        for p in self.players:
            # Sammle alle Wurfkoordinaten des Spielers aus dem gesamten Spiel
            all_coords = [coords for _, _, coords in p.all_game_throws if coords is not None]

            stats_data = {
                'game_mode': self.options.name,
                'win': (p == winner),
                'all_throws_coords': all_coords
            }
            if self.options.name in ('301', '501', '701'):
                stats_data['average'] = p.get_average()
                stats_data['checkout_percentage'] = p.get_checkout_percentage()
                stats_data['highest_finish'] = p.stats.get('highest_finish', 0)
            
            elif self.options.name in ('Cricket', 'Cut Throat', 'Tactics'):
                stats_data['mpr'] = p.get_mpr()

            self.player_stats_manager.add_game_record(p.name, stats_data)
        
        # Highscore-Logik hier zentralisieren
        if self.highscore_manager:
            # Für X01 ist die Metrik die Anzahl der Darts
            if self.options.name in ('301', '501', '701'):
                total_darts = winner.get_total_darts_in_game()
                self.highscore_manager.add_score(self.options.name, winner.name, total_darts)
            # Für Cricket ist die Metrik die MPR
            elif self.options.name in ('Cricket', 'Cut Throat', 'Tactics'):
                mpr = winner.get_mpr()
                self.highscore_manager.add_score(self.options.name, winner.name, mpr)

    def throw(self, ring, segment, coords=None):
        """
        Verarbeitet einen Wurf eines Spielers.
        Fokussiert sich auf die Aktualisierung des Spielzustands und delegiert
        die Logik und das Feedback an spezialisierte Methoden.

        Args:
            ring (str): Der getroffene Ring (z.B. "Single", "Double").
            segment (int): Das getroffene Segment (Zahlenwert).
            coords (tuple, optional): Die (x, y)-Koordinaten des Wurfs für die Heatmap.
        """
        player = self.current_player()
        if not player: return

        if len(player.throws) >= 3:
            ui_utils.show_message('info', "Zuviel Würfe", "Bitte 'Weiter' klicken!", parent=self.dartboard.root)
            # Verhindert, dass ein Dart-Bild für einen ungültigen Wurf gezeichnet wird.
            if self.dartboard:
                self.dartboard.clear_last_dart_image_from_canvas()
            return
        
        # Wurf protokollieren
        player.throws.append((ring, segment, coords))

        # Verarbeitung an die spezifische Spiellogik delegieren
        throw_result = self.game._handle_throw(player, ring, segment, self.players)

        # Ergebnis entpacken
        if isinstance(throw_result, tuple):
            status, message = throw_result
        else: # Fallback für ältere Logik, die nur einen String zurückgibt
            status, message = ('win' if throw_result else 'ok', throw_result)

        # Erstelle ein strukturiertes Ergebnisobjekt
        result = ThrowResult(status=status, message=message)

        # Sound bestimmen und dem Ergebnisobjekt hinzufügen (bleibt hier)
        result.sound = self._determine_sound_for_throw(result, player, ring)

        # Rufe den Callback auf, um das UI-Feedback zu verarbeiten
        self.on_throw_processed(result, player)

        # NEU: Wenn das Spiel durch diesen Wurf gewonnen wurde, die Statistiken finalisieren.
        # Für X01 wird dies durch _handle_leg_win() gesteuert, das von der X01-Logik aufgerufen wird.
        # Für alle anderen Spiele (ohne Legs/Sets) müssen wir es hier explizit aufrufen.
        if result.status == 'win' and self.winner and not self.is_leg_set_match:
            # Die X01-Logik ruft _handle_leg_win, was wiederum _finalize_and_record_stats aufruft.
            self._finalize_and_record_stats(self.winner)

        # Button-Zustände nach jedem Wurf aktualisieren, damit "Weiter" und "Zurück"
        # korrekt aktiviert/deaktiviert werden.
        if self.dartboard:
            self.dartboard.update_button_states()

    def _update_leg_set_displays(self):
        """Weist alle Scoreboards an, ihre Leg/Set-Anzeige zu aktualisieren."""
        if not self.is_leg_set_match:
            return
        for p in self.players:
            if p.sb and hasattr(p.sb, 'update_leg_set_scores'):
                leg_score = self.player_leg_scores.get(p.id, 0)
                set_score = self.player_set_scores.get(p.id, 0)
                p.sb.update_leg_set_scores(leg_score, set_score)

    def _handle_leg_win(self, winner: Player):
        """
        Wird von der Spiellogik (z.B. X01) aufgerufen, wenn ein Leg endet.
        Steuert den Ablauf von Legs und Sets.
        """
        if not self.is_leg_set_match:
            # Dies ist ein einfaches Spiel (keine Legs/Sets). Der Gewinn des "Legs" ist der Gewinn des Matches.
            self._finalize_and_record_stats(winner)
            return

        self.player_leg_scores[winner.id] += 1
        self._update_leg_set_displays()

        # Prüfen, ob der Satz gewonnen wurde
        if self.player_leg_scores[winner.id] >= self.legs_to_win:
            self.player_set_scores[winner.id] += 1
            self.player_leg_scores = {p.id: 0 for p in self.players} # Reset für nächsten Satz
            self._update_leg_set_displays() # Anzeige aktualisieren (Legs=0, Sets++)
            ui_utils.show_message('info', "Satzgewinn", f"{winner.name} gewinnt den Satz!", parent=self.dartboard.root)

            # Prüfen, ob das gesamte Match gewonnen wurde
            if self.player_set_scores[winner.id] >= self.sets_to_win:
                # Finaler Gewinn des Matches. Jetzt werden die Statistiken gespeichert.
                self._finalize_and_record_stats(winner)
                return
            else:
                # Nächster Satz beginnt
                self.end = False
                self.winner = None
                self._start_next_leg()
        else:
            # Nächstes Leg im selben Satz
            ui_utils.show_message('info', "Leg-Gewinn", f"{winner.name} gewinnt das Leg!", parent=self.dartboard.root)
            self.end = False
            self.winner = None
            self._start_next_leg()

    def _start_next_leg(self):
        """Setzt den Zustand für das nächste Leg zurück."""
        # Setze den Zustand für alle Spieler zurück
        for player in self.players:
            # Setze die Leg-spezifischen Statistiken zurück, bevor der neue Zustand gesetzt wird.
            player.reset_leg_stats()
            player.reset_turn() # Leert die 'throws'-Liste für alle
            self.game.initialize_player_state(player) # Setzt Score, etc.

        # Wer beginnt das nächste Leg? (abwechselnd)
        self.leg_start_player_index = (self.leg_start_player_index + 1) % len(self.players)
        self.current = self.leg_start_player_index
        
        # UI für alle Scoreboards aktualisieren
        for p in self.players:
            if p.sb:
                p.sb.update_score(p.score)

        self.announce_current_player_turn()

    def to_dict(self) -> dict:
        """
        Serialisiert den kompletten Spielzustand in ein Dictionary.
        Implementiert einen Teil der Speicher-Schnittstelle.
        """
        players_data = []
        for p in self.players:
            player_dict = {
                'name': p.name,
                'id': p.id,
                'score': p.score,
                'throws': p.throws,
                'stats': p.stats,
                'state': p.state,
            }
            players_data.append(player_dict)

        game_state = {
            **self.options.to_dict(),
            'current_player_index': self.current,
            'round': self.round,
            'players': players_data,
        }

        # Füge den Zustand für Legs & Sets hinzu, falls es sich um ein solches Match handelt.
        # Dies ist wichtig für das korrekte Laden des Spiels.
        if self.is_leg_set_match:
            game_state.update({
                'player_leg_scores': self.player_leg_scores,
                'player_set_scores': self.player_set_scores,
                'leg_start_player_index': self.leg_start_player_index
            })

        return game_state

    def get_save_meta(self) -> dict:
        """
        Gibt die Metadaten für den Speicherdialog zurück.
        Implementiert den zweiten Teil der Speicher-Schnittstelle.
        """
        return {
            'title': "Spiel speichern unter...",
            'filetypes': SaveLoadManager.GAME_FILE_TYPES,
            'defaultextension': ".json",
            'save_type': SaveLoadManager.GAME_SAVE_TYPE
        }
