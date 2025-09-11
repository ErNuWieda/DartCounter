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

import json
import logging
from pathlib import Path
from . import ui_utils

logger = logging.getLogger(__name__)


class JsonIOHandler:
    """Eine statische Utility-Klasse für zentralisiertes Lesen und Schreiben von JSON-Dateien."""

    @staticmethod
    def read_json(filepath: Path, parent_for_dialog=None) -> dict | None:
        """
        Liest und dekodiert eine JSON-Datei mit zentralisierter Fehlerbehandlung.

        Args:
            filepath (Path): Der Pfad zur JSON-Datei.
            parent_for_dialog (tk.Widget, optional): Das übergeordnete Widget für Fehlerdialoge.
                                                     Wenn None, werden Fehler nur geloggt.

        Returns:
            dict or None: Die geladenen Daten als Dictionary oder None bei einem Fehler.
        """
        if not filepath.exists():
            logger.info(f"JSON-Datei nicht gefunden unter: {filepath}")
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            error_msg = f"Fehler beim Lesen oder Parsen der JSON-Datei:\n{filepath}\n\nFehler: {e}"
            logger.error(error_msg, exc_info=True)
            if parent_for_dialog:
                ui_utils.show_message(
                    "error", "Fehler beim Laden", error_msg, parent=parent_for_dialog
                )
            return None

    @staticmethod
    def write_json(filepath: Path, data: dict, parent_for_dialog=None, show_success=False) -> bool:
        """
        Kodiert und schreibt Daten in eine JSON-Datei mit zentralisierter Fehlerbehandlung.
        """
        try:
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            if show_success and parent_for_dialog:
                ui_utils.show_message(
                    "info",
                    "Erfolg",
                    f"Daten erfolgreich gespeichert unter:\n{filepath}",
                    parent=parent_for_dialog,
                )
            return True
        except IOError as e:
            error_msg = f"Die Daten konnten nicht gespeichert werden.\nFehler: {e}"
            logger.error(error_msg, exc_info=True)
            if parent_for_dialog:
                ui_utils.show_message(
                    "error",
                    "Fehler beim Speichern",
                    error_msg,
                    parent=parent_for_dialog,
                )
            return False
