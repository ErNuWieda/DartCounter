import pytest
from unittest.mock import mock_open, call, MagicMock, patch
import json
from pathlib import Path

# Klasse, die getestet wird
from core.settings_manager import SettingsManager


@pytest.fixture
def settings_manager_mocks(monkeypatch):
    """Patcht die Hilfsfunktion, um den Dateipfad zu kontrollieren und setzt das Singleton zurück."""
    # Singleton-Reset, um eine saubere Instanz für jeden Test zu gewährleisten.
    if hasattr(SettingsManager, "_instance"):
        SettingsManager._instance = None
    if hasattr(SettingsManager, "_initialized"):
        delattr(SettingsManager, "_initialized")

    # Patch für das AppData-Verzeichnis
    mock_app_data_dir = Path("/fake/appdata/dir")
    monkeypatch.setattr(
        "core.settings_manager.get_app_data_dir", lambda: mock_app_data_dir
    )

    # Patch für das Anwendungs-Root-Verzeichnis
    mock_root_dir = Path("/fake/root/dir")
    monkeypatch.setattr(
        "core.settings_manager.get_application_root_dir", lambda: mock_root_dir
    )

    return {
        "app_data_dir": mock_app_data_dir,
        "root_dir": mock_root_dir,
        "expected_filepath": mock_app_data_dir / "settings.json",
    }


class TestSettingsManager:
    """Testet die Logik zum Laden und Speichern von Anwendungseinstellungen."""

    def test_load_settings_no_file_uses_defaults(
        self, settings_manager_mocks, monkeypatch
    ):
        """Testet, ob Standardeinstellungen geladen werden, wenn keine Datei existiert."""
        mock_exists = MagicMock(return_value=False)
        monkeypatch.setattr("pathlib.Path.exists", mock_exists)

        sm = SettingsManager()
        defaults = sm._get_defaults()

        assert sm.settings == defaults
        assert sm.get("theme") == "light"
        # Prüfen, ob auf beide Pfade geprüft wurde
        assert mock_exists.call_count == 2

    def test_load_settings_with_existing_file(
        self, settings_manager_mocks, monkeypatch
    ):
        """Testet das erfolgreiche Laden aus einer existierenden Datei."""
        mock_exists = MagicMock(return_value=True)
        monkeypatch.setattr("pathlib.Path.exists", mock_exists)
        expected_filepath = settings_manager_mocks["expected_filepath"]

        mock_data = json.dumps(
            {"theme": "dark", "sound_enabled": False, "last_player_names": ["A", "B"]}
        )

        with patch(
            "builtins.open", mock_open(read_data=mock_data)
        ) as m_open:  # noqa: F821
            sm = SettingsManager()
            assert sm.get("theme") == "dark"
            assert not sm.get("sound_enabled")
            assert sm.get("last_player_names") == ["A", "B"]
            # Wir prüfen, ob die korrekte Datei geöffnet wurde. Die Anzahl der `exists`-Aufrufe ist ein Implementierungsdetail.
            m_open.assert_called_with(expected_filepath, "r", encoding="utf-8")

    def test_load_settings_with_partial_file_merges_defaults(
        self, settings_manager_mocks, monkeypatch
    ):
        """Testet, ob eine unvollständige Datei mit Standardwerten zusammengeführt wird."""
        monkeypatch.setattr("pathlib.Path.exists", MagicMock(return_value=True))
        mock_data = json.dumps(
            {"theme": "dark"}
        )  # 'sound_enabled' und 'last_player_names' fehlen

        with patch("builtins.open", mock_open(read_data=mock_data)):  # noqa: F821
            sm = SettingsManager()
            assert sm.get("theme") == "dark"  # Wert aus Datei
            assert sm.get("sound_enabled")  # Wert aus Defaults
            assert sm.get("last_player_names") is not None  # Wert aus Defaults

    def test_load_settings_with_corrupt_file_uses_defaults(
        self, settings_manager_mocks, monkeypatch
    ):
        """Testet, ob bei einer korrupten JSON-Datei auf Standardwerte zurückgegriffen wird."""
        monkeypatch.setattr("pathlib.Path.exists", MagicMock(return_value=True))
        mock_data = "this is not valid json"

        with patch("builtins.open", mock_open(read_data=mock_data)):  # noqa: F821
            sm = SettingsManager()
            defaults = sm._get_defaults()
            assert sm.settings == defaults

    def test_get_value_with_default_fallback(self, settings_manager_mocks, monkeypatch):
        """Testet die get-Methode mit einem Fallback-Standardwert."""
        # Initialisieren ohne Datei, um sicherzustellen, dass nur Defaults geladen werden
        monkeypatch.setattr("pathlib.Path.exists", MagicMock(return_value=False))
        sm = SettingsManager()

        # Annahme: 'non_existent_key' ist nicht in den Defaults
        assert sm.get("non_existent_key") is None
        assert sm.get("non_existent_key", "fallback") == "fallback"

    def test_set_and_save_settings(self, settings_manager_mocks, monkeypatch):
        """Testet das Setzen und anschließende Speichern von Einstellungen."""
        monkeypatch.setattr("pathlib.Path.exists", MagicMock(return_value=False))
        mock_mkdir = MagicMock()
        monkeypatch.setattr("pathlib.Path.mkdir", mock_mkdir)
        m_open = mock_open()
        monkeypatch.setattr("builtins.open", m_open)
        mock_json_dump = MagicMock()
        monkeypatch.setattr("json.dump", mock_json_dump)

        expected_filepath = settings_manager_mocks["expected_filepath"]
        sm = SettingsManager()

        # Werte ändern
        sm.set("theme", "dark")
        sm.set("new_setting", 123)

        # Speichern
        sm.save_settings()

        # Überprüfen, ob mkdir aufgerufen wurde
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Überprüfen, ob die Datei zum Schreiben geöffnet wurde
        m_open.assert_called_once_with(expected_filepath, "w", encoding="utf-8")

        # Überprüfen, ob json.dump mit den korrekten, aktualisierten Daten aufgerufen wurde
        assert mock_json_dump.called
        saved_data = mock_json_dump.call_args[0][0]

        assert saved_data["theme"] == "dark"
        assert saved_data["new_setting"] == 123
        assert saved_data["sound_enabled"]  # Standardwert sollte noch da sein

    def test_save_settings_creates_directory_if_not_exists(
        self, settings_manager_mocks, monkeypatch
    ):
        """Testet, ob save_settings das Verzeichnis erstellt, falls es nicht existiert."""
        monkeypatch.setattr("pathlib.Path.exists", MagicMock(return_value=False))
        mock_mkdir = MagicMock()
        monkeypatch.setattr("pathlib.Path.mkdir", mock_mkdir)
        m_open = mock_open()
        monkeypatch.setattr("builtins.open", m_open)
        mock_json_dump = MagicMock()
        monkeypatch.setattr("json.dump", mock_json_dump)

        expected_filepath = settings_manager_mocks["expected_filepath"]
        sm = SettingsManager()

        # Speichern
        sm.save_settings()

        # Überprüfen, ob versucht wurde, das Verzeichnis zu erstellen.
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

        # Überprüfen, ob die Datei trotzdem gespeichert wurde
        m_open.assert_called_once_with(expected_filepath, "w", encoding="utf-8")
        mock_json_dump.assert_called_once()
