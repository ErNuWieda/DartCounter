import configparser
import os
from datetime import date
import psycopg2
from psycopg2.extras import DictCursor

class DatabaseManager:
    """
    Verwaltet die Verbindung und die Abfragen zur PostgreSQL-Datenbank.
    """
    def __init__(self):
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
        """Erstellt die 'highscores'-Tabelle, falls sie nicht existiert."""
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS highscores (
                        id SERIAL PRIMARY KEY,
                        game_mode VARCHAR(50) NOT NULL,
                        player_name VARCHAR(100) NOT NULL,
                        darts_used INTEGER NOT NULL,
                        date DATE NOT NULL
                    );
                """)
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Erstellen der Tabelle: {error}")

    def get_scores(self, game_mode):
        """Ruft die Top 10 Highscores für einen Spielmodus ab."""
        if not self.is_connected: return []
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT player_name, darts_used, date FROM highscores WHERE game_mode = %s ORDER BY darts_used ASC, date DESC LIMIT 10;", (game_mode,))
                return [dict(row) for row in cur.fetchall()]
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Abrufen der Highscores: {error}")
            return []

    def add_score(self, game_mode, player_name, darts_used):
        """Fügt einen neuen Highscore in die Datenbank ein."""
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                cur.execute("INSERT INTO highscores (game_mode, player_name, darts_used, date) VALUES (%s, %s, %s, %s);", (game_mode, player_name, darts_used, date.today()))
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Hinzufügen des Highscores: {error}")

    def reset_scores(self, game_mode=None):
        """Setzt Highscores zurück. Entweder für einen Modus oder alle."""
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
        if self.conn:
            self.conn.close()