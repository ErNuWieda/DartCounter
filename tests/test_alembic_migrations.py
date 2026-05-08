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
import subprocess
from pathlib import Path
import logging
from alembic.config import Config
from alembic import command
from core.database_manager import DatabaseManager


@pytest.fixture(scope="module")
def real_db_manager():
    """
    Fixture zur Erstellung einer echten DatabaseManager-Instanz.
    Diese Fixture ist so konzipiert, dass sie in der CI mit einem Live-PostgreSQL-Dienst
    verwendet wird. Die Initialisierung des DatabaseManager ruft _run_migrations auf.
    """
    # Sicherstellen, dass das Singleton für einen sauberen Start zurückgesetzt wird
    DatabaseManager._instance = None

    # Debug-Check für CI: Existiert die Config?
    config_path = Path.cwd() / "config.ini"
    if not config_path.exists():
        pytest.skip(f"Datenbank-Tests übersprungen: config.ini nicht gefunden unter {config_path}")

    # Die Initialisierung des DatabaseManager ruft _run_migrations auf,
    # was die Alembic-Migrationen anwenden sollte.
    db_manager = DatabaseManager()

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

    try:
        result = subprocess.run(
            ["alembic", "-c", str(alembic_ini_path), "current"],
            check=True,
            capture_output=True,
            cwd=project_root,
            text=True
        )
        # Die Ausgabe von 'alembic current' sollte ' (head)' enthalten, wenn es auf dem neuesten Stand ist.
        assert "(head)" in result.stdout, f"Alembic current ist nicht auf head: {result.stdout}"
    except subprocess.CalledProcessError as e:
        pytest.fail(f"Alembic current fehlgeschlagen: {e.stderr}\n{e.stdout}")


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
    # WICHTIG: Nutze die Engine-URL des real_db_manager (zeigt auf die Test-DB)
    alembic_cfg.set_main_option("sqlalchemy.url", str(real_db_manager.engine.url))

    # 1. Sicherstellen, dass wir auf head sind
    command.upgrade(alembic_cfg, "head")

    # 2. Testdaten einfügen (ein Profil, das in der DB überleben soll)
    test_name = f"MigrationTest_{Path(__file__).stem}"
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