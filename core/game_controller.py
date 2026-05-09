from __future__ import annotations

"""
Dieses Modul definiert die Hauptlogik für verschiedene Dartspiele.
Es enthält die GameController-Klasse, die den Spielablauf und die Spieler verwaltet.
"""
import logging
import tkinter as tk
from typing import TYPE_CHECKING
from . import ui_utils
from .game_logic_base import GameLogicBase
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
from .split_score import SplitScore

if TYPE_CHECKING:
    from .game_view_manager import GameViewManager
    from .scoreboard import Scoreboard

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
    "Split Score": SplitScore,
}

# Leite Listen von Spielmodi-Typen aus der GAME_LOGIC_MAP ab.
# Dies zentralisiert die Konfiguration und vermeidet doppelte Listen.
X01_MODES = [mode for mode, logic in GAME_LOGIC_MAP.items() if logic == X01]
CRICKET_MODES = [mode for mode, logic in GAME_LOGIC_MAP.items() if logic == Cricket]
HIGHSCORE_MODES = sorted(list(GAME_LOGIC_MAP.keys()))


logger = logging.getLogger(__name__)


class GameController:
    """
    Die zentrale Steuerungseinheit für eine Dartspiel-Sitzung (Controller).

    Diese Klasse initialisiert und verwaltet den gesamten Spielzustand,
    einschließlich der Spieler, Runden und Spieloptionen. Sie agiert als
    der die Interaktionen zwischen dem GameViewManager (UI), den Datenmodellen
    (Player) und den spezialisierten
    Logik-Handlern (z.B. X01, Cricket) koordiniert.

    Verantwortlichkeiten:
    - Initialisierung des Spiels mit den gewählten Optionen und Spielern.
    - Dynamisches Laden der korrekten Spiellogik über eine Factory-Methode.
    - Verwaltung des Spielablaufs (Spielerwechsel, Runden zählen).
    - Entgegennahme von UI-Events (Würfe, Undo, Spieler verlässt Spiel) und
      Delegation an die zuständigen Methoden oder Logik-Handler.
    - Koordination mit dem GameViewManager für UI-Updates.
    """

    root: tk.Tk
    on_throw_processed: callable
    highscore_manager: object | None
    player_stats_manager: object | None
    profile_manager: object | None
    settings_manager: object | None
    options: GameOptions
    current: int
    round: int
    shanghai_finish: bool
    shanghai_finish_round: int | None
    is_tournament_match: bool
    end: bool
    winner: Player | None
    game_view_manager: GameViewManager | None
    players: list[Player]
    game: GameLogicBase
    targets: list[str]
    scoreboards: list["Scoreboard"]

    def __init__(
        self,
        root: tk.Tk,
        game_options: GameOptions,
        player_names: list[str],
        on_throw_processed_callback: callable,
        highscore_manager=None,
        player_stats_manager=None,
        profile_manager=None,
        settings_manager=None,
        is_tournament_match: bool = False,
    ):
        """
        Initialisiert eine neue Spielinstanz.

        Args:
            root (tk.Tk): Das Hauptfenster der Anwendung, das als Parent dient.
            game_options (GameOptions): Eine Instanz der GameOptions.
            player_names (list[str]): Eine Liste der Namen der teilnehmenden Spieler.
            on_throw_processed_callback (callable): Callback-Funktion, die nach einem Wurf aufgerufen wird.
            highscore_manager (object, optional): Instanz zur Verwaltung von Highscores.
            player_stats_manager (object, optional): Instanz zur Verwaltung von Spielerstatistiken.
            profile_manager (object, optional): Instanz zur Verwaltung von Spielerprofilen.
            settings_manager (object, optional): Instanz zur Verwaltung von App-Einstellungen.
            is_tournament_match (bool): True, wenn das Spiel Teil eines Turniers ist.
        """
        self.root = root
        self.on_throw_processed = on_throw_processed_callback # Callback für App-Level Feedback
        self.highscore_manager = highscore_manager
        self.player_stats_manager = player_stats_manager
        self.profile_manager = profile_manager
        self.settings_manager = settings_manager
        self.options = game_options
        self.current = 0
        self.round = 1
        self.game_view_manager = None
        self.shanghai_finish = False
        self.shanghai_finish_round = None  # Neu: Speichert die Runde, in der ein Shanghai-Finish erzielt wurde
        self.is_tournament_match = is_tournament_match
        self.end = False
        self.winner = None

        # Schritt 1: Spielerliste erstellen.
        self.players = []  # Spieler-Instanzen erstellen und Profile zuweisen
        for name in player_names:
            profile = (
                self.profile_manager.get_profile_by_name(name) if self.profile_manager else None
            )
            if profile and profile.is_ai:
                self.players.append(AIPlayer(name, self, profile=profile))
            else:
                self.players.append(Player(name, self, profile=profile))

        # Schritt 2: Spiellogik und Ziele initialisieren, nachdem die Spieler existieren.
        self.game = self.get_game_logic()
        self.targets = self.game.get_targets()

        # Spielspezifischen Zustand für jeden Spieler initialisieren,
        # indem die Logik an die jeweilige Spielklasse delegiert wird.
        for player in self.players:
            self.game.initialize_player_state(player)

        # Spezifische Initialisierung nach Erstellung der Spieler (für Killer, X01 Legs/Sets)
        if hasattr(self.game, "set_players"):
            self.game.set_players(self.players)

    def destroy(self):
        """Zerstört alle UI-Elemente, die zu diesem Spiel gehören, sicher."""
        if self.game_view_manager:
            self.game_view_manager.destroy()

    @property
    def dartboard(self):
        """Gibt das Dartboard aus dem ViewManager zurück (für Abwärtskompatibilität)."""
        return self.game_view_manager.dartboard if self.game_view_manager else None

    def leave(self, player_to_remove: Player):
        """
        Entfernt einen Spieler aus dem laufenden Spiel.

        Behandelt verschiedene Szenarien, z.B. wenn der aktuell spielende
        Spieler entfernt wird oder wenn der letzte verbleibende Spieler das
        Spiel verlässt, was zum Spielende führt.
        """
        if player_to_remove not in self.players:
            return

        # UI des Spielers sicher zerstören
        if player_to_remove.sb and player_to_remove.sb.score_window.winfo_exists():
            try:
                player_to_remove.sb.score_window.destroy()
            except tk.TclError:
                pass  # Fenster wurde möglicherweise bereits anderweitig geschlossen

        # --- Vereinfachte Logik zur Bestimmung des nächsten Spielers ---
        # 1. Merke dir, wer als Nächstes dran gewesen wäre.
        was_current_player = self.current_player() == player_to_remove
        next_player_in_line = self.players[(self.players.index(player_to_remove) + 1) % len(self.players)]

        # 2. Entferne den Spieler.
        self.players.remove(player_to_remove)

        # 3. Prüfe, ob das Spiel vorbei ist.
        if not self.players:
            ui_utils.show_message(
                "info",
                "Spielende",
                "Alle Spieler haben das Spiel verlassen.",
                parent=self.game_view_manager.get_dartboard_root() if self.game_view_manager else self.root,
            )
            self.end = True
            self.destroy()
            return

        # 4. Setze den 'current'-Index neu, basierend auf dem, der als Nächstes dran war.
        try:
            self.current = self.players.index(next_player_in_line)
        except ValueError:
            # Dieser Fall tritt ein, wenn der 'next_player_in_line' derjenige war,
            # der entfernt wurde (passiert, wenn der letzte Spieler geht).
            # Der Index wird sicher auf 0 gesetzt.
            self.current = 0

        # 5. Wenn der Spieler am Zug entfernt wurde, starte den Zug des neuen Spielers.
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
        if self.end and self.game_view_manager:
            msg = (
                "Das Spiel ist bereits beendet und die Ergebnisse wurden gespeichert.\n\n"
                "Möchtest du den Sieg wirklich rückgängig machen? "
                "Dies löscht die aktuellen Einträge in der Statistik und der Highscore-Liste."
            )
            # Modaler Dialog am Dartboard-Fenster ausrichten
            parent = self.game_view_manager.get_dartboard_root() or self.root # type: ignore
            if not ui_utils.ask_question("yesno", "Sieg rückgängig machen", msg, parent=parent):
                return

            # NEU: Bereits gespeicherte Statistiken und Highscores aus der DB entfernen
            if self.player_stats_manager:
                self.player_stats_manager.delete_last_records_for_players(self.players)
            
            if self.highscore_manager and self.winner:
                self.highscore_manager.delete_last_score(self.options.name, self.winner.name)

            self.end = False
            self.winner = None
            self.shanghai_finish_round = None # Auch die Runde zurücksetzen
            self.shanghai_finish = False
        player = self.current_player()

        # NEU: Unterstützung für das Rückgängigmachen über Runden- und Spieler-Grenzen hinweg.
        # Wenn der aktuelle Spieler noch keine Würfe hat, springen wir zum vorherigen Spieler zurück.
        if player and not player.throws and not self.end:
            prev_idx = (self.current - 1) % len(self.players)
            # Abbrechen, wenn wir am absoluten Anfang des Spiels sind.
            if self.round == 1 and self.current == 0:
                return

            # Index und ggf. Runde aktualisieren
            if self.current == 0:
                self.round -= 1
            self.current = prev_idx
            player = self.current_player()

            # Die Würfe der letzten Aufnahme dieses Spielers wiederherstellen
            if player.turn_history:
                num_to_restore = player.turn_history.pop()
                player.throws = player.all_game_throws[-num_to_restore:]
                player.all_game_throws = player.all_game_throws[:-num_to_restore]

        if player and player.throws and self.game_view_manager: # type: ignore
            popped_throw = player.throws.pop()  # This is now a 3-tuple (ring, segment, coords)
            self.game._handle_throw_undo(player, popped_throw[0], popped_throw[1], self.players)
            self.game_view_manager.clear_last_dart_image() # type: ignore
            # Nach dem Undo die Button-Zustände aktualisieren
            self.game_view_manager.update_button_states(player, self.end)
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
        Aktualisiert die UI und startet dann entweder den KI-Zug oder zeigt
        eine Nachricht für einen menschlichen Spieler an.
        """
        if not self.game_view_manager:
            return

        player = self.current_player()
        if not player:
            return

        # Schritt 1: UI für den neuen Zug aktualisieren
        self.game_view_manager.update_ui_for_new_turn(player, self.round)

        # Schritt 2: Den eigentlichen Zug starten (Mensch vs. KI)
        if player.is_ai():
            # Für einen KI-Spieler wird der automatische Zug direkt gestartet.
            # Die KI benötigt eine Referenz zum ViewManager, um UI-Aktionen zu triggern
            player.take_turn(self.game_view_manager) # type: ignore
        else:
            # Für einen menschlichen Spieler wird eine blockierende MessageBox angezeigt.
            # Hole eine spielspezifische Nachricht vom Logik-Handler
            turn_message_data = self.game.get_turn_start_message(player)  # type: ignore
            self.game_view_manager.display_turn_start_message(player, self.round, turn_message_data)

    def next_player(self):
        """
        Wechselt zum nächsten Spieler oder startet eine neue Runde.

        Wird aufgerufen, nachdem ein Spieler seinen Zug beendet hat. Setzt den
        Zeiger (`self.current_player_index`) auf den nächsten Spieler in der Liste und erhöht
        den Rundenzähler, falls eine volle Runde abgeschlossen wurde.
        """
        if not self.players:  # Keine Spieler mehr im Spiel
            return

        if self.end:
            if self.game_view_manager:
                self.game_view_manager.destroy()
            return

        current_p = self.current_player()
        if current_p:
            # Hook für Spiellogiken, die am Ende einer Runde ausgeführt werden müssen (z.B. Split Score)
            if hasattr(self.game, "handle_end_of_turn"):
                self.game.handle_end_of_turn(current_p)

            current_p.reset_turn()  # Reset throws for the player whose turn just ended

        self.current = (self.current + 1) % len(self.players) # type: ignore
        if self.current == 0:  # Moved to next round
            self.round += 1

        self.announce_current_player_turn()  # Announce the new current player

    def get_game_logic(self):
        """
        Factory-Methode zur Auswahl der Spiellogik.

        Basierend auf dem Namen des Spiels (`self.name`) wird die passende
        Logik-Klasse aus einer vordefinierten Zuordnung (GAME_LOGIC_MAP)
        ausgewählt und instanziiert. Dies vermeidet dynamische Imports und
        macht die Abhängigkeiten der Klasse explizit.
        """
        logic_class = GAME_LOGIC_MAP.get(self.options.name) # type: ignore
        if logic_class:
            return logic_class(self)
        else:
            # Fallback oder Fehlerbehandlung, falls ein unbekannter Spielname übergeben wird
            raise ValueError(
                f"Unbekannter oder nicht implementierter Spielmodus: {self.options.name}"
            )

    @staticmethod
    def get_score(ring, segment):
        """
        Berechnet den Punktwert eines Wurfs basierend auf Ring und Segment.

        Args:
            ring (str): Der getroffene Ring
                        ("Single", "Double", "Triple", "Bull", "Bullseye", "Miss").
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

    def _determine_sound_for_throw(
        self, result: "ThrowResult", player: Player, ring: str
    ) -> str | None:
        """
        Bestimmt den passenden Sound für das Ergebnis eines Wurfs.
        Kapselt die Sound-Auswahl-Logik.
        """
        if result.status == "win":
            return None # Announcer sagt "Game shot"
        if result.status == "bust":
            return None # Announcer sagt "Bust"
            
        # Standard-Treffer-Sound
        hit_sounds = {"Miss": "miss"}
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
                "game_mode": self.options.name,
                "win": (p == winner),
                "all_throws_coords": all_coords,
            }
            if self.options.name in ("301", "501", "701"):
                stats_data["average"] = p.get_average()
                stats_data["checkout_percentage"] = p.get_checkout_percentage()
                stats_data["highest_finish"] = p.stats.get("highest_finish", 0)

            elif self.options.name in ("Cricket", "Cut Throat", "Tactics"):
                stats_data["mpr"] = p.get_mpr()

            self.player_stats_manager.add_game_record(p.name, stats_data)

        # Highscore-Logik hier zentralisieren
        if self.highscore_manager:
            # Für X01 ist die Metrik die Anzahl der Darts
            if self.options.name in ("301", "501", "701"):
                total_darts = winner.get_total_darts_in_game()
                self.highscore_manager.add_score(self.options.name, winner.name, total_darts)
            # Für Cricket ist die Metrik die MPR # type: ignore
            elif self.options.name in ("Cricket", "Cut Throat", "Tactics"):
                mpr = winner.get_mpr()
                self.highscore_manager.add_score(self.options.name, winner.name, mpr)
            # Für Shanghai: Priorisiere frühe Shanghai-Finishes
            elif self.options.name == "Shanghai":
                if self.shanghai_finish and self.shanghai_finish_round is not None:
                    # Bonus für frühes Finish: Je früher, desto höher die Punktzahl.
                    # Addiere den aktuellen Score als Tie-Breaker.
                    score_metric = (self.options.rounds - self.shanghai_finish_round + 1) * 1000 + winner.score
                else:
                    # Wenn kein Shanghai-Finish, einfach den Endscore verwenden.
                    score_metric = winner.score
                self.highscore_manager.add_score(self.options.name, winner.name, score_metric)

    def throw(self, ring: str, segment: int, coords: tuple[float, float] | None = None) -> None:
        """
        Verarbeitet einen Wurf eines Spielers.
        Fokussiert sich auf die Aktualisierung des Spielzustands und delegiert
        die Logik und das Feedback an spezialisierte Methoden.

        Args:
            ring (str): Der getroffene Ring (z.B. "Single", "Double", "Triple", "Bull", "Bullseye", "Miss").
            segment (int): Der Zahlenwert des getroffenen Segments.
            coords (tuple[float, float] | None, optional): Die normalisierten (x, y)-Koordinaten des Wurfs für die Heatmap.
        """
        player = self.current_player()
        if not player:
            return
        
        if not self.game_view_manager:
            # Dies sollte nicht passieren, wenn der GameViewManager korrekt initialisiert wurde.
            logger.error("GameViewManager ist nicht gesetzt. Wurfverarbeitung nicht möglich.")
            return


        if len(player.throws) >= 3:
            ui_utils.show_message(
                "info",
                "Zu viele Würfe",
                "Bitte 'Weiter' klicken!",
                parent=self.game_view_manager.get_dartboard_root(), # type: ignore
            )
            # Verhindert, dass ein Dart-Bild für einen ungültigen Wurf gezeichnet wird.
            self.game_view_manager.clear_last_dart_image() # type: ignore
            return

        # Wurf protokollieren
        player.throws.append((ring, segment, coords))

        # Verarbeitung an die spezifische Spiellogik delegieren
        throw_result = self.game._handle_throw(player, ring, segment, self.players)

        # Ergebnis entpacken
        if isinstance(throw_result, tuple):
            status, message = throw_result
        else:  # Fallback für ältere Logik, die nur einen String zurückgibt
            status, message = ("win" if throw_result else "ok", throw_result)

        # Erstelle ein strukturiertes Ergebnisobjekt
        result = ThrowResult(status=status, message=message)

        # Sound bestimmen und dem Ergebnisobjekt hinzufügen (bleibt hier)
        result.sound = self._determine_sound_for_throw(result, player, ring) # type: ignore

        # UI-Feedback (Sounds, Caller, Nachrichten) über den ViewManager auslösen
        if self.game_view_manager:
            auto_close = 1000 if player.is_ai() else 0
            self.game_view_manager.display_throw_feedback(result, player, auto_close)

        # Rufe den Callback auf, um das UI-Feedback zu verarbeiten
        self.on_throw_processed(result, player)

        # On a win, stats are finalized. For X01 matches with legs/sets,
        # this is controlled by _handle_leg_win().
        if (
            result.status == "win"
            and self.winner
            and not getattr(self.game, "is_leg_set_match", False)
        ):
            # Die X01-Logik ruft _handle_leg_win, was wiederum _finalize_and_record_stats aufruft.
            self._finalize_and_record_stats(self.winner)

        # Button-Zustände nach jedem Wurf aktualisieren, damit "Weiter" und "Zurück"
        # korrekt aktiviert/deaktiviert werden.
        self.game_view_manager.update_button_states(player, self.end)

    def process_player_throw(self, x: int, y: int) -> None:
        """Verarbeitet einen Wurf, der von einem menschlichen Spieler oder der KI simuliert wurde."""
        self.game_view_manager.dartboard._process_throw_at_coords(x, y) # type: ignore

    def _handle_leg_win(self, winner: Player):
        """
        Wird von der Spiellogik (z.B. X01) aufgerufen, wenn ein Leg endet,
        um der Game-Klasse mitzuteilen, dass Statistiken finalisiert werden können.
        Die eigentliche Leg/Set-Logik befindet sich jetzt in der X01-Klasse.
        """
        # Wenn es kein Leg/Set-Match ist, ist der Leg-Gewinn der Match-Gewinn.
        if not self.game.is_leg_set_match:
            self._finalize_and_record_stats(winner)

    def to_dict(self) -> dict:
        """
        Serialisiert den kompletten Spielzustand in ein Dictionary.
        Implementiert einen Teil der Speicher-Schnittstelle.
        """
        players_data = []
        for p in self.players:
            player_dict = {
                "name": p.name,
                "id": p.id,
                "score": p.score,
                "throws": p.throws,
                "all_game_throws": p.all_game_throws,
                "turn_is_over": p.turn_is_over,
                "stats": p.stats,
                "state": p.state,
            }
            players_data.append(player_dict)

        game_state = {
            **self.options.to_dict(),
            "current_player_index": self.current,
            "round": self.round,
            "shanghai_finish": self.shanghai_finish,
            "shanghai_finish_round": self.shanghai_finish_round,
            "is_tournament_match": self.is_tournament_match,
            "players": players_data,
        }

        # Füge den Zustand für Legs & Sets hinzu, falls es sich um ein solches Match handelt.
        # Dies ist wichtig für das korrekte Laden des Spiels.
        if hasattr(self.game, "to_dict"):
            game_state.update(self.game.to_dict())
        return game_state

    def get_save_meta(self) -> dict:
        """
        Gibt die Metadaten für den Speicherdialog zurück.
        Implementiert den zweiten Teil der Speicher-Schnittstelle.
        """
        return {
            "title": "Spiel speichern unter...",
            "filetypes": SaveLoadManager.GAME_FILE_TYPES,
            "defaultextension": ".json",
            "save_type": SaveLoadManager.GAME_SAVE_TYPE,
        }
