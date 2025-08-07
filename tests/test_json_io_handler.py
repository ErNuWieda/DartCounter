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
import json
import logging
from unittest.mock import MagicMock, patch

from core.json_io_handler import JsonIOHandler

@pytest.fixture
def mock_ui_utils(monkeypatch):
    """Fixture to patch ui_utils to prevent actual dialogs from showing."""
    mock = MagicMock()
    monkeypatch.setattr('core.json_io_handler.ui_utils', mock)
    return mock

class TestJsonIOHandler:

    # --- Tests for read_json ---

    def test_read_json_success(self, tmp_path):
        """Testet das erfolgreiche Lesen einer validen JSON-Datei."""
        filepath = tmp_path / "test.json"
        test_data = {"key": "value", "number": 123}
        filepath.write_text(json.dumps(test_data), encoding='utf-8')

        data = JsonIOHandler.read_json(filepath)

        assert data == test_data

    def test_read_json_file_not_found(self, tmp_path, caplog):
        """Testet das Verhalten, wenn die Datei nicht existiert."""
        filepath = tmp_path / "non_existent.json"
        
        with caplog.at_level(logging.INFO):
            data = JsonIOHandler.read_json(filepath)

        assert data is None
        assert f"JSON-Datei nicht gefunden unter: {filepath}" in caplog.text

    def test_read_json_invalid_json(self, tmp_path, mock_ui_utils):
        """Testet das Verhalten bei einer fehlerhaften JSON-Datei."""
        filepath = tmp_path / "invalid.json"
        filepath.write_text('{"key": "value",}', encoding='utf-8') # Invalid JSON with trailing comma
        mock_parent = MagicMock()

        data = JsonIOHandler.read_json(filepath, parent_for_dialog=mock_parent)

        assert data is None
        # Überprüfe den Aufruf flexibler, da die exakte Fehlermeldung von der JSON-Bibliothek abhängt
        mock_ui_utils.show_message.assert_called_once()
        args, kwargs = mock_ui_utils.show_message.call_args
        assert args[0] == 'error'
        assert args[1] == "Fehler beim Laden"
        assert f"Fehler beim Lesen oder Parsen der JSON-Datei:\n{filepath}" in args[2]
        assert "Fehler: " in args[2]
        assert kwargs['parent'] == mock_parent

    @patch('pathlib.Path.exists', return_value=True)
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_read_json_io_error(self, mock_open, mock_exists, tmp_path, mock_ui_utils):
        """Testet das Verhalten bei einem IOError während des Lesens."""
        filepath = tmp_path / "anyfile.json" # Filepath is needed, but open is mocked
        mock_parent = MagicMock()

        data = JsonIOHandler.read_json(filepath, parent_for_dialog=mock_parent)

        assert data is None
        mock_ui_utils.show_message.assert_called_once()

    # --- Tests for write_json ---

    def test_write_json_success(self, tmp_path):
        """Testet das erfolgreiche Schreiben von Daten in eine Datei."""
        filepath = tmp_path / "output.json"
        test_data = {"a": 1, "b": [2, 3]}

        result = JsonIOHandler.write_json(filepath, test_data)

        assert result is True
        assert filepath.exists()
        # Verify content
        with open(filepath, 'r', encoding='utf-8') as f:
            read_data = json.load(f)
        assert read_data == test_data

    def test_write_json_creates_directory(self, tmp_path):
        """Testet, ob das übergeordnete Verzeichnis bei Bedarf erstellt wird."""
        dirpath = tmp_path / "new_dir"
        filepath = dirpath / "output.json"
        test_data = {"message": "hello"}

        assert not dirpath.exists()
        result = JsonIOHandler.write_json(filepath, test_data)

        assert result is True
        assert dirpath.exists()
        assert filepath.exists()

    @patch('builtins.open', side_effect=IOError("Disk full"))
    def test_write_json_io_error(self, mock_open, tmp_path, mock_ui_utils):
        """Testet das Verhalten bei einem IOError während des Schreibens."""
        filepath = tmp_path / "output.json"
        test_data = {"a": 1}
        mock_parent = MagicMock()

        result = JsonIOHandler.write_json(filepath, test_data, parent_for_dialog=mock_parent)

        assert result is False
        mock_ui_utils.show_message.assert_called_once()
