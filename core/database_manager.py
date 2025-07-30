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
import logging
import os
from datetime import date
from pathlib import Path
import shutil
import psycopg2
import json
from psycopg2.extras import DictCursor
from .settings_manager import get_app_data_dir, get_application_root_dir

from functools import wraps

logger = logging.getLogger(__name__)

def db_operation(write=False, default_return_value=None):
    """
    Ein Decorator, der die Standardlogik für Datenbankoperationen kapselt:
    - Prüft die Verbindung.
    - Verwaltet den Cursor und die Transaktion (commit/rollback).
    - Fängt Fehler ab und gibt einen Standardwert zurück.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.is_connected:
                # Bestimme den Rückgabewert bei fehlender Verbindung
                if default_return_value is not None: return default_return_value
                return False if write else []

            try:
                with self.conn.cursor(cursor_factory=DictCursor) as cur:
                    result = func(self, cur, *args, **kwargs)
                    if write:
                        self.conn.commit()
                    return result
            except (Exception, psycopg2.Error) as error:
                logger.error(f"Datenbankfehler in '{func.__name__}': {error}", exc_info=True)
                if write and self.conn:
                    self.conn.rollback()
                if default_return_value is not None: return default_return_value
                return False if write else []
        return wrapper
    return decorator
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
        config = self._load_config()

        if config:
            self._connect_to_db(config)

        if self.is_connected:
            self._create_tables_if_not_exist()
            self._migrate_schema()

    def _load_config(self):
        """Sucht und lädt die config.ini-Datei."""
        config = configparser.ConfigParser()

        # 1. Im Benutzer-spezifischen Anwendungsordner (bevorzugt für installierte Version)
        user_config_path = get_app_data_dir() / 'config.ini'
        
        # 2. Im Hauptverzeichnis der Anwendung (für Entwicklung oder portable Nutzung)
        app_root_path = get_application_root_dir()
        root_config_path = app_root_path / 'config.ini'

        config_path_to_use = None
        if user_config_path.exists():
            config_path_to_use = user_config_path
            logger.info(f"Lade Datenbank-Konfiguration von: {user_config_path}")
        elif root_config_path.exists():
            config_path_to_use = root_config_path
            logger.info(f"Lade Datenbank-Konfiguration von: {root_config_path}")
        else:
            example_config_path = app_root_path / 'config.ini.example'
            if example_config_path.exists():
                # --- Automatische Erstellung der Konfigurationsdatei ---
                try:
                    shutil.copy(example_config_path, user_config_path)
                    config_path_to_use = user_config_path
                    logger.info(f"Keine 'config.ini' gefunden. Eine Standard-Konfiguration wurde hier erstellt: {user_config_path}")
                    logger.info("Bitte passen Sie diese Datei bei Bedarf an, um die Datenbankverbindung zu ermöglichen.")
                except Exception as e:
                    logger.error(f"Konnte die Standard-Konfigurationsdatei nicht erstellen: {e}", exc_info=True)
        
        if not config_path_to_use or not config_path_to_use.exists():
            logger.info("'config.ini' weder im Anwendungsordner noch im Benutzerverzeichnis gefunden. Datenbankfunktionen sind deaktiviert.")
            return None

        config.read(config_path_to_use)
        return config

    def _connect_to_db(self, config):
        """Baut die Datenbankverbindung basierend auf dem Konfigurationsobjekt auf."""
        try:
            db_config = config['postgresql']
            required_keys = ['host', 'database', 'user', 'password']
            if not all(key in db_config for key in required_keys):
                logger.error("'config.ini' ist unvollständig. Es fehlen Schlüssel im [postgresql] Abschnitt. Datenbankfunktionen sind deaktiviert.")
                return

            self.conn = psycopg2.connect(
                host=db_config['host'],
                database=db_config['database'],
                user=db_config['user'],
                password=db_config['password']
            )
            self.is_connected = True
        except (configparser.NoSectionError, KeyError, psycopg2.Error) as error:
            logger.error(f"Fehler bei der Verbindung zur PostgreSQL-Datenbank: {error}", exc_info=True)
            self.is_connected = False

    def _migrate_schema(self):
        """
        Prüft auf veraltete Datenbankschemata und migriert sie zur aktuellen Version.
        Dies wird benötigt, wenn sich Spaltennamen oder -typen ändern.
        """
        # Diese Methode wird jetzt mit dem Decorator versehen, um die Logik zu kapseln
        self._perform_migration()

    @db_operation(write=True)
    def _perform_migration(self, cur):
        # Migration von 'darts_used' (alt) zu 'score_metric' (neu)
        cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name='highscores' AND column_name='darts_used';")
        if cur.fetchone():
            cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name='highscores' AND column_name='score_metric';")
            if not cur.fetchone():
                logger.info("Veraltetes Datenbankschema gefunden. Migriere 'darts_used' zu 'score_metric'.")
                cur.execute("ALTER TABLE highscores RENAME COLUMN darts_used TO score_metric;")
                cur.execute("ALTER TABLE highscores ALTER COLUMN score_metric TYPE FLOAT;")
                logger.info("Migration 'score_metric' erfolgreich.")

        # Migration für die Heatmap-Spalte
        cur.execute("SELECT 1 FROM information_schema.columns WHERE table_name='game_records' AND column_name='all_throws_coords';")
        if not cur.fetchone():
            logger.info("Datenbankschema wird erweitert. Füge Spalte 'all_throws_coords' zu 'game_records' hinzu.")
            cur.execute("ALTER TABLE game_records ADD COLUMN all_throws_coords JSONB;")
            logger.info("Migration 'all_throws_coords' erfolgreich.")

    @db_operation(write=True)
    def _create_tables_if_not_exist(self, cur):
        """Erstellt alle notwendigen Tabellen, falls sie nicht existieren."""
        cur.execute("""
            CREATE TABLE IF NOT EXISTS highscores (
                id SERIAL PRIMARY KEY,
                game_mode VARCHAR(50) NOT NULL,
                player_name VARCHAR(100) NOT NULL,
                score_metric FLOAT NOT NULL,
                date DATE NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS player_profiles (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                avatar_path TEXT,
                dart_color VARCHAR(7) NOT NULL DEFAULT '#ff0000',
                is_ai BOOLEAN DEFAULT FALSE,
                difficulty varchar(6)
            );
        """)
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
                highest_finish INT,
                all_throws_coords JSONB
            );
        """)

    @db_operation(default_return_value=[])
    def get_scores(self, cur, game_mode):
        """
        Ruft die Top 10 Highscores für einen bestimmten Spielmodus ab.

        Args:
            game_mode (str): Der Spielmodus (z.B. "301", "501"), für den die
                             Highscores abgerufen werden sollen.

        Returns:
            list[dict]: Eine Liste von Dictionaries, wobei jedes Dictionary einen
                        Highscore-Eintrag repräsentiert. Gibt eine leere Liste zurück bei Fehlern.
        """
        # Cricket/Tactics: Höherer Score ist besser (DESC)
        # X01: Niedrigerer Score ist besser (ASC)
        sort_order = "DESC" if game_mode in ("Cricket", "Cut Throat", "Tactics") else "ASC"
        # Die f-string-Nutzung ist hier sicher, da sort_order aus einer festen Logik stammt und nicht von Benutzereingaben.
        query = f"SELECT player_name, score_metric, date FROM highscores WHERE game_mode = %s ORDER BY score_metric {sort_order}, date DESC LIMIT 10;"
        cur.execute(query, (game_mode,))
        return [dict(row) for row in cur.fetchall()]

    @db_operation(write=True)
    def add_score(self, cur, game_mode, player_name, score_metric):
        """
        Fügt einen neuen Highscore-Eintrag in die Datenbank ein.
        """
        cur.execute("INSERT INTO highscores (game_mode, player_name, score_metric, date) VALUES (%s, %s, %s, %s);", (game_mode, player_name, score_metric, date.today()))

    @db_operation(write=True)
    def add_game_record(self, cur, player_name, game_stats):
        """Fügt einen neuen Spiel-Datensatz in die Datenbank ein."""
        query = """
            INSERT INTO game_records (
                player_name, game_mode, game_date, is_win,
                average, mpr, checkout_percentage, highest_finish, all_throws_coords
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        coords_json = json.dumps(game_stats.get('all_throws_coords')) if game_stats.get('all_throws_coords') else None
        values = (
            player_name,
            game_stats['game_mode'],
            game_stats['date'],
            game_stats['win'],
            game_stats.get('average'),
            game_stats.get('mpr'),
            game_stats.get('checkout_percentage'),
            game_stats.get('highest_finish'),
            coords_json
        )
        cur.execute(query, values)

    @db_operation(default_return_value=[])
    def get_all_player_names_from_records(self, cur):
        """Gibt eine Liste einzigartiger Spielernamen aus der game_records Tabelle zurück."""
        cur.execute("SELECT DISTINCT player_name FROM game_records ORDER BY player_name;")
        return [row['player_name'] for row in cur.fetchall()]

    @db_operation(default_return_value=[])
    def get_records_for_player(self, cur, player_name):
        """Ruft alle Spiel-Datensätze für einen bestimmten Spieler ab."""
        query = "SELECT * FROM game_records WHERE player_name = %s ORDER BY game_date DESC;"
        cur.execute(query, (player_name,))
        return [dict(row) for row in cur.fetchall()]

    @db_operation(write=True)
    def reset_game_records(self, cur, player_name=None):
        """
        Setzt Spiel-Datensätze zurück. Entweder für einen spezifischen Spieler oder alle.
        """
        if player_name:
            cur.execute("DELETE FROM game_records WHERE player_name = %s;", (player_name,))
        else:
            cur.execute("DELETE FROM game_records;")

    # --- CRUD für Player Profiles ---

    @db_operation(default_return_value=[])
    def get_all_profiles(self, cur):
        """Ruft alle Spielerprofile aus der Datenbank ab."""
        cur.execute("SELECT id, name, avatar_path, dart_color, is_ai, difficulty FROM player_profiles ORDER BY name;")
        return [dict(row) for row in cur.fetchall()]

    @db_operation(write=True, default_return_value=False)
    def add_profile(self, cur, name, avatar_path, dart_color, is_ai=False, difficulty=None):
        """Fügt ein neues Spielerprofil in die Datenbank ein."""
        query = "INSERT INTO player_profiles (name, avatar_path, dart_color, is_ai, difficulty) VALUES (%s, %s, %s, %s, %s);"
        cur.execute(query, (name, avatar_path, dart_color, is_ai, difficulty))
        return True # Wird nur bei Erfolg erreicht

    @db_operation(write=True, default_return_value=False)
    def update_profile(self, cur, profile_id, new_name, new_avatar_path, new_dart_color, is_ai=False, difficulty=None):
        """Aktualisiert ein bestehendes Spielerprofil in der Datenbank."""
        query = """
            UPDATE player_profiles
            SET name = %s, avatar_path = %s, dart_color = %s, is_ai = %s, difficulty = %s
            WHERE id = %s;
        """
        cur.execute(query, (new_name, new_avatar_path, new_dart_color, is_ai, difficulty, profile_id))
        return True # Wird nur bei Erfolg erreicht

    @db_operation(write=True, default_return_value=False)
    def delete_profile(self, cur, profile_name):
        """Löscht ein Spielerprofil aus der Datenbank anhand seines Namens."""
        query = "DELETE FROM player_profiles WHERE name = %s;"
        cur.execute(query, (profile_name,))
        return cur.rowcount > 0 # Gibt True zurück, wenn eine Zeile gelöscht wurde

    @db_operation(write=True)
    def reset_scores(self, cur, game_mode=None):
        """
        Setzt Highscores zurück. Entweder für einen spezifischen Modus oder alle.
        """
        if game_mode:
            cur.execute("DELETE FROM highscores WHERE game_mode = %s;", (game_mode,))
        else:
            cur.execute("DELETE FROM highscores;")

    def close_connection(self):
        """Schließt die Datenbankverbindung, falls sie offen ist."""
        if self.conn:
            self.conn.close()
            self.is_connected = False