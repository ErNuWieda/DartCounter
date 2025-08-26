import pytest
from unittest.mock import MagicMock, patch

from core.game import Game
from core.game_options import GameOptions
from core.player import Player
from core.save_load_manager import SaveLoadManager

@pytest.fixture
def _x01_game_factory(game_factory):
    """
    Private factory to create an X01 game and mock its scoreboard interactions.
    This avoids code duplication in other fixtures.
    """
    def _factory(game_options, player_names):
        game = game_factory(game_options, player_names)
        # Mocken der Scoreboard-Interaktion, die für X01-Tests kritisch ist
        for p in game.players:
            mock_sb = MagicMock()
            # Simuliere, dass das Scoreboard den Score des Spielers aktualisiert
            def score_updater_factory(player_instance):
                def updater(score, subtract=True):
                    player_instance.score = player_instance.score - score if subtract else player_instance.score + score
                return updater
            mock_sb.update_score_value.side_effect = score_updater_factory(p)
            p.sb = mock_sb
        return game
    return _factory

@pytest.fixture
def x01_game(_x01_game_factory):
    """Richtet ein Standard-301-Spiel mit 3 Spielern für die Tests ein."""
    game_options = {
        "name": "301", "opt_in": "Single", "opt_out": "Double", "count_to": 301,
        "legs_to_win": 1, "sets_to_win": 1, "opt_atc": "Single", "lifes": 3, "rounds": 7
    }
    player_names = ["Alice", "Bob", "Charlie"]
    game = _x01_game_factory(game_options, player_names)
    
    # Manuelles Zuweisen von IDs, um die `leave`-Methode zuverlässig testen zu können
    game.players[0].id = 101 # Alice
    game.players[1].id = 102 # Bob
    game.players[2].id = 103 # Charlie
    
    return game

@pytest.fixture
def leg_set_game(_x01_game_factory):
    """Richtet ein 'Best of 3 Legs / Best of 3 Sets' 501-Spiel ein."""
    game_options = {
        "name": "501", "opt_in": "Single", "opt_out": "Double", "count_to": 501,
        "legs_to_win": 2, "sets_to_win": 2, "opt_atc": "Single", "lifes": 3, "rounds": 7
    }
    player_names = ["Alice", "Bob"]
    return _x01_game_factory(game_options, player_names)

class TestGameWithX01:

    def test_initial_state(self, x01_game):
        """Testet den korrekten Anfangszustand des Spiels."""
        game = x01_game
        assert game.options.name == "301"
        assert len(game.players) == 3
        assert game.current_player().name == "Alice"
        assert game.round == 1
        for player in game.players:
            assert player.score == 301

    def test_full_turn_and_next_player(self, x01_game):
        """Simuliert einen vollen Zug und einen kompletten Rundenwechsel."""
        game = x01_game
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

    def test_remove_player(self, x01_game):
        """Testet das Entfernen von Spielern aus dem Spiel."""
        game = x01_game
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

    def test_undo_dispatches_to_logic_handler(self, x01_game):
        """Testet, ob game.undo() den Aufruf an den Spiellogik-Handler weiterleitet."""
        game = x01_game
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

    def test_undo_on_empty_turn(self, x01_game):
        """Testet, dass undo() bei einem leeren Zug keinen Fehler verursacht und den Zustand nicht ändert."""
        game = x01_game
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

    def test_undo_multiple_throws_in_turn(self, x01_game):
        """Testet das mehrmalige Rückgängigmachen von Würfen innerhalb eines Zugs."""
        game = x01_game
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

    def test_stat_recording_on_win(self, x01_game):
        """Testet, ob Statistiken bei einem Sieg korrekt erfasst werden."""
        game = x01_game
        mock_player_stats_manager = game.player_stats_manager
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
                # Der höchste Finish (120) sollte erhalten bleiben, da der neue Finish (40) niedriger ist.
                assert stats_dict_arg['highest_finish'] == 120
                break
        
        assert winner_call_found, "Statistikaufzeichnung für den Gewinner wurde nicht gefunden."

    def test_undo_winning_throw_resets_game_state(self, x01_game):
        """Testet, ob das Rückgängigmachen eines Gewinnwurfs den Spielzustand (end, winner) zurücksetzt."""
        game = x01_game
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

    def test_save_and_load_leg_set_match(self, _x01_game_factory):
        """
        Tests that the state of a running "Legs & Sets" match can be correctly
        saved and restored. This is a migrated test.
        """
        game_options = {
            "name": "501", "opt_in": "Single", "opt_out": "Double", "count_to": 501,
            "legs_to_win": 2, "sets_to_win": 2, "opt_atc": "Single", "lifes": 3, "rounds": 7
        }
        player_names = ["Alice", "Bob"]
        
        # 1. Create the first game and play one leg
        game1 = _x01_game_factory(game_options, player_names)
        p1, p2 = game1.players[0], game1.players[1]
        p1.score = 40
        game1.throw("Double", 20) # Alice wins the leg

        # 2. Save the state
        saved_data = game1.to_dict()

        # 3. Create a new game instance and restore the state
        game2 = _x01_game_factory(game_options, player_names)
        SaveLoadManager.restore_game_state(game2, saved_data)
        new_p1, new_p2 = game2.players[0], game2.players[1]

        # 4. Assert that the restored state is correct
        assert game2.is_leg_set_match is True
        assert game2.player_leg_scores == {new_p1.id: 1, new_p2.id: 0}
        assert game2.player_set_scores == {new_p1.id: 0, new_p2.id: 0}
        assert game2.leg_start_player_index == 1
        assert game2.current_player() == new_p2
        assert new_p1.score == 501 and new_p2.score == 501

    def test_leave_player_in_leg_set_match_adjusts_starter(self, _x01_game_factory):
        """
        Tests that the starting player for the next leg is correctly adjusted
        when a player leaves the game. This is a migrated test.
        """
        game_options = {
            "name": "501", "opt_in": "Single", "opt_out": "Double", "count_to": 501,
            "legs_to_win": 3, "sets_to_win": 1, "opt_atc": "Single", "lifes": 3, "rounds": 7
        }
        game = _x01_game_factory(game_options, ["P1", "P2", "P3"])
        p1, p2, p3 = game.players[0], game.players[1], game.players[2]

        p1.score = 40
        game.throw("Double", 20) # P1 wins the leg

        assert game.current_player() == p2
        assert game.leg_start_player_index == 1

        game.leave(p1) # P1 leaves

        assert game.current_player().name == "P2"
        assert game.leg_start_player_index == 0

    def test_leg_stats_reset_after_win(self, leg_set_game):
        """
        Tests that leg-specific stats are reset after a leg win,
        while match stats are preserved. This is a migrated test.
        """
        game = leg_set_game
        p1, _ = game.players[0], game.players[1]

        # Simulate some throws in Leg 1 to generate stats
        p1.score = 100
        game.throw("Triple", 20) # 60
        game.throw("Single", 20) # 20
        p1.stats['highest_finish'] = 120 # Manually set a match-level stat

        assert p1.stats['total_darts_thrown'] == 2
        assert p1.stats['total_score_thrown'] == 80

        p1.score = 40
        game.throw("Double", 20) # Winning throw for the leg

        assert not game.end
        assert p1.stats['total_darts_thrown'] == 0, "Darts Thrown should be reset for the new leg"
        assert p1.stats['total_score_thrown'] == 0, "Score Thrown should be reset for the new leg" # This was the bug
        assert p1.stats['highest_finish'] == 120, "Highest Finish should be preserved across legs"

    def test_leg_and_set_win_flow(self, leg_set_game):
        """
        Simuliert ein komplettes Match im "Legs & Sets"-Modus, um den korrekten
        Ablauf und die Zustandsübergänge zu verifizieren.
        """
        game = leg_set_game
        alice, bob = game.players[0], game.players[1]

        # --- SET 1 ---
        # Leg 1: Alice gewinnt.
        game.current = 0 # Alice am Zug
        alice.score = 40
        game.throw("Double", 20)
        assert game.player_leg_scores[alice.id] == 1
        assert game.player_set_scores[alice.id] == 0
        assert game.current_player() == bob, "Bob sollte das nächste Leg beginnen."
        assert alice.score == 501 and bob.score == 501, "Scores sollten für das neue Leg zurückgesetzt werden."

        # Leg 2: Bob gewinnt.
        game.current = 1 # Bob am Zug
        bob.score = 50
        game.throw("Bullseye", 50)
        assert game.player_leg_scores[bob.id] == 1
        assert game.current_player() == alice, "Alice sollte das entscheidende Leg beginnen."

        # Leg 3: Alice gewinnt das Leg und damit Set 1.
        game.current = 0 # Alice am Zug
        alice.score = 60
        game.throw("Double", 30)
        assert game.player_set_scores[alice.id] == 1, "Alice sollte ein Set gewonnen haben."
        assert game.player_leg_scores[alice.id] == 0 and game.player_leg_scores[bob.id] == 0, "Leg-Scores sollten für das neue Set zurückgesetzt werden."
        assert game.current_player() == bob, "Bob sollte das neue Set beginnen."
        assert not game.end

        # --- SET 2 ---
        # Leg 1 & 2: Alice gewinnt beide Legs und damit das Match.
        game.current = 0; alice.score = 40; game.throw("Double", 20) # Alice gewinnt Leg 1
        game.current = 0; alice.score = 40; game.throw("Double", 20) # Alice gewinnt Leg 2

        # Finale Prüfung
        assert game.end, "Das Match sollte beendet sein, nachdem Alice zwei Sets gewonnen hat."
        assert game.winner == alice
        assert game.player_set_scores[alice.id] == 2