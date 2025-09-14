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

import unittest
from core.checkout_calculator import CheckoutCalculator


class TestCheckoutCalculator(unittest.TestCase):
    """
    Testet die Logik des CheckoutCalculator.
    Diese Klasse ist ideal für Unit-Tests, da sie keine externen Abhängigkeiten hat.
    """

    def test_standard_checkouts_3_darts(self):
        """Testet bekannte 3-Dart-Finishes."""
        # Höchstes mögliches Finish
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(170), "T20, T20, BE")
        # Klassiker
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(167), "T20, T19, BE")
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(100), "T20, D20")
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(40), "D20")

    def test_checkouts_2_darts(self):
        """Testet Finishes, wenn nur noch 2 Darts übrig sind."""
        # 110 ist das höchste 2-Dart-Finish.
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(110, darts_left=2), "T20, BE")
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(100, darts_left=2), "T20, D20")
        # Mit 2 Darts ist 101 finishbar (T17, BE).
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(101, darts_left=2), "T17, BE")
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(40, darts_left=2), "D20")

    def test_checkouts_1_dart(self):
        """Testet Finishes mit dem letzten Dart."""
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(50, darts_left=1), "BE")
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(40, darts_left=1), "D20")
        # Ungerade Zahlen (außer Bullseye) sind nicht mit einem Dart auf Double finishbar
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(39, darts_left=1), "-")
        # 52 ist mit einem Dart nicht möglich (D26 gibt es nicht)
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(52, darts_left=1), "-")

    def test_bogey_numbers(self):
        """Testet "Bogey"-Nummern, die nicht gefinished werden können."""
        bogey_scores = [169, 168, 166, 165, 163, 162, 159]
        for score in bogey_scores:
            with self.subTest(score=score):
                self.assertEqual(
                    CheckoutCalculator.get_checkout_suggestion(score),
                    "-",
                    f"Score {score} sollte ein Bogey sein.",
                )

    def test_single_out_logic(self):
        """Testet die einfachere Logik für 'Single Out'."""
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(5, opt_out="Single"), "5")
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(57, opt_out="Single"), "T19")
        self.assertEqual(
            # Die Logik priorisiert den höchsten ersten Wurf, daher ist T20, T13 korrekt.
            CheckoutCalculator.get_checkout_suggestion(99, opt_out="Single"),
            "T20, T13",
        )

    def test_preferred_double_logic(self):
        """Testet, ob das bevorzugte Double korrekt in den Vorschlag integriert wird."""
        # Standard-Weg für 96 ist T20, D18.
        self.assertEqual(CheckoutCalculator.get_checkout_suggestion(96), "T20, D18")
        # Mit bevorzugtem Double 16 ist der Weg T16, D24 nicht möglich.
        # Der berechnete Weg ist T20, D18.
        self.assertEqual(
            CheckoutCalculator.get_checkout_suggestion(96, preferred_double=16),
            "T20, D18",
        )
        # Für 92 ist der Standardweg T20, D16.
        # Mit bevorzugtem Double 20 ist der Weg T16, D20 nicht möglich.
        # Der beste Standardweg für 92 ist T20, D16.
        self.assertEqual(
            CheckoutCalculator.get_checkout_suggestion(92, preferred_double=20),
            "T20, D16",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
