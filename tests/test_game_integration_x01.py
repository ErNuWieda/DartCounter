import pytest
from unittest.mock import MagicMock, patch
import os
import sys
import tkinter as tk

# Füge das Hauptverzeichnis zum Python-Pfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.game import Game
from core.game_options import GameOptions

@pytest.fixture
def tk_root():
        """Erstellt eine einzige, versteckte Tk-Wurzel für alle Integrationstests in dieser Klasse."""
        root = tk.Tk()
        root.withdraw()
        yield root
        if root and root.winfo_exists():
            root.destroy()

@pytest.fixture
def game_setup(tk_root, monkeypatch):
        """
        Richtet für jeden Test eine neue Spielinstanz mit gemockten Abhängigkeiten ein.
        """
        # Wir "patchen" die zentralen UI-Utility-Funktionen, damit keine echten Fenster aufpoppen.
        mock_show_message = MagicMock()
        mock_ask_question = MagicMock()
        monkeypatch.setattr('core.game.ui_utils.show_message', mock_show_message)
        monkeypatch.setattr('core.game.ui_utils.ask_question', mock_ask_question)

        # Mocks für alle externen Abhängigkeiten erstellen
        mock_sound_manager = MagicMock()
        mock_highscore_manager = MagicMock()
        mock_player_stats_manager = MagicMock()
        mock_profile_manager = MagicMock()

        player_names = ["Alice", "Bob", "Charlie"]
        game_options = GameOptions(
            name="301",
            opt_in="Single",
            opt_out="Double",
            opt_atc="Single",
            count_to=301,
            lifes=3,
            rounds=7
        )
        
        # Wir mocken die UI-Komponenten, die von Game direkt erstellt werden
        def mock_setup_scoreboards(game_controller):
            """Simuliert die setup_scoreboards-Funktion, um jedem Spieler ein Mock-SB zuzuweisen."""
            mock_sbs = []
            for p in game_controller.players:
                mock_sb = MagicMock()
                p.sb = mock_sb # Wichtig: Die Funktion weist das SB dem Spieler zu.
                mock_sbs.append(mock_sb)
            return mock_sbs
        monkeypatch.setattr('core.game.DartBoard', MagicMock())
        monkeypatch.setattr('core.game.setup_scoreboards', mock_setup_scoreboards)

        game = Game(
                tk_root, 
                game_options, 
                player_names, 
                mock_sound_manager, 
                mock_highscore_manager, 
                mock_player_stats_manager,
                profile_manager=mock_profile_manager
            )

        # Manuelles Zuweisen von IDs, um die `leave`-Methode zuverlässig testen zu können
        game.players[0].id = 101 # Alice
        game.players[1].id = 102 # Bob
        game.players[2].id = 103 # Charlie

        yield game, mock_show_message, mock_player_stats_manager

        if game:
            game.destroy()

class TestGameWithX01:

    def test_initial_state(self, game_setup):
        """Testet den korrekten Anfangszustand des Spiels."""
        game, _, _ = game_setup
        assert game.options.name == "301"
        assert len(game.players) == 3
        assert game.current_player().name == "Alice"
        assert game.round == 1
        for player in game.players:
            assert player.score == 301

    def test_full_turn_and_next_player(self, game_setup):
        """Simuliert einen vollen Zug und einen kompletten Rundenwechsel."""
        game, _, _ = game_setup
        alice = game.current_player()
        assert alice.name == "Alice"

        # Alice wirft 3 Darts
        game.throw("Triple", 20)
        game.throw("Single", 20)
        game.throw("Single", 5)
        
        # Überprüfen, ob die echte Spiellogik den Score korrekt aktualisiert hat
        assert alice.score == 301 - 60 - 20 - 5
        assert len(alice.throws) == 3

        # Wechsel zum nächsten Spieler
        game.next_player()
        bob = game.current_player()
        assert bob.name == "Bob"
        assert game.round == 1

        # Komplette Runde durchlaufen
        game.next_player() # zu Charlie
        assert game.current_player().name == "Charlie"
        assert game.round == 1

        game.next_player() # zurück zu Alice
        assert game.current_player().name == "Alice"
        assert game.round == 2, "Nach einem vollen Durchlauf sollte eine neue Runde beginnen."

    def test_remove_player(self, game_setup):
        """Testet das Entfernen von Spielern aus dem Spiel."""
        game, mock_show_message, _ = game_setup
        # Anfangszustand: [Alice, Bob, Charlie], current=0 (Alice)
        assert len(game.players) == 3
        
        # 1. Entferne einen Spieler, der nicht am Zug ist (Charlie)
        charlie = next(p for p in game.players if p.id == 103)
        game.leave(charlie)
        assert len(game.players) == 2
        assert [p.name for p in game.players] == ["Alice", "Bob"]
        assert game.current_player().name == "Alice", "Der aktuelle Spieler sollte sich nicht ändern."

        # 2. Entferne den aktuellen Spieler (Alice)
        alice = next(p for p in game.players if p.id == 101)
        game.leave(alice)
        assert len(game.players) == 1
        assert game.players[0].name == "Bob"
        assert game.current_player().name == "Bob", "Der nächste Spieler sollte nun am Zug sein."

    def test_undo_dispatches_to_logic_handler(self, game_setup):
        """Testet, ob game.undo() den Aufruf an den Spiellogik-Handler weiterleitet."""
        game, _, _ = game_setup
        player = game.current_player()
        player.throws.append(("Triple", 20, None)) # Coords sind Teil des Tupels
        
        # Mocken der Methoden, die aufgerufen werden sollen
        game.game._handle_throw_undo = MagicMock() # Mock für die Spiellogik
        # Das Dartboard wird bereits in der Fixture gemockt und ist unter game.dartboard verfügbar
        
        game.undo()

        # Überprüfen, ob die Undo-Methode des Logik-Handlers aufgerufen wurde
        game.game._handle_throw_undo.assert_called_once_with(player, "Triple", 20, game.players)
        # Überprüfen, ob die clear-Methode des Dartboards aufgerufen wurde
        game.dartboard.clear_last_dart_image_from_canvas.assert_called_once()

    def test_undo_on_empty_turn(self, game_setup):
        """Testet, dass undo() bei einem leeren Zug keinen Fehler verursacht und den Zustand nicht ändert."""
        game, _, _ = game_setup
        alice = game.current_player()
        initial_score = alice.score
        initial_round = game.round

        # Mock die Spiellogik, da wir nur das Verhalten der Game-Klasse testen wollen
        game.game._handle_throw_undo = MagicMock()

        game.undo()

        assert alice.score == initial_score, "Der Punktestand sollte sich nicht ändern."
        assert game.current_player() == alice, "Der Spieler sollte sich nicht ändern."
        assert game.round == initial_round, "Die Runde sollte sich nicht ändern."
        game.game._handle_throw_undo.assert_not_called(), "Die Undo-Logik sollte nicht aufgerufen werden, wenn keine Würfe vorhanden sind."

    def test_undo_multiple_throws_in_turn(self, game_setup):
        """Testet das mehrmalige Rückgängigmachen von Würfen innerhalb eines Zugs."""
        game, _, _ = game_setup
        alice = game.current_player()
        alice.score = 101 # Startwert für den Test

        game.throw("Triple", 20) # -> Rest 41
        assert alice.score == 41
        game.throw("Single", 1) # -> Rest 40
        assert alice.score == 40

        game.undo() # Undo S1
        assert alice.score == 41, "Score sollte nach dem ersten Undo auf 41 zurückgesetzt werden."
        assert len(alice.throws) == 1, "Es sollte nur noch ein Wurf in der Liste sein."

        game.undo() # Undo T20
        assert alice.score == 101, "Score sollte nach dem zweiten Undo auf den Startwert zurückgesetzt werden."
        assert len(alice.throws) == 0, "Die Wurfliste sollte nach allen Undos leer sein."

    def test_stat_recording_on_win(self, game_setup):
        """Testet, ob Statistiken bei einem Sieg korrekt erfasst werden."""
        game, _, mock_player_stats_manager = game_setup
        winner = game.current_player()
        winner.score = 40 # Setup für einen Gewinnwurf
        
        # Mocken der Statistik-Methoden des Spielers für vorhersagbare Ergebnisse
        winner.get_average = MagicMock(return_value=85.5)
        winner.get_checkout_percentage = MagicMock(return_value=50.0)
        # Initialisiere die Stats mit einem vollständigen Dictionary, um KeyErrors zu vermeiden
        winner.stats = {
            'total_darts_thrown': 10, 'total_score_thrown': 855,
            'checkout_opportunities': 1, 'checkouts_successful': 0, 'highest_finish': 120
        }

        # Simuliere den Gewinnwurf
        game.throw("Double", 20)

        # Überprüfen, ob der Stats-Manager aufgerufen wurde
        mock_player_stats_manager.add_game_record.assert_called()
        
        # Überprüfen der Argumente für den Gewinner
        # Der Manager wird für alle Spieler aufgerufen, wir suchen den Aufruf für den Gewinner
        winner_call_found = False
        for call in mock_player_stats_manager.add_game_record.call_args_list:
            player_name_arg, stats_dict_arg = call.args
            if player_name_arg == winner.name:
                winner_call_found = True
                assert stats_dict_arg['win'] is True
                assert stats_dict_arg['game_mode'] == "301"
                assert stats_dict_arg['average'] == 85.5
                assert winner.stats['highest_finish'] == 40 # Der Finish wurde durch den Wurf aktualisiert
                break
        
        assert winner_call_found, "Statistikaufzeichnung für den Gewinner wurde nicht gefunden."

    def test_undo_winning_throw_resets_game_state(self, game_setup):
        """Testet, ob das Rückgängigmachen eines Gewinnwurfs den Spielzustand (end, winner) zurücksetzt."""
        game, _, _ = game_setup
        # Setup: Alice hat 40 Punkte
        alice = game.players[0]
        alice.score = 40
        
        # Aktion: Alice wirft den Gewinn-Dart (D20).
        # Dies ruft die echte X01._handle_throw-Logik auf.
        game.throw("Double", 20)
        
        # Überprüfung des Endzustands
        assert game.end, "Das Spiel sollte nach dem Gewinnwurf beendet sein."
        assert game.winner == alice, "Alice sollte die Gewinnerin sein."
        
        # Aktion: Undo
        game.undo()
        
        # Überprüfung des wiederhergestellten Zustands
        assert not game.end, "Die 'end'-Flagge sollte nach dem Undo zurückgesetzt sein."
        assert game.winner is None, "Der 'winner' sollte nach dem Undo zurückgesetzt sein."
        assert alice.score == 40, "Der Punktestand von Alice sollte wiederhergestellt sein."