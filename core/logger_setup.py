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

import logging
from logging.handlers import RotatingFileHandler
from .settings_manager import get_app_data_dir

def setup_logging():
    """
    Konfiguriert das zentrale Logging für die gesamte Anwendung.

    - Setzt das globale Logging-Level auf INFO.
    - Fügt einen FileHandler hinzu, der Logs in eine rotierende Datei schreibt.
    - Fügt einen StreamHandler hinzu, der Logs in die Konsole ausgibt.
    """
    # Root-Logger konfigurieren
    logger = logging.getLogger()
    
    # Bereinige eventuell vorhandene, von anderen Bibliotheken gesetzte Handler,
    # um eine saubere und kontrollierte Logging-Konfiguration sicherzustellen.
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.INFO)

    # Formatter für alle Handler definieren
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # --- FileHandler mit Fehlerbehandlung ---
    # Versucht, einen File-Logger zu erstellen. Wenn dies fehlschlägt (z.B. wegen
    # fehlender Berechtigungen), wird die Anwendung nicht abstürzen.
    try:
        log_dir = get_app_data_dir()
        log_file = log_dir / "dartcounter.log"
        # FileHandler mit Rotation (z.B. 1MB pro Datei, 3 Backups)
        file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=3, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (IOError, PermissionError) as e:
        # Wenn das Logging in eine Datei fehlschlägt, geben wir eine Warnung auf der
        # Konsole aus, aber die Anwendung läuft weiter.
        print(f"WARNUNG: Konnte Log-Datei nicht erstellen. Logging erfolgt nur in die Konsole. Fehler: {e}")

    # StreamHandler für die Konsolenausgabe
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
