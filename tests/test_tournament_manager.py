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

        # Wir definieren eine erwartete Struktur für den Turnierbaum.
        # Eine Liste von Runden, wobei jede Runde eine Liste von Matches ist.
        # Ein Match ist ein Dictionary.
        expected_round1 = [
            {'player1': 'Alice', 'player2': 'Bob', 'winner': None},
            {'player1': 'Charlie', 'player2': 'David', 'winner': None}
        ]
        
        # Diese Asserts werden fehlschlagen, bis die Logik implementiert ist.
        self.assertIn('rounds', tm.bracket)
        self.assertEqual(len(tm.bracket['rounds']), 1, "Anfangs sollte nur die erste Runde existieren.")
        self.assertEqual(tm.bracket['rounds'][0], expected_round1)

    def test_initialization_with_three_players_creates_bye(self):
        """
        Testet, ob bei 3 Spielern ein Freilos (Bye) korrekt erstellt wird.
        """
        players = ["Alice", "Bob", "Charlie"]
        tm = TournamentManager(player_names=players, game_mode="501")

        # Erwartete Struktur: Ein reguläres Match und ein Freilos.
        # Der Spieler mit dem Freilos ist automatisch der Gewinner dieses "Matches".
        expected_round1 = [
            {'player1': 'Alice', 'player2': 'Bob', 'winner': None},
            {'player1': 'Charlie', 'player2': 'BYE', 'winner': 'Charlie'}
        ]

        self.assertIn('rounds', tm.bracket)
        self.assertEqual(len(tm.bracket['rounds']), 1)
        self.assertEqual(tm.bracket['rounds'][0], expected_round1)

    def test_get_next_match_returns_first_unplayed_match(self):
        """Testet, ob get_next_match das erste ungespielte Match zurückgibt."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")

        next_match = tm.get_next_match()

        self.assertIsNotNone(next_match)
        self.assertEqual(next_match['player1'], 'Alice')
        self.assertEqual(next_match['player2'], 'Bob')

    def test_get_next_match_skips_played_match(self):
        """Testet, ob get_next_match ein bereits gespieltes Match überspringt."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")

        # Simuliere, dass das erste Match bereits gespielt wurde
        tm.bracket['rounds'][0][0]['winner'] = 'Alice'

        next_match = tm.get_next_match()

        self.assertIsNotNone(next_match)
        self.assertEqual(next_match['player1'], 'Charlie')
        self.assertEqual(next_match['player2'], 'David')

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
        
        # Finde das erste Match
        match_to_play = tm.get_next_match()
        self.assertEqual(match_to_play['player1'], 'Alice')

        # Zeichne den Gewinner auf
        tm.record_match_winner(match_to_play, 'Alice')

        # Überprüfe, ob der Gewinner im ursprünglichen Bracket-Dictionary gesetzt wurde
        self.assertEqual(tm.bracket['rounds'][0][0]['winner'], 'Alice')

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
        round1 = tm.bracket['rounds'][0]
        round1[0]['winner'] = 'Alice'  # Alice schlägt Bob
        round1[1]['winner'] = 'David'  # David schlägt Charlie

        # Führe die zu testende Methode aus
        tm.advance_to_next_round()

        # Überprüfe das Ergebnis
        self.assertEqual(len(tm.bracket['rounds']), 2, "Es sollte jetzt zwei Runden im Bracket geben.")
        
        expected_round2 = [
            {'player1': 'Alice', 'player2': 'David', 'winner': None}
        ]
        self.assertEqual(tm.bracket['rounds'][1], expected_round2, "Die zweite Runde sollte die korrekten Gewinner-Paarungen enthalten.")

    def test_advance_to_next_round_does_nothing_if_round_not_finished(self):
        """Testet, dass nichts passiert, wenn die aktuelle Runde noch nicht beendet ist."""
        players = ["Alice", "Bob", "Charlie", "David"]
        tm = TournamentManager(player_names=players, game_mode="501")

        tm.bracket['rounds'][0][0]['winner'] = 'Alice' # Nur ein Match ist beendet
        tm.advance_to_next_round()
        self.assertEqual(len(tm.bracket['rounds']), 1, "Es sollte keine neue Runde hinzugefügt worden sein.")

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
        round1 = tm.bracket['rounds'][0]
        tm.record_match_winner(round1[0], 'Alice')
        tm.record_match_winner(round1[1], 'David')
        
        # Nächste Runde generieren
        tm.advance_to_next_round()
        self.assertEqual(len(tm.bracket['rounds']), 2)

        # Finale
        final_match = tm.get_next_match()
        tm.record_match_winner(final_match, 'David')

        # Turnier beenden (letzter Aufruf von advance_to_next_round setzt den Gewinner)
        tm.advance_to_next_round()

        self.assertEqual(tm.get_tournament_winner(), 'David')
        self.assertTrue(tm.is_finished)

    def test_advance_to_next_round_with_bye(self):
        """Testet, ob ein Spieler mit einem Freilos korrekt in die nächste Runde kommt."""
        players = ["Alice", "Bob", "Charlie"]
        tm = TournamentManager(player_names=players, game_mode="501")

        # Runde 1: Alice vs Bob, Charlie hat Freilos
        # Das Freilos-Match sollte bereits einen Gewinner haben.
        self.assertEqual(tm.bracket['rounds'][0][1]['winner'], 'Charlie')

        # Simuliere das Ende des regulären Matches
        match1 = tm.get_next_match() # Alice vs Bob
        tm.record_match_winner(match1, 'Alice')

        # Führe die zu testende Methode aus
        tm.advance_to_next_round()

        # Überprüfe das Ergebnis
        self.assertEqual(len(tm.bracket['rounds']), 2)
        expected_round2 = [
            {'player1': 'Alice', 'player2': 'Charlie', 'winner': None}
        ]
        self.assertEqual(tm.bracket['rounds'][1], expected_round2)

    def test_serialization_to_and_from_dict(self):
        """Testet, ob der Manager-Zustand korrekt serialisiert und deserialisiert werden kann."""
        players = ["Alice", "Bob", "Charlie", "David"]
        game_options = {'opt_out': 'Double'}
        tm_original = TournamentManager(player_names=players, game_mode="501", game_options=game_options)

        # Simuliere einen Spielverlauf
        match1 = tm_original.get_next_match()
        tm_original.record_match_winner(match1, "Alice")

        # Serialisieren und Deserialisieren
        state_dict = tm_original.to_dict()
        tm_rehydrated = TournamentManager.from_dict(state_dict)

        # Überprüfen, ob der Zustand identisch ist
        self.assertEqual(tm_rehydrated.to_dict(), tm_original.to_dict())

if __name__ == '__main__':
    unittest.main(verbosity=2)