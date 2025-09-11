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
import json, logging
from sqlalchemy import create_engine, desc, asc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from alembic.config import Config
from alembic import command

from .settings_manager import get_app_data_dir, get_application_root_dir
from .db_models import Base, Highscore, PlayerProfile, GameRecord

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Verwaltet die Verbindung und alle CRUD-Operationen für die PostgreSQL-Datenbank.
    Nutzt SQLAlchemy für die Abstraktion von SQL-Abfragen.

    Die Klasse ist so konzipiert, dass sie bei Verbindungs- oder Konfigurationsfehlern
    nicht abstürzt, sondern die Datenbankfunktionen für die Sitzung deaktiviert
    und informative Meldungen auf der Konsole ausgibt.

    Attributes:
        engine (sqlalchemy.engine.Engine): Die SQLAlchemy-Engine für die DB-Verbindung.
        is_connected (bool): Ein Flag, das anzeigt, ob die Verbindung erfolgreich
                             hergestellt wurde.
    """

    def __init__(self):
        """
        Initialisiert den DatabaseManager und versucht, eine Verbindung herzustellen.

        Liest die Konfigurationsdatei, baut die Verbindung zur PostgreSQL-Datenbank
        auf und ruft die Methode zur Tabellenerstellung auf.
        """
        self.engine = None
        self.Session = None
        self.is_connected = False
        config = self._load_config()

        if config:
            self._connect_to_db(config)
            if self.is_connected:
                self._run_migrations()

    def _load_config(self):
        """Sucht und lädt die config.ini-Datei."""
        config = configparser.ConfigParser()

        # 1. Im Benutzer-spezifischen Anwendungsordner (bevorzugt für installierte Version)
        user_config_path = get_app_data_dir() / "config.ini"

        # 2. Im Hauptverzeichnis der Anwendung (für Entwicklung oder portable Nutzung)
        app_root_path = get_application_root_dir()
        root_config_path = app_root_path / "config.ini"

        config_path_to_use = None
        if user_config_path.exists():
            config_path_to_use = user_config_path
            logger.info(f"Lade Datenbank-Konfiguration von: {user_config_path}")
        elif root_config_path.exists():
            config_path_to_use = root_config_path
            logger.info(f"Lade Datenbank-Konfiguration von: {root_config_path}")
        else:
            # Fallback: Versuche, die Beispiel-Konfiguration zu kopieren
            example_config_path = app_root_path / "config.ini.example"
            if example_config_path.exists():
                try:
                    shutil.copy(example_config_path, user_config_path)
                    logger.info(
                        f"Keine 'config.ini' gefunden. Eine Standard-Konfiguration wurde hier erstellt: {user_config_path}"
                    )
                    logger.info(
                        "Bitte passen Sie diese Datei bei Bedarf an, um die Datenbankverbindung zu ermöglichen."
                    )
                    # Lese die gerade kopierte Konfigurationsdatei direkt
                    config.read(user_config_path)
                    return config
                except Exception as e:
                    logger.error(
                        f"Konnte die Standard-Konfigurationsdatei nicht erstellen: {e}",
                        exc_info=True,
                    )

        if not config_path_to_use or not config_path_to_use.exists():
            logger.info(
                "'config.ini' weder im Anwendungsordner noch im Benutzerverzeichnis gefunden. Datenbankfunktionen sind deaktiviert."
            )
            return None

        config.read(config_path_to_use)
        return config

    def _connect_to_db(self, config):
        """Baut die Datenbankverbindung basierend auf dem Konfigurationsobjekt auf."""
        if not config:
            return

        try:
            db_config = config["postgresql"]
            required_keys = ["host", "database", "user", "password"]
            if not all(key in db_config for key in required_keys):
                logger.error(
                    "'config.ini' ist unvollständig. Es fehlen Schlüssel im [postgresql] Abschnitt. Datenbankfunktionen sind deaktiviert."
                )
                return

            # SQLAlchemy Verbindungs-URL im Format: dialect+driver://user:password@host/dbname
            db_url = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
            self.engine = create_engine(db_url)

            # Teste die Verbindung, bevor wir fortfahren
            self.engine.connect()

            self.Session = sessionmaker(bind=self.engine)
            self.is_connected = True
        except (configparser.NoSectionError, KeyError, SQLAlchemyError) as error:
            logger.error(
                f"Fehler bei der Verbindung zur PostgreSQL-Datenbank: {error}",
                exc_info=True,
            )
            self.is_connected = False

    def _model_to_dict(self, model_instance):
        """Konvertiert eine SQLAlchemy-Modellinstanz in ein Dictionary."""
        return {
            c.name: getattr(model_instance, c.name)
            for c in model_instance.__table__.columns
        }

    def _run_migrations(self):
        """Führt Alembic-Migrationen aus, um die Datenbank auf den neuesten Stand zu bringen."""
        if not self.engine:
            return
        try:
            # Der Pfad zur alembic.ini relativ zum Projekt-Root
            alembic_ini_path = get_application_root_dir() / "alembic.ini"
            logger.info("Prüfe und führe Datenbank-Migrationen aus...")

            # Erstelle eine Alembic-Konfiguration und setze den Pfad zur .ini-Datei
            alembic_cfg = Config(str(alembic_ini_path))

            # Führe den 'upgrade head'-Befehl aus
            command.upgrade(alembic_cfg, "head")

            logger.info("Datenbank-Migrationen erfolgreich abgeschlossen.")
        except SQLAlchemyError as e:
            # Fängt Fehler ab, die während der Migration auftreten können
            logger.error(f"Fehler während der Datenbank-Migration: {e}", exc_info=True)
            self.is_connected = False

    def get_scores(self, game_mode):
        """
        Ruft die Top 10 Highscores für einen bestimmten Spielmodus ab.
        """
        if not self.Session:
            return []
        try:
            with self.Session() as session:
                sort_func = (
                    desc if game_mode in ("Cricket", "Cut Throat", "Tactics") else asc
                )

                results = (
                    session.query(Highscore)
                    .filter_by(game_mode=game_mode)
                    .order_by(sort_func(Highscore.score_metric), desc(Highscore.date))
                    .limit(10)
                    .all()
                )

                # Konvertiere die ORM-Objekte in Dictionaries für die Kompatibilität mit der UI
                return [
                    {
                        "player_name": r.player_name,
                        "score_metric": r.score_metric,
                        "date": r.date,
                    }
                    for r in results
                ]
        except SQLAlchemyError as e:
            logger.error(
                f"Fehler beim Abrufen der Highscores für '{game_mode}': {e}",
                exc_info=True,
            )
            return []

    def get_personal_bests_for_mode(self, game_mode: str) -> dict[str, float]:
        """
        Ruft die persönliche Bestleistung für jeden Spieler in einem bestimmten Modus ab.
        """
        if not self.Session:
            return {}

        # Bestimme die Aggregationsfunktion basierend auf dem Spielmodus
        if game_mode in ("Cricket", "Cut Throat", "Tactics"):
            agg_func = func.max(Highscore.score_metric)
        else:  # X01
            agg_func = func.min(Highscore.score_metric)

        with self.Session() as session:
            try:
                results = (
                    session.query(Highscore.player_name, agg_func)
                    .filter(Highscore.game_mode == game_mode)
                    .group_by(Highscore.player_name)
                    .all()
                )
                # Konvertiere die Ergebnisliste von Tupeln in ein Dictionary
                return {player_name: best_score for player_name, best_score in results}
            except SQLAlchemyError as e:
                logger.error(
                    f"Fehler beim Abrufen der persönlichen Bestleistungen für '{game_mode}': {e}",
                    exc_info=True,
                )
                return {}

    def add_score(self, game_mode, player_name, score_metric):
        """Fügt einen neuen Highscore-Eintrag hinzu."""
        if not self.Session:
            return
        with self.Session() as session:
            new_score = Highscore(
                game_mode=game_mode,
                player_name=player_name,
                score_metric=score_metric,
                date=date.today(),
            )
            session.add(new_score)
            session.commit()

    def add_game_record(self, player_name, game_stats):
        """Fügt einen neuen Spiel-Datensatz in die Datenbank ein."""
        if not self.Session:
            return
        with self.Session() as session:
            record = GameRecord(
                player_name=player_name,
                game_mode=game_stats["game_mode"],
                game_date=game_stats["date"],
                is_win=game_stats["win"],
                average=game_stats.get("average"),
                mpr=game_stats.get("mpr"),
                checkout_percentage=game_stats.get("checkout_percentage"),
                highest_finish=game_stats.get("highest_finish"),
                all_throws_coords=game_stats.get("all_throws_coords"),
            )
            session.add(record)
            session.commit()

    def get_all_player_names_from_records(self):
        """Gibt eine Liste einzigartiger Spielernamen aus der game_records Tabelle zurück."""
        if not self.Session:
            return []
        with self.Session() as session:
            results = (
                session.query(GameRecord.player_name)
                .distinct()
                .order_by(GameRecord.player_name)
                .all()
            )
            return [row[0] for row in results]

    def get_records_for_player(self, player_name):
        """Ruft alle Spiel-Datensätze für einen bestimmten Spieler ab."""
        if not self.Session:
            return []
        with self.Session() as session:
            results = (
                session.query(GameRecord)
                .filter_by(player_name=player_name)
                .order_by(desc(GameRecord.game_date))
                .all()
            )
            # Konvertiere in Dictionaries für UI-Kompatibilität
            return [
                {c.name: getattr(r, c.name) for c in r.__table__.columns}
                for r in results
            ]

    def reset_game_records(self, player_name=None):
        """
        Setzt Spiel-Datensätze zurück. Entweder für einen spezifischen Spieler oder alle.
        """
        if not self.Session:
            return
        with self.Session() as session:
            query = session.query(GameRecord)
            if player_name:
                query = query.filter_by(player_name=player_name)
            query.delete(synchronize_session=False)
            session.commit()

    # --- CRUD für Player Profiles ---

    def get_all_profiles(self):
        """Ruft alle Spielerprofile aus der Datenbank ab."""
        if not self.Session:
            return []
        with self.Session() as session:
            results = session.query(PlayerProfile).order_by(PlayerProfile.name).all()
            return [self._model_to_dict(r) for r in results]

    def add_profile(
        self,
        name,
        avatar_path,
        dart_color,
        is_ai=False,
        difficulty=None,
        preferred_double=None,
        accuracy_model=None,
    ):
        """Fügt ein neues Spielerprofil hinzu. Gibt True bei Erfolg zurück, False bei Fehlern (z.B. doppelter Name)."""
        if not self.Session:
            return False
        with self.Session() as session:
            try:
                new_profile = PlayerProfile(
                    name=name,
                    avatar_path=avatar_path,
                    dart_color=dart_color,
                    is_ai=is_ai,
                    difficulty=difficulty,
                    preferred_double=preferred_double,
                    accuracy_model=accuracy_model,
                )
                session.add(new_profile)
                session.commit()
                return True
            except (
                IntegrityError
            ):  # Wird bei UNIQUE-Verletzung (doppelter Name) ausgelöst
                session.rollback()
                logger.warning(
                    f"Versuch, ein Profil mit dem bereits existierenden Namen '{name}' zu erstellen."
                )
                return False
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(
                    f"Fehler beim Hinzufügen des Profils '{name}': {e}", exc_info=True
                )
                return False

    def update_profile(
        self,
        profile_id,
        new_name,
        new_avatar_path,
        new_dart_color,
        is_ai,
        difficulty,
        preferred_double,
        accuracy_model=None,
    ):
        """Aktualisiert ein bestehendes Spielerprofil. Gibt True bei Erfolg zurück."""
        if not self.Session:
            return False
        with self.Session() as session:
            try:
                profile = (
                    session.query(PlayerProfile).filter_by(id=profile_id).one_or_none()
                )
                if profile:
                    profile.name = new_name
                    profile.avatar_path = new_avatar_path
                    profile.dart_color = new_dart_color
                    profile.is_ai = is_ai
                    profile.difficulty = difficulty
                    profile.preferred_double = preferred_double
                    profile.accuracy_model = accuracy_model
                    session.commit()
                    return True
                return False
            except IntegrityError:
                session.rollback()
                logger.warning(
                    f"Versuch, ein Profil auf einen bereits existierenden Namen '{new_name}' zu aktualisieren."
                )
                return False
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(
                    f"Fehler beim Aktualisieren des Profils ID {profile_id}: {e}",
                    exc_info=True,
                )
                return False

    def update_profile_accuracy_model(self, player_name: str, model: dict) -> bool:
        """Aktualisiert nur das Genauigkeitsmodell eines Profils."""
        if not self.Session:
            return False
        with self.Session() as session:
            try:
                profile = (
                    session.query(PlayerProfile)
                    .filter_by(name=player_name)
                    .one_or_none()
                )
                if profile:
                    profile.accuracy_model = model
                    session.commit()
                    return True
                logger.warning(
                    f"Konnte Genauigkeitsmodell nicht speichern: Profil '{player_name}' nicht gefunden."
                )
                return False
            except SQLAlchemyError as e:
                session.rollback()
                logger.error(
                    f"Fehler beim Speichern des Genauigkeitsmodells für '{player_name}': {e}",
                    exc_info=True,
                )
                return False

    def delete_profile(self, profile_name):
        """Löscht ein Spielerprofil aus der Datenbank anhand seines Namens."""
        if not self.Session:
            return False
        with self.Session() as session:
            profile = (
                session.query(PlayerProfile).filter_by(name=profile_name).one_or_none()
            )
            if profile:
                session.delete(profile)
                session.commit()
                return True
            return False

    def reset_scores(self, game_mode=None):
        """Setzt Highscores zurück. Entweder für einen spezifischen Modus oder alle."""
        if not self.Session:
            return
        with self.Session() as session:
            query = session.query(Highscore)
            if game_mode:
                query = query.filter_by(game_mode=game_mode)
            query.delete(synchronize_session=False)
            session.commit()

    def close_connection(self):
        """Schließt die Datenbankverbindung, falls sie offen ist."""
        if self.engine:
            self.engine.dispose()
            self.is_connected = False
