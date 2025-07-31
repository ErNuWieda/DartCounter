import unittest
from unittest.mock import patch, MagicMock

# Klasse, die getestet wird
from core.tournament_manager import TournamentManager

class TestTournamentManager(unittest.TestCase):
    """
    Testet die Logik des TournamentManager.
    """

    def test_initialization_with_invalid_player_count_raises_error(self):
        """Testet, ob bei weniger als 2 Spielern ein Fehler ausgelöst wird."""
        with self.assertRaisesRegex(ValueError, "mindestens 2 Spieler"):
            TournamentManager(player_names=["Player 1"], game_mode="501")

    def test_initialization_with_four_players(self):
        """
        Testet, ob bei der Initialisierung ein Turnierbaum für die erste Runde
        erstellt wird (dieser Test wird zunächst fehlschlagen).
        """
        players = ["Alice", "Bob", "Charlie", "David"]
        # Diese Instanziierung wird fehlschlagen, bis _create_bracket implementiert ist.
        # Das ist der Kern von TDD: Schreibe einen Test, der fehlschlägt, und dann den Code,
        # um den Test zu bestehen.
        tm = TournamentManager(player_names=players, game_mode="501")

        self.assertIn('rounds', tm.bracket)
        self.assertEqual(len(tm.bracket['rounds']), 1, "Anfangs sollte nur die erste Runde existieren.")
        
        round1 = tm.bracket['rounds'][0]
        self.assertEqual(len(round1), 2, "Bei 4 Spielern sollte es 2 Matches geben.")

        # Überprüfen, ob alle Spieler genau einmal gepaart wurden
        paired_players = []
        for match in round1:
            paired_players.append(match['player1'])
            paired_players.append(match['player2'])
        
        self.assertEqual(len(paired_players), 4)
        self.assertEqual(set(paired_players), set(players), "Alle Spieler müssen in den Paarungen vorkommen.")

    def test_initialization_with_three_players_creates_bye(self):
        """
        Testet, ob bei 3 Spielern ein Freilos (Bye) korrekt erstellt wird.
        """
        players = ["Alice", "Bob", "Charlie"]
        tm = TournamentManager(player_names=players, game_mode="501")

        self.assertIn('rounds', tm.bracket)
        self.assertEqual(len(tm.bracket['rounds']), 1)
        
        round1 = tm.bracket['rounds'][0]
        self.assertEqual(len(round1), 2, "Bei 3 Spielern sollte es 2 'Matches' geben (eines davon ein Freilos).")

        # Finde das Freilos und das reguläre Match
        bye_match = next((m for m in round1 if m['player2'] == 'BYE'), None)
        regular_match = next((m for m in round1 if m['player2'] != 'BYE'), None)

        self.assertIsNotNone(bye_match, "Es sollte ein Freilos geben.")
        self.assertIsNotNone(regular_match, "Es sollte ein reguläres Match geben.")

        # Überprüfe das Freilos
        self.assertEqual(bye_match['winner'], bye_match['player1'], "Der Spieler mit Freilos ist sofort der Gewinner.")

        # Überprüfe, ob alle Spieler im Turnierbaum vorkommen
        all_players_in_bracket = {regular_match['player1'], regular_match['player2'], bye_match['player1']}
        self.assertEqual(all_players_in_bracket, set(players), "Alle Spieler müssen im Turnierbaum vorkommen.")

    def test_get_next_match_returns_first_unplayed_match(self):
        """Testet, ob get_next_match das erste ungespielte Match zurückgibt."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")

        next_match = tm.get_next_match()

        self.assertIsNotNone(next_match)
        self.assertIsNone(next_match['winner'], "Das nächste Match sollte keinen Gewinner haben.")
        self.assertIn(next_match, tm.bracket['rounds'][0], "Das zurückgegebene Match muss Teil des Brackets sein.")

    def test_get_next_match_skips_played_match(self):
        """Testet, ob get_next_match ein bereits gespieltes Match überspringt."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")

        # Simuliere, dass das erste Match im Bracket bereits gespielt wurde
        first_match_in_list = tm.bracket['rounds'][0][0]
        first_match_in_list['winner'] = first_match_in_list['player1']

        next_match = tm.get_next_match()

        self.assertIsNotNone(next_match, "Es sollte ein weiteres Match zu spielen geben.")
        self.assertNotEqual(next_match, first_match_in_list, "Das nächste Match darf nicht das bereits gespielte sein.")
        self.assertIsNone(next_match['winner'], "Das nächste Match sollte noch keinen Gewinner haben.")

    def test_get_next_match_returns_none_when_all_played(self):
        """Testet, ob get_next_match None zurückgibt, wenn alle Matches gespielt sind."""
        players = ["Alice", "Bob"]
        tm = TournamentManager(player_names=players, game_mode="501")

        # Simuliere, dass alle Matches gespielt wurden (inkl. Freilose)
        for match in tm.bracket['rounds'][0]:
            if match['winner'] is None:
                match['winner'] = match['player1'] # Setze einen beliebigen Gewinner

        next_match = tm.get_next_match()

        self.assertIsNone(next_match)

    def test_record_match_winner_updates_bracket(self):
        """Testet, ob record_match_winner den Gewinner im Turnierbaum korrekt einträgt."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")
        
        # Finde das nächste ungespielte Match
        match_to_play = tm.get_next_match()
        self.assertIsNotNone(match_to_play)

        # Zeichne den Gewinner auf
        winner_name = match_to_play['player1'] # Wähle den ersten Spieler als Gewinner
        tm.record_match_winner(match_to_play, winner_name)

        # Überprüfe, ob der Gewinner im ursprünglichen Match-Dictionary gesetzt wurde
        self.assertEqual(match_to_play['winner'], winner_name)

    def test_record_match_winner_with_invalid_winner_raises_error(self):
        """Testet, ob ein Fehler ausgelöst wird, wenn ein ungültiger Gewinnername übergeben wird."""
        players = ["Alice", "Bob"]
        tm = TournamentManager(player_names=players, game_mode="501")
        match_to_play = tm.get_next_match()

        with self.assertRaisesRegex(ValueError, "ist kein Teilnehmer dieses Matches"):
            tm.record_match_winner(match_to_play, "Zelda")

    def test_advance_to_next_round_creates_new_round_from_winners(self):
        """Testet, ob advance_to_next_round eine neue Runde mit den Gewinnern erstellt."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")

        # Simuliere das Ende der ersten Runde
        winners = []
        for match in tm.bracket['rounds'][0]:
            winner = match['player1'] # Wähle den ersten Spieler als Gewinner
            match['winner'] = winner
            winners.append(winner)

        # Führe die zu testende Methode aus
        tm.advance_to_next_round()

        # Überprüfe das Ergebnis
        self.assertEqual(len(tm.bracket['rounds']), 2, "Es sollte jetzt zwei Runden im Bracket geben.")
        round2 = tm.bracket['rounds'][1]
        self.assertEqual(len(round2), 1, "Die zweite Runde sollte ein Match haben.")
        round2_players = {round2[0]['player1'], round2[0]['player2']}
        self.assertEqual(round2_players, set(winners), "Die zweite Runde sollte die Gewinner der ersten Runde enthalten.")

    def test_advance_to_next_round_does_nothing_if_round_not_finished(self):
        """Testet, dass nichts passiert, wenn die aktuelle Runde noch nicht beendet ist."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")

        tm.bracket['rounds'][0][0]['winner'] = 'Alice' # Nur ein Match ist beendet
        
        tm.advance_to_next_round()
        
        # Mit der neuen Logik sollte eine Vorschau-Runde erstellt werden.
        self.assertEqual(len(tm.bracket['rounds']), 2, "Es sollte eine Vorschau der zweiten Runde hinzugefügt worden sein.")

    def test_get_tournament_winner_returns_none_if_not_finished(self):
        """Testet, dass get_tournament_winner None zurückgibt, solange das Turnier läuft."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")
        self.assertIsNone(tm.get_tournament_winner())
        self.assertFalse(tm.is_finished)

    def test_get_tournament_winner_returns_winner_when_finished(self):
        """Testet, dass get_tournament_winner den korrekten Sieger nach Turnierende zurückgibt."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")

        # Runde 1
        for match in tm.bracket['rounds'][0]:
            winner = match['player1']
            tm.record_match_winner(match, winner)

        # Nächste Runde generieren
        tm.advance_to_next_round()
        self.assertEqual(len(tm.bracket['rounds']), 2)

        # Finale
        final_match = tm.get_next_match()
        winner_name = final_match['player1'] # Wähle dynamisch einen Gewinner
        tm.record_match_winner(final_match, winner_name)

        # Turnier beenden (letzter Aufruf von advance_to_next_round setzt den Gewinner)
        tm.advance_to_next_round()

        self.assertEqual(tm.get_tournament_winner(), winner_name)
        self.assertTrue(tm.is_finished)

    def test_advance_to_next_round_with_bye(self):
        """Testet, ob ein Spieler mit einem Freilos korrekt in die nächste Runde kommt."""
        players = ["Alice", "Bob", "Charlie"]
        tm = TournamentManager(player_names=players, game_mode="501")

        # Finde das Freilos und das reguläre Match
        round1 = tm.bracket['rounds'][0]
        bye_match = next((m for m in round1 if m['player2'] == 'BYE'), None)
        regular_match = next((m for m in round1 if m['player2'] != 'BYE'), None)
        self.assertIsNotNone(bye_match)
        self.assertIsNotNone(regular_match)
        bye_winner = bye_match['winner']

        # Simuliere das Ende des regulären Matches
        regular_winner = regular_match['player1']
        tm.record_match_winner(regular_match, regular_winner)

        # Führe die zu testende Methode aus
        tm.advance_to_next_round()

        # Überprüfe das Ergebnis
        self.assertEqual(len(tm.bracket['rounds']), 2)
        round2_players = {tm.bracket['rounds'][1][0]['player1'], tm.bracket['rounds'][1][0]['player2']}
        self.assertEqual(round2_players, {bye_winner, regular_winner})

    def test_serialization_to_and_from_dict(self):
        """Testet, ob der Manager-Zustand korrekt serialisiert und deserialisiert werden kann."""
        players = ["Alice", "Bob", "Charlie", "David"]
        game_options = {'opt_out': 'Double'}
        tm_original = TournamentManager(player_names=players, game_mode="501", game_options=game_options)

        # Simuliere einen Spielverlauf
        match1 = tm_original.get_next_match()
        winner_name = match1['player1'] # Wähle den ersten Spieler des Matches als Gewinner
        tm_original.record_match_winner(match1, winner_name)

        # Serialisieren und Deserialisieren
        state_dict = tm_original.to_dict()
        tm_rehydrated = TournamentManager.from_dict(state_dict)

        # Überprüfen, ob der Zustand identisch ist
        self.assertEqual(tm_rehydrated.to_dict(), tm_original.to_dict())

if __name__ == '__main__':
    unittest.main(verbosity=2)