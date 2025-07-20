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
    def __init__(self, name, game):
        """
        Initialisiert eine neue Spielerinstanz.

        Setzt die grundlegenden Attribute und initialisiert spielspezifische
        Werte basierend auf dem Namen des Spiels, das in der `game`-Instanz
        definiert ist.

        Args:
            name (str): Der Name des Spielers.
            game (Game): Die Instanz des laufenden Spiels.
        """
        self.name = name
        self.game_name = game.name
        self.hits = {}
        
        # Spielspezifische Attribute
        self.life_segment = ""
        self.lifes = game.lifes
        self.can_kill = False
        self.killer_throws = 0
        self.next_target = None
        self.score = 0
        self.game = game
        self.targets = self.game.targets
        
        # Statistik-Dictionary
        self.stats = {
            'total_darts_thrown': 0,
            'total_score_thrown': 0,
            # Statistiken für Checkout-Quote und High-Finish
            'checkout_opportunities': 0,
            'checkouts_successful': 0,
            'highest_finish': 0,
        }

        # Initialisierung basierend auf dem Spielmodus
        if self.game.name in ('301', '501', '701'):
            self.score = int(self.game.name)
        elif self.targets:
            self.next_target = self.targets[0]
            for target in self.targets:
                self.hits[target] = 0 # Initial 0 Treffer    

        # Eindeutige ID zuweisen und den Zähler erhöhen
        self.id = Player.id
        Player.id = self.id+1        
        self.has_opened = False
        self.throws = []
        self.sb = None # ScoreBoard wird extern von der Game-Klasse erstellt und zugewiesen

    def __del__(self):
        """
        Bereinigt die Ressourcen des Spielers, insbesondere das Scoreboard-Fenster.
        """
        self.sb.__del__()
        self.clear()

    def leave(self):
        """
        Löst den Prozess zum Verlassen des Spiels für diesen Spieler aus.

        Delegiert den Entfernungsaufruf an die `Game`-Klasse und zerstört
        anschließend die eigene Instanz.
        """
        self.game.leave(self.id)
        self.__del__()

    def clear(self):
        """
        Platzhalter-Methode für potenzielle zukünftige Bereinigungslogik.

        Früher wurde hier `Player.id` dekrementiert, was aber zu Problemen mit
        nicht-eindeutigen IDs führen konnte. Jetzt bleibt die Methode leer,
        um die Eindeutigkeit der IDs über die gesamte Laufzeit der Anwendung
        sicherzustellen.
        """
        pass


    def reset_turn(self):
        """
        Setzt die Wurfhistorie für die aktuelle Runde zurück.
        Wird am Ende des Zugs eines Spielers aufgerufen.
        """
        self.throws = []

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
        if self.stats['total_darts_thrown'] == 0:
            return 0.0
        # Durchschnittlicher Punktwert pro Dart, mal 3
        return (self.stats['total_score_thrown'] / self.stats['total_darts_thrown']) * 3

    def get_checkout_percentage(self):
        """
        Berechnet die Checkout-Quote in Prozent.

        Returns:
            float: Die Erfolgsquote bei Checkout-Versuchen in Prozent. Gibt 0.0
                   zurück, wenn es keine Checkout-Möglichkeiten gab.
        """
        if self.stats['checkout_opportunities'] == 0:
            return 0.0
        return (self.stats['checkouts_successful'] / self.stats['checkout_opportunities']) * 100
