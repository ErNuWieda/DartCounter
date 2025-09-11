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


class Player:
    """
    Repräsentiert einen einzelnen Spieler im Spiel.

    Diese Klasse dient als Datenmodell für einen Spieler und speichert alle
    relevanten Informationen wie Name, Punktestand, Wurfhistorie und
    spielspezifische Daten (z.B. Treffer bei Cricket, Leben bei Killer).
    Sie enthält auch Methoden zur Berechnung von Statistiken.

    Attributes:
        id (int): Eine klassenweite, eindeutige ID für jeden Spieler.
        name (str): Der Name des Spielers.
        game (Game): Eine Referenz auf die übergeordnete Spielinstanz.
        score (int): Der aktuelle Punktestand des Spielers.
        throws (list[tuple]): Eine Liste der Würfe in der aktuellen Runde.
        hits (dict): Ein Dictionary, das Treffer für zielbasierte Spiele speichert.
        stats (dict): Ein Dictionary zur Speicherung von Leistungsstatistiken.
        sb (ScoreBoard): Eine Referenz auf die zugehörige Scoreboard-UI-Instanz.
    """

    id = 1
    # Ein Dictionary, das die Standardwerte für alle Statistiken enthält.
    # Dies macht die __init__-Methode übersichtlicher.
    INITIAL_STATS = {
        "total_darts_thrown": 0,
        "total_score_thrown": 0,
        "checkout_opportunities": 0,
        "checkouts_successful": 0,
        "highest_finish": 0,
        "total_marks_scored": 0,
        "successful_finishes": [],
    }

    # Ein Dictionary, das die Standardwerte für alle spielspezifischen
    # Zustands-Attribute enthält. Dies zentralisiert die Initialisierung und
    # macht sie wartbarer (DRY-Prinzip).
    INITIAL_STATE = {
        "hits": {},
        "life_segment": "",
        "can_kill": False,
        "next_target": None,
        "has_opened": False,
    }

    # Das Set der Zustandsschlüssel wird nun direkt aus dem Dictionary abgeleitet.
    STATE_KEYS = set(INITIAL_STATE.keys())

    def __init__(self, name, game, profile=None):
        """
        Initialisiert eine neue Spielerinstanz.

        Setzt die grundlegenden Attribute und initialisiert spielspezifische
        Werte basierend auf dem Namen des Spiels, das in der `game`-Instanz
        definiert ist.

        Args:
            name (str): Der Name des Spielers.
            game (Game): Die Instanz des laufenden Spiels.
            profile (PlayerProfile, optional): Das zugehörige Spielerprofil. Defaults to None.
        """
        self.name = name  # type: ignore
        self.game_name = game.options.name
        self.profile = profile
        self.score = 0
        self.game = game
        self.targets = self.game.targets  # type: ignore

        # State- und Statistik-Dictionaries aus den Klassenvorlagen initialisieren
        self.state = self.INITIAL_STATE.copy()
        self.stats = self.INITIAL_STATS.copy()

        # Eindeutige ID zuweisen und den Zähler erhöhen
        self.id = Player.id
        Player.id += 1
        self.turn_is_over = False
        self.all_game_throws = []  # Hält alle Würfe des gesamten Spiels für Statistiken
        self.throws = []
        self.sb = None  # ScoreBoard wird extern von der Game-Klasse erstellt und zugewiesen

    def is_ai(self) -> bool:
        """Gibt an, ob es sich um einen KI-Spieler handelt. Wird von AIPlayer überschrieben."""
        return False

    # --- Properties für den sicheren Zugriff auf das State-Dictionary ---
    # Dies ermöglicht den Zugriff auf spielspezifische Attribute (z.B. player.lifes)
    # und leitet ihn intern an das state-Dictionary weiter (player.state['lifes']).
    # Das macht den Code lesbarer und verhindert Fehler durch inkonsistente
    # Zugriffe nach dem Refactoring.

    @property
    def hits(self):
        return self.state.get("hits", {})

    @hits.setter
    def hits(self, value):
        self.state["hits"] = value

    @property
    def life_segment(self):
        return self.state.get("life_segment")

    @life_segment.setter
    def life_segment(self, value):
        self.state["life_segment"] = value

    @property
    def can_kill(self):
        return self.state.get("can_kill", False)

    @can_kill.setter
    def can_kill(self, value):
        self.state["can_kill"] = value

    @property
    def next_target(self):
        return self.state.get("next_target")

    @next_target.setter
    def next_target(self, value):
        self.state["next_target"] = value

    @property
    def has_opened(self):
        return self.state.get("has_opened", False)

    @has_opened.setter
    def has_opened(self, value):
        self.state["has_opened"] = value

    def leave(self):
        """
        Löst den Prozess zum Verlassen des Spiels für diesen Spieler aus.

        Delegiert den Entfernungsaufruf an die `Game`-Klasse, welche den Spieler
        aus der Liste der aktiven Spieler entfernt und das zugehörige
        Scoreboard-Fenster schließt.
        """
        self.game.leave(self)

    def reset_turn(self):
        """
        Setzt die Wurfhistorie für die aktuelle Runde zurück.
        Wird am Ende des Zugs eines Spielers aufgerufen.
        """
        self.all_game_throws.extend(self.throws)
        self.turn_is_over = False
        self.throws = []

    def reset_leg_stats(self):
        """
        Setzt die Statistiken zurück, die pro Leg gezählt werden (z.B. Average).
        Match-übergreifende Statistiken wie 'highest_finish' bleiben erhalten.
        """
        self.stats["total_darts_thrown"] = 0
        self.stats["total_score_thrown"] = 0
        self.stats["checkout_opportunities"] = 0

    def update_score_value(self, value, subtract=True):
        """
        Aktualisiert den Punktestand des Spielers und die UI-Anzeige.

        Args:
            value (int): Der Wert, um den der Punktestand geändert wird.
            subtract (bool): Wenn True, wird der Wert subtrahiert, sonst addiert.
        """
        if subtract:
            self.score -= value
        else:
            self.score += value
        self.sb.update_score(self.score)

    def get_average(self):
        """
        Berechnet und gibt den 3-Dart-Average für X01-Spiele zurück.

        Returns:
            float: Der 3-Dart-Average. Gibt 0.0 zurück, wenn noch keine Darts
                   geworfen wurden, um eine Division durch Null zu vermeiden.
        """
        if self.stats["total_darts_thrown"] == 0:
            return 0.0
        # Durchschnittlicher Punktwert pro Dart, mal 3
        return (self.stats["total_score_thrown"] / self.stats["total_darts_thrown"]) * 3

    def get_total_darts_in_game(self):
        """
        Berechnet die Gesamtzahl der in diesem Spiel vom Spieler geworfenen Darts.

        Diese Methode wird für die Anzeige in Gewinn-Nachrichten und für die
        MPR-Berechnung verwendet, wo eine rundenbasierte Zählung erforderlich ist.

        Returns:
            int: Die Gesamtzahl der geworfenen Darts.
        """
        return (self.game.round - 1) * 3 + len(self.throws)

    def get_mpr(self):
        """
        Berechnet und gibt die "Marks Per Round" (MPR) für Cricket-Spiele zurück.

        Die Berechnung basiert auf der Gesamtzahl der geworfenen Darts in der
        Partie, um eine faire "Marks pro 3 Darts"-Rate zu ermitteln.

        Returns:
            float: Die MPR. Gibt 0.0 zurück, wenn noch keine Darts geworfen
                   wurden, um eine Division durch Null zu vermeiden.
        """
        total_darts = self.get_total_darts_in_game()
        if total_darts == 0:
            return 0.0

        total_marks = self.stats.get("total_marks_scored", 0)
        return (total_marks / total_darts) * 3

    def get_checkout_percentage(self):
        """
        Berechnet die Checkout-Quote in Prozent.

        Returns:
            float: Die Erfolgsquote bei Checkout-Versuchen in Prozent. Gibt 0.0
                   zurück, wenn es keine Checkout-Möglichkeiten gab.
        """
        if self.stats["checkout_opportunities"] == 0:
            return 0.0
        return (self.stats["checkouts_successful"] / self.stats["checkout_opportunities"]) * 100
