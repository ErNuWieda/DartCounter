import unittest
from unittest.mock import patch, MagicMock, call
import psycopg2

from core.database_manager import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    """
    Testet den DatabaseManager.
    Fokus liegt auf der korrekten Interaktion mit der Datenbank (gemockt)
    und der Logik des @db_operation Decorators.
    """

    @patch('core.database_manager.shutil.copy')
    @patch('core.database_manager.os.path.exists')
    @patch('core.database_manager.configparser.ConfigParser')
    @patch('core.database_manager.psycopg2.connect')
    def setUp(self, mock_connect, mock_configparser, mock_exists, mock_copy):
        """Setzt eine saubere Testumgebung mit gemockter DB-Verbindung auf."""
        
        # Mock für die Konfiguration
        mock_exists.return_value = True
        mock_config_instance = mock_configparser.return_value
        mock_config_instance.__getitem__.return_value = {
            'host': 'testhost', 'database': 'testdb', 'user': 'testuser', 'password': 'testpassword'
        }
        
        # Mock für die DB-Verbindung
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        # Konfiguriere den Context Manager (__enter__/__exit__) des Cursors
        self.mock_conn.cursor.return_value.__enter__.return_value = self.mock_cursor
        mock_connect.return_value = self.mock_conn

        # Instanziiere den DatabaseManager, was die Mocks auslöst
        self.db_manager = DatabaseManager()

    def test_initialization_successful(self):
        """Testet, ob bei erfolgreicher Konfiguration eine Verbindung aufgebaut wird."""
        self.assertTrue(self.db_manager.is_connected)
        self.assertIsNotNone(self.db_manager.conn)
        # Prüfen, ob die Initialisierungsmethoden aufgerufen wurden
        # Es reicht zu prüfen, ob execute überhaupt aufgerufen wurde, da die Logik komplex ist.
        self.mock_cursor.execute.assert_called()

    @patch('core.database_manager.psycopg2.connect')
    def test_initialization_connection_error(self, mock_connect):
        """Testet, ob is_connected bei einem Verbindungsfehler False ist."""
        mock_connect.side_effect = psycopg2.Error("Connection failed")
        db_manager = DatabaseManager()
        self.assertFalse(db_manager.is_connected)
        self.assertIsNone(db_manager.conn)

    def test_get_scores_calls_correct_query(self):
        """Testet, ob get_scores die korrekte SQL-Abfrage ausführt."""
        # Reset, um die Aufrufe aus setUp zu ignorieren
        self.mock_cursor.reset_mock()

        # Test für X01 (ASC)
        self.db_manager.get_scores("501")
        self.mock_cursor.execute.assert_called_with(
            "SELECT player_name, score_metric, date FROM highscores WHERE game_mode = %s ORDER BY score_metric ASC, date DESC LIMIT 10;",
            ("501",)
        )

        # Test für Cricket (DESC)
        self.db_manager.get_scores("Cricket")
        self.mock_cursor.execute.assert_called_with(
            "SELECT player_name, score_metric, date FROM highscores WHERE game_mode = %s ORDER BY score_metric DESC, date DESC LIMIT 10;",
            ("Cricket",)
        )

    def test_add_score_commits_transaction(self):
        """Testet, ob add_score einen Commit auslöst."""
        # Reset, um die Aufrufe aus setUp zu ignorieren
        self.mock_cursor.reset_mock()
        self.mock_conn.reset_mock()

        self.db_manager.add_score("501", "Tester", 99)
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.commit.assert_called_once()

    def test_db_operation_on_disconnected_db(self):
        """Testet, dass bei fehlender Verbindung keine DB-Operationen ausgeführt werden."""
        self.db_manager.is_connected = False
        
        # Reset mocks to check for new calls
        self.mock_conn.reset_mock()

        # Test read operation
        result_read = self.db_manager.get_all_profiles()
        self.assertEqual(result_read, []) # Sollte den Default-Wert zurückgeben

        # Test write operation
        result_write = self.db_manager.delete_profile("Test")
        self.assertFalse(result_write) # Sollte den Default-Wert zurückgeben

        # Es dürfen keine Cursor- oder Commit-Aufrufe stattgefunden haben
        self.mock_conn.cursor.assert_not_called()
        self.mock_conn.commit.assert_not_called()

    def test_db_operation_handles_exception_and_rolls_back(self):
        """
        Testet, ob der Decorator bei einem Fehler einen Rollback durchführt
        und den Standardwert zurückgibt.
        """
        # Reset, um die Aufrufe aus setUp zu ignorieren
        self.mock_conn.reset_mock()

        # Simuliere einen Fehler während der Ausführung
        self.mock_cursor.execute.side_effect = psycopg2.Error("Test IntegrityError")

        # Führe eine Schreiboperation aus, die fehlschlagen wird
        result = self.db_manager.add_profile("Tester", "/path", "#ff0000")

        # Überprüfe das Ergebnis
        self.assertFalse(result) # Sollte den Default-Wert False zurückgeben
        self.mock_conn.commit.assert_not_called() # Commit darf nicht aufgerufen werden
        self.mock_conn.rollback.assert_called_once() # Rollback muss aufgerufen werden

    def test_delete_profile_returns_true_on_success(self):
        """Testet, ob delete_profile bei Erfolg True zurückgibt."""
        # Reset, um die Aufrufe aus setUp zu ignorieren
        self.mock_conn.reset_mock()

        # rowcount > 0 bedeutet, dass eine Zeile gelöscht wurde
        self.mock_cursor.rowcount = 1
        result = self.db_manager.delete_profile("Existing Player")
        self.assertTrue(result)
        self.mock_conn.commit.assert_called_once()

    def test_delete_profile_returns_false_if_not_found(self):
        """Testet, ob delete_profile bei nicht gefundenem Profil False zurückgibt."""
        # Reset, um die Aufrufe aus setUp zu ignorieren
        self.mock_conn.reset_mock()

        # rowcount == 0 bedeutet, dass keine Zeile gelöscht wurde
        self.mock_cursor.rowcount = 0
        result = self.db_manager.delete_profile("Non-Existing Player")
        self.assertFalse(result)
        self.mock_conn.commit.assert_called_once()

if __name__ == '__main__':
    unittest.main(verbosity=2)