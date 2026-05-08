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

import pytest
import sys
import time
from pathlib import Path
import logging
import logging.config
from unittest.mock import patch
from alembic.config import Config
from alembic import command
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from core.database_manager import DatabaseManager


@pytest.fixture(scope="module", autouse=True)
def protect_logging():
    """
    Verhindert, dass Alembic (via fileConfig in env.py) die globalen 
    Logging-Handler von pytest deaktiviert, was caplog-Tests zerstören würde.
    """
    with patch("logging.config.fileConfig"):
        yield

@pytest.fixture(scope="module")
def real_db_manager():
    """
    Fixture zur Erstellung einer echten DatabaseManager-Instanz.
    Diese Fixture ist so konzipiert, dass sie in der CI mit einem Live-PostgreSQL-Dienst
    verwendet wird. Die Initialisierung des DatabaseManager ruft _run_migrations auf.
    """
    # Sicherstellen, dass das Singleton für einen sauberen Start zurückgesetzt wird
    DatabaseManager._instance = None

    # Wir instanziieren den Manager und prüfen, ob er eine Config gefunden hat.
    # Die Logik für die Suche (CWD, AppData, Root) steckt im DatabaseManager selbst.
    db_manager = DatabaseManager()

    if not db_manager.is_connected:
        pytest.skip(
            "Datenbank-Tests übersprungen: Keine gültige config.ini gefunden oder "
            "keine Verbindung zur Datenbank möglich."
        )

    # Verbindung überprüfen
    assert db_manager.is_connected, "DatabaseManager sollte mit der Test-DB verbunden sein."

    yield db_manager

    # Teardown: Verbindung schließen und Singleton zurücksetzen
    db_manager.close_connection()
    DatabaseManager._instance = None


@pytest.mark.alembic_migrations
@pytest.mark.db
def test_alembic_migrations_applied(real_db_manager):
    """
    Testet, ob Alembic-Migrationen erfolgreich auf die Testdatenbank angewendet wurden
    und die Datenbank auf der 'head'-Revision ist.
    """
    # Die real_db_manager Fixture stellt bereits sicher, dass die Migrationen ausgeführt wurden.
    # Jetzt überprüfen wir, ob die Datenbank auf der 'head'-Revision ist.
    project_root = Path(__file__).parent.parent
    alembic_ini_path = project_root / "alembic.ini"

    # Alembic Konfiguration für den programmatischen Zugriff
    alembic_cfg = Config(str(alembic_ini_path))
    db_url = real_db_manager.engine.url.render_as_string(hide_password=False)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    try:
        # Programmatische Prüfung der Revision (wesentlich robuster als Output-Parsing)
        script = ScriptDirectory.from_config(alembic_cfg)
        with real_db_manager.engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            head_rev = script.get_current_head()
            
        assert current_rev == head_rev, f"Revision mismatch: DB ist auf {current_rev}, Head ist {head_rev}"
    except Exception as e:
        pytest.fail(f"Alembic Check fehlgeschlagen: {e}")


@pytest.mark.alembic_migrations
@pytest.mark.db
def test_migration_roundtrip_and_data_persistence(real_db_manager):
    """
    Verifiziert, dass Downgrades funktionieren und Daten einen 
    Upgrade-Prozess unbeschadet überstehen.
    """
    project_root = Path(__file__).parent.parent
    alembic_ini_path = project_root / "alembic.ini"
    
    # Alembic Konfiguration für den programmatischen Zugriff
    alembic_cfg = Config(str(alembic_ini_path))

    # WICHTIG: Nutze render_as_string(hide_password=False), da str(url) bei SQLAlchemy 
    # das Passwort oft mit '***' maskiert, was zu Verbindungsfehlern führt.
    db_url = real_db_manager.engine.url.render_as_string(hide_password=False)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # 1. Sicherstellen, dass wir auf head sind
    command.upgrade(alembic_cfg, "head")

    # 2. Testdaten einfügen (ein Profil, das in der DB überleben soll)
    # Nutze Zeitstempel für Eindeutigkeit, falls die DB zwischen Testläufen nicht gelöscht wird.
    test_name = f"MigrationTest_{int(time.time())}"
    success = real_db_manager.add_profile(
        name=test_name,
        avatar_path=None,
        dart_color="#00ff00"
    )
    assert success, "Konnte Testprofil vor der Migration nicht anlegen."

    # 3. Downgrade durchführen (einen Schritt zurück)
    # Dies testet, ob deine downgrade()-Methoden im Alembic-Script sauber sind.
    try:
        command.downgrade(alembic_cfg, "-1")
    except Exception as e:
        pytest.fail(f"Alembic Downgrade (-1) fehlgeschlagen: {e}")

    # 4. Wieder Upgrade auf head
    # Dies testet, ob deine upgrade()-Logik auch mit vorhandenen Daten klarkommt 
    # (wichtig für NOT NULL Constraints ohne Defaults!)
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        pytest.fail(f"Alembic Upgrade nach Downgrade fehlgeschlagen: {e}")

    # 5. Daten-Persistenz prüfen
    profiles = real_db_manager.get_all_profiles()
    profile_names = [p.name for p in profiles]
    
    assert test_name in profile_names, (
        f"Datenverlust während der Migration! Profil '{test_name}' nicht mehr gefunden."
    )