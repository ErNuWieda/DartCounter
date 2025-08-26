import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

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
    monkeypatch.setattr('core.database_manager.shutil.copy', MagicMock())
    # Wir mocken die `exists`-Methode so, dass sie nur für die config.ini True zurückgibt
    def mock_exists(path):
        return 'config.ini' in str(path)
    monkeypatch.setattr('pathlib.Path.exists', mock_exists)
    
    mock_configparser = MagicMock()
    monkeypatch.setattr('core.database_manager.configparser.ConfigParser', mock_configparser)

    mock_config_instance = mock_configparser.return_value
    # Simuliere den Zugriff via `config['postgresql']`
    mock_config_instance.__getitem__.return_value = {'host': 'testhost', 'database': 'testdb', 'user': 'testuser', 'password': 'testpassword'}
    
    # Mock für SQLAlchemy-Engine und Session
    # Verhindere, dass die echten Migrationen im Test ausgeführt werden, was zu ImportErrors führt.
    monkeypatch.setattr('core.database_manager.DatabaseManager._run_migrations', MagicMock())

    with patch('core.database_manager.create_engine') as mock_create_engine:
        mock_engine_instance = MagicMock()
        mock_create_engine.return_value = mock_engine_instance

        mock_session_instance = MagicMock()
        # Konfiguriere den Context Manager (__enter__/__exit__) der Session
        mock_session_instance.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_session_instance.query.return_value.distinct.return_value.order_by.return_value.all.return_value = []
        mock_session_instance.query.return_value.filter_by.return_value.one_or_none.return_value = None

        # Mock für Base.metadata.create_all
        mock_base = MagicMock()
        monkeypatch.setattr('core.database_manager.Base', mock_base)

        mock_sessionmaker = MagicMock()
        mock_sessionmaker.return_value.__enter__.return_value = mock_session_instance

        # Instanziiere den DatabaseManager, was die Mocks auslöst
        db_manager = DatabaseManager()
        db_manager.Session = mock_sessionmaker

        yield db_manager, mock_engine_instance, mock_session_instance, mock_base

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
    monkeypatch.setattr('pathlib.Path.exists', MagicMock(return_value=True))
    mock_configparser = MagicMock()
    mock_config_instance = mock_configparser.return_value
    mock_config_instance.__getitem__.return_value = {'host': 'h', 'database': 'd', 'user': 'u', 'password': 'p'}
    monkeypatch.setattr('core.database_manager.configparser.ConfigParser', mock_configparser)
    
    # Simuliere einen Fehler bei create_engine
    with patch('core.database_manager.create_engine', side_effect=SQLAlchemyError("Connection failed")):
        db_manager = DatabaseManager()
        assert not db_manager.is_connected
        assert db_manager.engine is None

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
    db_manager.Session = None # Wichtig, um den Zustand zu simulieren
    
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