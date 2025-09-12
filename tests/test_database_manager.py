import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import configparser
from pathlib import Path
from core.database_manager import DatabaseManager
from core.db_models import Highscore, PlayerProfile

"""
Testet den DatabaseManager mit SQLAlchemy.
Fokus liegt auf der korrekten Interaktion mit der SQLAlchemy Session und Engine.
"""


@pytest.fixture
def db_manager_setup(monkeypatch):
    """Setzt eine saubere Testumgebung mit gemockter SQLAlchemy-Engine und Session auf."""
    # Mock für die Konfiguration
    monkeypatch.setattr("core.database_manager.shutil.copy", MagicMock())

    # Wir mocken die `exists`-Methode so, dass sie nur für die config.ini True zurückgibt
    def mock_exists(path):
        return "config.ini" in str(path)

    monkeypatch.setattr("pathlib.Path.exists", mock_exists)

    mock_configparser = MagicMock()
    monkeypatch.setattr("core.database_manager.configparser.ConfigParser", mock_configparser)

    mock_config_instance = mock_configparser.return_value
    # Simuliere den Zugriff via `config['postgresql']`
    mock_config_instance.__getitem__.return_value = {
        "host": "testhost",
        "database": "testdb",
        "user": "testuser",
        "password": "testpassword",
    }

    # Mock für SQLAlchemy-Engine und Session
    # Verhindere, dass die echten Migrationen im Test ausgeführt werden, was zu ImportErrors führt.
    monkeypatch.setattr("core.database_manager.DatabaseManager._run_migrations", MagicMock())

    with patch("core.database_manager.create_engine") as mock_create_engine:
        mock_engine_instance = MagicMock()
        mock_create_engine.return_value = mock_engine_instance

        mock_session_instance = MagicMock()
        # Konfiguriere den Context Manager (__enter__/__exit__) der Session
        mock_session_instance.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = (
            []
        )
        mock_session_instance.query.return_value.distinct.return_value.order_by.return_value.all.return_value = (
            []
        )
        mock_session_instance.query.return_value.filter_by.return_value.one_or_none.return_value = (
            None
        )

        # Mock für Base.metadata.create_all
        mock_base = MagicMock()
        monkeypatch.setattr("core.database_manager.Base", mock_base)

        mock_sessionmaker = MagicMock()
        mock_sessionmaker.return_value.__enter__.return_value = mock_session_instance

        # Instanziiere den DatabaseManager, was die Mocks auslöst
        db_manager = DatabaseManager()
        db_manager.Session = mock_sessionmaker

        yield db_manager, mock_engine_instance, mock_session_instance, mock_base


@pytest.fixture
def mock_logger(monkeypatch):
    """Fixture to patch the logger and allow asserting log messages."""
    mock_log = MagicMock()
    monkeypatch.setattr("core.database_manager.logger", mock_log)
    return mock_log


def reset_db_manager_singleton():
    """Setzt das Singleton-Pattern des DatabaseManager zurück."""
    if hasattr(DatabaseManager, "_instance"):
        delattr(DatabaseManager, "_instance")
    if hasattr(DatabaseManager, "_initialized"):
        delattr(DatabaseManager, "_initialized")


@pytest.fixture
def config_test_setup(monkeypatch):
    """Eine Fixture, die die gesamte Umgebung für die Konfigurations-Tests einrichtet."""
    # Wir verwenden `with` hier, um sicherzustellen, dass die Mocks nach dem Test
    # automatisch aufgeräumt werden.
    with patch("core.database_manager.configparser.ConfigParser") as MockConfigParser, patch(
        "core.database_manager.shutil.copy"
    ) as mock_shutil_copy, patch("core.database_manager.DatabaseManager._connect_to_db"):

        # 1. Setze das Singleton vor jedem Test zurück.
        reset_db_manager_singleton()

        # 2. Mocke die Pfad-Funktionen.
        mock_app_data_dir = Path("/fake/appdata/dir/DartCounter")
        mock_root_dir = Path("/fake/root/dir")
        monkeypatch.setattr("core.database_manager.get_app_data_dir", lambda: mock_app_data_dir)
        monkeypatch.setattr(
            "core.database_manager.get_application_root_dir",
            lambda: mock_root_dir,
        )

        # 3. Erstelle eine flexible Factory für `pathlib.Path.exists`.
        def mock_exists_factory(user_exists=False, root_exists=False, example_exists=False):
            user_config_path = mock_app_data_dir / "config.ini"
            root_config_path = mock_root_dir / "config.ini"
            example_config_path = mock_root_dir / "config.ini.example"

            def mock_exists(path):
                if path == user_config_path:
                    return user_exists
                if path == root_config_path:
                    return root_exists
                if path == example_config_path:
                    return example_exists
                return False

            monkeypatch.setattr("pathlib.Path.exists", mock_exists)

        # 4. Gib die Mocks zurück, die im Test selbst benötigt werden.
        yield {
            "mock_exists_factory": mock_exists_factory,
            "mock_shutil_copy": mock_shutil_copy,
            "MockConfigParser": MockConfigParser,
        }


def test_config_loading_user_config_exists(config_test_setup):
    """Szenario 1: User-Config existiert und wird gelesen."""
    mocks = config_test_setup
    mocks["mock_exists_factory"](user_exists=True)
    DatabaseManager()
    mocks["MockConfigParser"].return_value.read.assert_called_once()


def test_config_loading_root_config_exists(config_test_setup):
    """Szenario 2: Nur Root-Config existiert und wird gelesen."""
    mocks = config_test_setup
    mocks["mock_exists_factory"](root_exists=True)
    DatabaseManager()
    mocks["MockConfigParser"].return_value.read.assert_called_once()


def test_config_loading_example_config_exists(config_test_setup):
    """Szenario 3: Nur Example-Config existiert, wird kopiert und dann gelesen."""
    mocks = config_test_setup
    mocks["mock_exists_factory"](example_exists=True)
    DatabaseManager()
    mocks["mock_shutil_copy"].assert_called_once()
    mocks["MockConfigParser"].return_value.read.assert_called_once()


def test_config_loading_no_config_exists(config_test_setup):
    """Szenario 4: Keine Config-Datei existiert, nichts wird gelesen."""
    mocks = config_test_setup
    mocks["mock_exists_factory"]()
    dbm = DatabaseManager()
    assert not dbm.is_connected
    mocks["MockConfigParser"].return_value.read.assert_not_called()


def test_initialization_successful(db_manager_setup):
    """Testet, ob bei erfolgreicher Konfiguration eine Verbindung aufgebaut wird."""
    db_manager, mock_engine, _, _ = db_manager_setup
    assert db_manager.is_connected
    assert db_manager.engine is not None
    mock_engine.connect.assert_called_once()
    # Überprüfen, ob die Migrationsmethode aufgerufen wurde
    db_manager._run_migrations.assert_called_once()


def test_initialization_connection_error(monkeypatch):
    """Testet, ob is_connected bei einem Verbindungsfehler False ist."""
    # Mocks für die Konfigurationsleselogik
    monkeypatch.setattr("pathlib.Path.exists", MagicMock(return_value=True))
    mock_configparser = MagicMock()
    mock_config_instance = mock_configparser.return_value
    mock_config_instance.__getitem__.return_value = {
        "host": "h",
        "database": "d",
        "user": "u",
        "password": "p",
    }
    monkeypatch.setattr("core.database_manager.configparser.ConfigParser", mock_configparser)

    # Simuliere einen Fehler bei create_engine
    with patch(
        "core.database_manager.create_engine",
        side_effect=SQLAlchemyError("Connection failed"),
    ):
        db_manager = DatabaseManager()
        assert not db_manager.is_connected
        assert db_manager.engine is None


def test_initialization_config_key_error(monkeypatch, mock_logger):
    """Testet, ob ein Fehler in der config.ini korrekt behandelt wird."""
    monkeypatch.setattr("pathlib.Path.exists", MagicMock(return_value=True))
    mock_configparser = MagicMock()
    # Simuliere eine unvollständige Konfiguration
    mock_config_instance = mock_configparser.return_value
    mock_config_instance.__getitem__.return_value = {
        "host": "h",
        "database": "d",
    }  # user/pw fehlen
    monkeypatch.setattr("core.database_manager.configparser.ConfigParser", mock_configparser)

    db_manager = DatabaseManager()
    assert not db_manager.is_connected
    # Prüfe, ob die Fehlermeldung den erwarteten Text enthält.
    mock_logger.error.assert_called_once()
    assert "unvollständig" in mock_logger.error.call_args[0][0]


def test_get_scores_calls_correct_query(db_manager_setup):
    """Testet, ob get_scores die korrekte SQLAlchemy-Abfrage ausführt."""
    db_manager, _, mock_session, _ = db_manager_setup

    # Test für X01 (ASC)
    db_manager.get_scores("501")
    mock_session.query.assert_called_with(Highscore)
    # Die Sortierlogik ist komplexer zu mocken, aber wir können den Filter prüfen
    mock_session.query.return_value.filter_by.assert_called_with(game_mode="501")

    # Test für Cricket (DESC)
    db_manager.get_scores("Cricket")
    mock_session.query.return_value.filter_by.assert_called_with(game_mode="Cricket")


def test_add_profile_commits_transaction(db_manager_setup):
    """Testet, ob add_profile einen Commit auslöst."""
    db_manager, _, mock_session, _ = db_manager_setup
    mock_session.reset_mock()

    db_manager.add_profile("Tester", "/path", "#ff0000")
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_operation_on_disconnected_db(db_manager_setup):
    """Testet, dass bei fehlender Verbindung keine DB-Operationen ausgeführt werden."""
    db_manager, _, mock_session, _ = db_manager_setup
    db_manager.is_connected = False
    db_manager.Session = None  # Wichtig, um den Zustand zu simulieren

    # Reset mocks to check for new calls
    mock_session.reset_mock()

    # Test read operation
    result_read = db_manager.get_all_profiles()
    assert result_read == []

    # Test write operation
    result_write = db_manager.delete_profile("Test")
    assert not result_write

    # Es dürfen keine Session-Aufrufe stattgefunden haben
    mock_session.query.assert_not_called()
    mock_session.commit.assert_not_called()


def test_add_profile_handles_integrity_error(db_manager_setup):
    """
    Testet, ob bei einem IntegrityError (z.B. doppelter Name) ein Rollback
    durchgeführt und False zurückgegeben wird.
    """
    db_manager, _, mock_session, _ = db_manager_setup
    mock_session.reset_mock()

    # Simuliere einen Fehler während des Commits
    mock_session.commit.side_effect = IntegrityError("test", "test", "test")

    # Führe die Schreiboperation aus, die fehlschlagen wird
    result = db_manager.add_profile("Tester", "/path", "#ff0000")

    # Überprüfe das Ergebnis
    assert not result
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()
    mock_session.rollback.assert_called_once()


def test_delete_profile_returns_true_on_success(db_manager_setup):
    """Testet, ob delete_profile bei Erfolg True zurückgibt."""
    db_manager, _, mock_session, _ = db_manager_setup
    mock_session.reset_mock()

    # Simuliere, dass ein Profil gefunden wird
    mock_profile = PlayerProfile(name="Existing Player")
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = mock_profile

    result = db_manager.delete_profile("Existing Player")
    assert result
    mock_session.delete.assert_called_with(mock_profile)
    mock_session.commit.assert_called_once()


def test_delete_profile_returns_false_if_not_found(db_manager_setup):
    """Testet, ob delete_profile bei nicht gefundenem Profil False zurückgibt."""
    db_manager, _, mock_session, _ = db_manager_setup
    mock_session.reset_mock()

    # Simuliere, dass kein Profil gefunden wird (Standardverhalten des Mocks)
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = None

    result = db_manager.delete_profile("Non-Existing Player")
    assert not result
    mock_session.delete.assert_not_called()
    mock_session.commit.assert_not_called()


def test_update_profile_handles_integrity_error(db_manager_setup, mock_logger):
    """Testet, ob update_profile bei einem IntegrityError korrekt reagiert."""
    db_manager, _, mock_session, _ = db_manager_setup
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = MagicMock()
    mock_session.commit.side_effect = IntegrityError("test", "test", "test")

    result = db_manager.update_profile(1, "ExistingName", "/path", "#ff0000", False, None, None)

    assert not result
    mock_session.rollback.assert_called_once()
    mock_logger.warning.assert_called_once()


def test_update_profile_accuracy_model(db_manager_setup):
    """Testet das Aktualisieren des Genauigkeitsmodells."""
    db_manager, _, mock_session, _ = db_manager_setup
    mock_profile = MagicMock()
    mock_session.query.return_value.filter_by.return_value.one_or_none.return_value = mock_profile

    model_data = {"T20": {"mean_offset_x": 5}}
    result = db_manager.update_profile_accuracy_model("Tester", model_data)

    assert result
    assert mock_profile.accuracy_model == model_data
    mock_session.commit.assert_called_once()


def test_reset_game_records_for_all_players(db_manager_setup):
    """Testet das Zurücksetzen aller Spiel-Datensätze."""
    db_manager, _, mock_session, _ = db_manager_setup
    mock_query = mock_session.query.return_value

    db_manager.reset_game_records(player_name=None)

    # Sicherstellen, dass kein filter_by aufgerufen wurde
    mock_query.filter_by.assert_not_called()
    mock_query.delete.assert_called_once_with(synchronize_session=False)
    mock_session.commit.assert_called_once()
