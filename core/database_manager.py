import configparser
import os
from datetime import date
import psycopg2
from psycopg2.extras import DictCursor

class DatabaseManager:
    """
    Verwaltet die Verbindung und alle CRUD-Operationen für die PostgreSQL-Datenbank.

    Diese Klasse kapselt die gesamte Datenbanklogik. Sie ist verantwortlich für:
    - Das sichere Einlesen der Verbindungsdaten aus der `config.ini`.
    - Den Aufbau und das Schließen der Datenbankverbindung.
    - Die Erstellung der `highscores`-Tabelle, falls diese nicht existiert.
    - Das Abfragen, Hinzufügen und Löschen von Highscore-Einträgen.

    Die Klasse ist so konzipiert, dass sie bei Verbindungs- oder Konfigurationsfehlern
    nicht abstürzt, sondern die Datenbankfunktionen für die Sitzung deaktiviert
    und informative Meldungen auf der Konsole ausgibt.

    Attributes:
        conn (psycopg2.connection): Das aktive Verbindungsobjekt zur Datenbank.
        is_connected (bool): Ein Flag, das anzeigt, ob die Verbindung erfolgreich
                             hergestellt wurde.
    """
    def __init__(self):
        """
        Initialisiert den DatabaseManager und versucht, eine Verbindung herzustellen.

        Liest die Konfigurationsdatei, baut die Verbindung zur PostgreSQL-Datenbank
        auf und ruft die Methode zur Tabellenerstellung auf.
        """
        self.conn = None
        self.is_connected = False
        
        config = configparser.ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')

        if not os.path.exists(config_path):
            print("INFO: 'config.ini' nicht gefunden. Datenbankfunktionen (Highscores) sind deaktiviert.")
            return

        config.read(config_path)

        try:
            db_config = config['postgresql']
            required_keys = ['host', 'database', 'user', 'password']
            if not all(key in db_config for key in required_keys):
                print("FEHLER: 'config.ini' ist unvollständig. Es fehlen Schlüssel im [postgresql] Abschnitt. Datenbankfunktionen sind deaktiviert.")
                return

            self.conn = psycopg2.connect(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            self.is_connected = True
            self._create_table()
        except (configparser.NoSectionError, KeyError, psycopg2.Error) as error:
            print(f"Fehler bei der Verbindung zur PostgreSQL-Datenbank: {error}")
            self.is_connected = False

    def _create_table(self):
        """
        Erstellt die 'highscores'-Tabelle in der Datenbank, falls sie nicht existiert.

        Diese Methode stellt sicher, dass die notwendige Tabellenstruktur für die
        Speicherung der Highscores vorhanden ist. Die `CREATE TABLE IF NOT EXISTS`-
        Anweisung sorgt dafür, dass die Operation idempotent ist und bei
        wiederholten Aufrufen keine Fehler verursacht.
        """
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS highscores (
                        id SERIAL PRIMARY KEY,
                        game_mode VARCHAR(50) NOT NULL,
                        player_name VARCHAR(100) NOT NULL,
                        score_metric FLOAT NOT NULL,
                        date DATE NOT NULL
                    );
                """)
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Erstellen der Tabelle: {error}")

    def get_scores(self, game_mode):
        """
        Ruft die Top 10 Highscores für einen bestimmten Spielmodus ab.

        Args:
            game_mode (str): Der Spielmodus (z.B. "301", "501"), für den die
                             Highscores abgerufen werden sollen.

        Returns:
            list[dict]: Eine Liste von Dictionaries, wobei jedes Dictionary einen
                        Highscore-Eintrag repräsentiert. Gibt eine leere Liste zurück bei Fehlern.
        """
        if not self.is_connected: return []
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                # Cricket/Tactics: Höherer Score ist besser (DESC)
                # X01: Niedrigerer Score ist besser (ASC)
                sort_order = "DESC" if game_mode in ("Cricket", "Cut Throat", "Tactics") else "ASC"
                # Die f-string-Nutzung ist hier sicher, da sort_order aus einer festen Logik stammt und nicht von Benutzereingaben.
                query = f"SELECT player_name, score_metric, date FROM highscores WHERE game_mode = %s ORDER BY score_metric {sort_order}, date DESC LIMIT 10;"
                cur.execute(query, (game_mode,))
                return [dict(row) for row in cur.fetchall()]
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Abrufen der Highscores: {error}")
            return []

    def add_score(self, game_mode, player_name, score_metric):
        """
        Fügt einen neuen Highscore-Eintrag in die Datenbank ein.

        Args:
            game_mode (str): Der Spielmodus des Eintrags.
            player_name (str): Der Name des Spielers.
            darts_used (int): Die Anzahl der benötigten Darts.
        """
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                cur.execute("INSERT INTO highscores (game_mode, player_name, score_metric, date) VALUES (%s, %s, %s, %s);", (game_mode, player_name, score_metric, date.today()))
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Hinzufügen des Highscores: {error}")

    def reset_scores(self, game_mode=None):
        """
        Setzt Highscores zurück. Entweder für einen spezifischen Modus oder alle.

        Args:
            game_mode (str, optional): Der Spielmodus, dessen Highscores
                                       zurückgesetzt werden sollen. Wenn `None`,
                                       werden alle Highscores aus der Tabelle
                                       gelöscht.
        """
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                if game_mode:
                    cur.execute("DELETE FROM highscores WHERE game_mode = %s;", (game_mode,))
                else:
                    cur.execute("DELETE FROM highscores;")
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Zurücksetzen der Highscores: {error}")

    def __del__(self):
        """
        Destruktor, der sicherstellt, dass die Datenbankverbindung geschlossen wird,
        wenn die Instanz des DatabaseManagers zerstört wird.
        """
        if self.conn:
            self.conn.close()