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

import configparser
import os
from datetime import date
from pathlib import Path
import shutil
import psycopg2
from psycopg2.extras import DictCursor
from .settings_manager import get_app_data_dir, get_application_root_dir

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
        
        # --- Suche nach config.ini an priorisierten Orten ---
        # 1. Im Benutzer-spezifischen Anwendungsordner (bevorzugt für installierte Version)
        user_config_path = get_app_data_dir() / 'config.ini'
        
        # 2. Im Hauptverzeichnis der Anwendung (für Entwicklung oder portable Nutzung)
        app_root_path = get_application_root_dir()
        root_config_path = app_root_path / 'config.ini'

        config_path_to_use = None
        if user_config_path.exists():
            config_path_to_use = user_config_path
            print(f"INFO: Lade Datenbank-Konfiguration von: {user_config_path}")
        elif root_config_path.exists():
            config_path_to_use = root_config_path
            print(f"INFO: Lade Datenbank-Konfiguration von: {root_config_path}")
        else:
            example_config_path = app_root_path / 'config.ini.example'
            if example_config_path.exists():
                # --- Automatische Erstellung der Konfigurationsdatei ---
                try:
                    shutil.copy(example_config_path, user_config_path)
                    config_path_to_use = user_config_path
                    print(f"INFO: Keine 'config.ini' gefunden. Eine Standard-Konfiguration wurde hier erstellt: {user_config_path}")
                    print("INFO: Bitte passen Sie diese Datei bei Bedarf an, um die Datenbankverbindung zu ermöglichen.")
                except Exception as e:
                    print(f"FEHLER: Konnte die Standard-Konfigurationsdatei nicht erstellen: {e}")
        
        if not config_path_to_use or not config_path_to_use.exists():
            print("INFO: 'config.ini' weder im Anwendungsordner noch im Benutzerverzeichnis gefunden. Datenbankfunktionen sind deaktiviert.")
            return

        config.read(config_path_to_use)

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
            self._create_game_records_table()
            self._migrate_schema()
        except (configparser.NoSectionError, KeyError, psycopg2.Error) as error:
            print(f"Fehler bei der Verbindung zur PostgreSQL-Datenbank: {error}")
            self.is_connected = False

    def _migrate_schema(self):
        """
        Prüft auf veraltete Datenbankschemata und migriert sie zur aktuellen Version.
        Dies wird benötigt, wenn sich Spaltennamen oder -typen ändern.
        """
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                # Migration von 'darts_used' (alt) zu 'score_metric' (neu)
                cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name='highscores' AND column_name='darts_used';")
                old_column_exists = cur.fetchone()

                cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name='highscores' AND column_name='score_metric';")
                new_column_exists = cur.fetchone()

                if old_column_exists and not new_column_exists:
                    print("INFO: Veraltetes Datenbankschema gefunden. Migriere 'darts_used' zu 'score_metric'.")
                    # Spalte umbenennen
                    cur.execute("ALTER TABLE highscores RENAME COLUMN darts_used TO score_metric;")
                    # Datentyp anpassen (von INT zu FLOAT für MPR)
                    cur.execute("ALTER TABLE highscores ALTER COLUMN score_metric TYPE FLOAT;")
                    self.conn.commit()
                    print("INFO: Migration erfolgreich.")

        except (Exception, psycopg2.Error) as error:
            print(f"Fehler bei der Schema-Migration: {error}")
            self.conn.rollback()

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

    def _create_game_records_table(self):
        """Erstellt die 'game_records'-Tabelle in der Datenbank, falls sie nicht existiert."""
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS game_records (
                        id SERIAL PRIMARY KEY,
                        player_name VARCHAR(100) NOT NULL,
                        game_mode VARCHAR(50) NOT NULL,
                        game_date TIMESTAMP NOT NULL,
                        is_win BOOLEAN NOT NULL,
                        average FLOAT,
                        mpr FLOAT,
                        checkout_percentage FLOAT,
                        highest_finish INT
                    );
                """)
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Erstellen der game_records Tabelle: {error}")

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
            score_metric (float): Die relevante Punktzahl (Darts für X01, MPR für Cricket).
        """
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                cur.execute("INSERT INTO highscores (game_mode, player_name, score_metric, date) VALUES (%s, %s, %s, %s);", (game_mode, player_name, score_metric, date.today()))
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Hinzufügen des Highscores: {error}")

    def add_game_record(self, player_name, game_stats):
        """Fügt einen neuen Spiel-Datensatz in die Datenbank ein."""
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                query = """
                    INSERT INTO game_records (
                        player_name, game_mode, game_date, is_win,
                        average, mpr, checkout_percentage, highest_finish
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """
                values = (
                    player_name,
                    game_stats['game_mode'],
                    game_stats['date'],
                    game_stats['win'],
                    game_stats.get('average'),
                    game_stats.get('mpr'),
                    game_stats.get('checkout_percentage'),
                    game_stats.get('highest_finish')
                )
                cur.execute(query, values)
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Hinzufügen des Spiel-Datensatzes: {error}")

    def get_all_player_names_from_records(self):
        """Gibt eine Liste einzigartiger Spielernamen aus der game_records Tabelle zurück."""
        if not self.is_connected: return []
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("SELECT DISTINCT player_name FROM game_records ORDER BY player_name;")
                return [row['player_name'] for row in cur.fetchall()]
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Abrufen der Spielernamen: {error}")
            return []

    def get_records_for_player(self, player_name):
        """Ruft alle Spiel-Datensätze für einen bestimmten Spieler ab."""
        if not self.is_connected: return []
        try:
            with self.conn.cursor(cursor_factory=DictCursor) as cur:
                query = "SELECT * FROM game_records WHERE player_name = %s ORDER BY game_date DESC;"
                cur.execute(query, (player_name,))
                return [dict(row) for row in cur.fetchall()]
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Abrufen der Spiel-Datensätze: {error}")
            return []

    def reset_game_records(self, player_name=None):
        """
        Setzt Spiel-Datensätze zurück. Entweder für einen spezifischen Spieler oder alle.

        Args:
            player_name (str, optional): Der Spieler, dessen Datensätze
                                         zurückgesetzt werden sollen. Wenn `None`,
                                         werden alle Datensätze aus der Tabelle
                                         gelöscht.
        """
        if not self.is_connected: return
        try:
            with self.conn.cursor() as cur:
                if player_name:
                    cur.execute("DELETE FROM game_records WHERE player_name = %s;", (player_name,))
                else:
                    cur.execute("DELETE FROM game_records;")
                self.conn.commit()
        except (Exception, psycopg2.Error) as error:
            print(f"Fehler beim Zurücksetzen der Spiel-Datensätze: {error}")

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

    def close_connection(self):
        """Schließt die Datenbankverbindung, falls sie offen ist."""
        if self.conn:
            self.conn.close()
            self.is_connected = False