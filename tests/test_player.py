import unittest
from unittest.mock import MagicMock

# Import the class to be tested
from core.player import Player

class TestPlayer(unittest.TestCase):
    """Testet die Statistikberechnungen der Player-Klasse."""

    def setUp(self):
        """
        Setzt eine kontrollierte Testumgebung für jeden Test auf.
        Erstellt eine Player-Instanz mit einem gemockten Game-Objekt.
        """
        # Erstelle einen Mock für die Game-Instanz, die der Player benötigt
        mock_game = MagicMock()
        mock_game.name = "501"
        mock_game.targets = [] # X01 hat keine festen Ziele

        # Erstelle die Player-Instanz, die wir testen wollen
        self.player = Player(name="TestPlayer", game=mock_game)

    def test_get_average_initial(self):
        """Testet, dass der Average am Anfang 0.0 ist."""
        self.assertEqual(self.player.get_average(), 0.0)

    def test_get_average_calculation(self):
        """Testet die korrekte Berechnung des 3-Dart-Average."""
        # Simuliere geworfene Darts und Punkte
        self.player.stats['total_darts_thrown'] = 6
        self.player.stats['total_score_thrown'] = 100

        # Erwarteter Average: (100 / 6) * 3 = 50.0
        self.assertAlmostEqual(self.player.get_average(), 50.0, places=2)

        # Weiterer Testfall
        self.player.stats['total_darts_thrown'] = 21
        self.player.stats['total_score_thrown'] = 450
        # Erwarteter Average: (450 / 21) * 3 = 64.2857...
        self.assertAlmostEqual(self.player.get_average(), 64.29, places=2)

    def test_get_checkout_percentage_initial(self):
        """Testet, dass die Checkout-Quote am Anfang 0.0 ist."""
        self.assertEqual(self.player.get_checkout_percentage(), 0.0)

    def test_get_checkout_percentage_calculation(self):
        """Testet die korrekte Berechnung der Checkout-Quote."""
        # Simuliere Checkout-Möglichkeiten und erfolgreiche Checkouts
        self.player.stats['checkout_opportunities'] = 4
        self.player.stats['checkouts_successful'] = 1

        # Erwartete Quote: (1 / 4) * 100 = 25.0%
        self.assertAlmostEqual(self.player.get_checkout_percentage(), 25.0, places=2)

    def test_get_checkout_percentage_no_success(self):
        """Testet die Checkout-Quote, wenn es Möglichkeiten, aber keine Erfolge gab."""
        self.player.stats['checkout_opportunities'] = 5
        self.player.stats['checkouts_successful'] = 0

        # Erwartete Quote: 0.0%
        self.assertEqual(self.player.get_checkout_percentage(), 0.0)

    def test_get_total_darts_in_game(self):
        """Testet die korrekte Berechnung der Gesamtzahl der im Spiel geworfenen Darts."""
        # Fall 1: Anfang des Spiels, Runde 1, 0 Würfe
        self.player.game.round = 1
        self.player.throws = []
        self.assertEqual(self.player.get_total_darts_in_game(), 0, "Sollte (1-1)*3 + 0 = 0 sein")

        # Fall 2: Mitte der Runde 1, 2 Würfe
        self.player.game.round = 1
        self.player.throws = [("T", 20), ("S", 1)]
        self.assertEqual(self.player.get_total_darts_in_game(), 2, "Sollte (1-1)*3 + 2 = 2 sein")

        # Fall 3: Anfang von Runde 5, 0 Würfe in dieser Runde
        self.player.game.round = 5
        self.player.throws = []
        self.assertEqual(self.player.get_total_darts_in_game(), 12, "Sollte (5-1)*3 + 0 = 12 sein")

        # Fall 4: Mitte von Runde 3, 1 Wurf in dieser Runde
        self.player.game.round = 3
        self.player.throws = [("D", 16)]
        self.assertEqual(self.player.get_total_darts_in_game(), 7, "Sollte (3-1)*3 + 1 = 7 sein")

    def test_get_mpr_calculation(self):
        """Testet die korrekte Berechnung der Marks Per Round (MPR)."""
        # Fall 1: Anfang des Spiels, keine Würfe, keine Marks
        self.player.game.round = 1
        self.player.throws = []
        self.player.stats['total_marks_scored'] = 0
        self.assertEqual(self.player.get_mpr(), 0.0, "MPR sollte am Anfang 0.0 sein.")

        # Fall 2: Einfacher Fall nach einer Runde
        # 5 Marks in 4 Darts (Runde 2, 1 Wurf)
        self.player.game.round = 2
        self.player.throws = [("S", 20)]
        self.player.stats['total_marks_scored'] = 5
        # Erwartete MPR: (5 / 4) * 3 = 3.75
        self.assertAlmostEqual(self.player.get_mpr(), 3.75, places=2)

        # Fall 3: Komplexerer Fall
        # 15 Marks in 11 Darts (Runde 4, 2 Würfe)
        self.player.game.round = 4
        self.player.throws = [("D", 18), ("S", 17)]
        self.player.stats['total_marks_scored'] = 15
        # Erwartete MPR: (15 / 11) * 3 = 4.0909...
        self.assertAlmostEqual(self.player.get_mpr(), 4.09, places=2)

if __name__ == '__main__':
    unittest.main(verbosity=2)