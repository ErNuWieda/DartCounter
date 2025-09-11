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

from tkinter import filedialog
import hashlib
import json
from pathlib import Path
import os
from .settings_manager import get_app_data_dir
from . import ui_utils
from .json_io_handler import JsonIOHandler


class SaveLoadManager:
    SAVE_FORMAT_VERSION = 3  # Version erhöht wegen Checksum-Implementierung
    SAVE_TYPE_KEY = "save_type"
    GAME_SAVE_TYPE = "game"
    TOURNAMENT_SAVE_TYPE = "tournament"

    # Zentralisierte Dateitypen für Dialoge
    GAME_FILE_TYPES = (("Spiel-Speicherstände", "*.json"), ("Alle Dateien", "*.*"))
    TOURNAMENT_FILE_TYPES = (
        ("Turnier-Speicherstände", "*.tourn.json"),
        ("Alle Dateien", "*.*"),
    )

    """
    Verwaltet das Speichern und Laden von Spielständen als statische Utility-Klasse.

    Diese Klasse enthält ausschließlich statische Methoden und wird nicht instanziiert.
    Sie ist verantwortlich für:
    - Das Sammeln aller relevanten Daten aus einer laufenden `Game`-Instanz.
    - Das Öffnen von Systemdialogen zum Auswählen von Speicher- oder Ladeorten.
    - Das Serialisieren des Spielzustands in eine JSON-Datei.
    - Das Deserialisieren einer JSON-Datei zurück in ein Python-Dictionary.
    - Das Wiederherstellen des Zustands einer `Game`-Instanz aus den geladenen Daten.
    """

    @staticmethod
    def _get_savegames_dir():
        """Gibt das Verzeichnis für Spielstände zurück und erstellt es bei Bedarf."""
        save_dir = get_app_data_dir() / "savegames"
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir

    @staticmethod
    def _calculate_checksum(data: dict) -> str:
        """
        Berechnet einen SHA-256-Checksum für ein Dictionary, um die Integrität
        der Speicherdatei zu gewährleisten.

        Args:
            data (dict): Die Daten, für die der Checksum berechnet werden soll.

        Returns:
            str: Der hexadezimale Checksum-String.
        """
        canonical_string = json.dumps(
            data, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(canonical_string).hexdigest()

    @staticmethod
    def _save_data(data, parent, title, filetypes, defaultextension):
        """
        Generische private Methode zum Speichern von Daten in eine JSON-Datei.

        Args:
            data (dict): Die zu speichernden Daten.
            parent (tk.Widget): Das übergeordnete Fenster für Dialoge.
            title (str): Der Titel für den Speicherdialog.
            filetypes (tuple): Die Dateitypen für den Dialog.
            defaultextension (str): Die Standard-Dateiendung.

        Returns:
            bool: True bei Erfolg, sonst False.
        """
        filepath = filedialog.asksaveasfilename(
            initialdir=SaveLoadManager._get_savegames_dir(),
            title=title,
            defaultextension=defaultextension,
            filetypes=filetypes,
        )
        if not filepath:
            return False  # User cancelled

        # Füge einen Checksum hinzu, um manuelle Änderungen zu erkennen
        data["checksum"] = SaveLoadManager._calculate_checksum(data)

        return JsonIOHandler.write_json(
            filepath=Path(filepath),
            data=data,
            parent_for_dialog=parent,
            show_success=True,  # Zeige eine Erfolgsmeldung an
        )

    @staticmethod
    def _load_data(parent, title, filetypes, expected_type):
        """
        Generische private Methode zum Laden von Daten aus einer JSON-Datei.

        Returns:
            dict or None: Die geladenen Daten oder None bei Fehler/Abbruch.
        Args:
            parent (tk.Widget): Das übergeordnete Fenster für Dialoge.
            title (str): Der Titel für den Ladedialog.
            filetypes (tuple): Die Dateitypen für den Dialog.
            expected_type (str): Der erwartete 'save_type' in der Datei.
        """
        filepath = filedialog.askopenfilename(
            initialdir=SaveLoadManager._get_savegames_dir(),
            title=title,
            filetypes=filetypes,
        )

        if not filepath:
            return None  # User cancelled

        data = JsonIOHandler.read_json(Path(filepath), parent_for_dialog=parent)
        if not data:
            return None  # Fehler wurde bereits vom Handler angezeigt

        # --- Validierung ---
        file_version = data.get("save_format_version")
        file_type = data.get(SaveLoadManager.SAVE_TYPE_KEY)
        stored_checksum = data.pop("checksum", None)

        if file_version is None or file_type != expected_type:
            ui_utils.show_message(
                "error",
                "Inkompatible Datei",
                f"Dies ist keine gültige '{expected_type}'-Speicherdatei.",
                parent=parent,
            )
            return None

        # Checksum-Validierung (ab Version 3)
        if file_version >= 3:
            if not stored_checksum:
                ui_utils.show_message(
                    "error",
                    "Fehler beim Laden",
                    "Die Speicherdatei enthält keinen Integritäts-Checksum und kann nicht geladen werden.",
                    parent=parent,
                )
                return None

            calculated_checksum = SaveLoadManager._calculate_checksum(data)
            if stored_checksum != calculated_checksum:
                ui_utils.show_message(
                    "error",
                    "Fehler beim Laden",
                    "Die Speicherdatei ist korrupt oder wurde manuell verändert. Der Ladevorgang wird abgebrochen.",
                    parent=parent,
                )
                return None

        if file_version > SaveLoadManager.SAVE_FORMAT_VERSION:
            ui_utils.show_message(
                "error",
                "Inkompatibler Spielstand",
                f"Diese Speicherdatei (Version {file_version}) ist nicht mit der aktuellen Programmversion (erwartet Version {SaveLoadManager.SAVE_FORMAT_VERSION}) kompatibel.",
                parent=parent,
            )
            return None

        return data

    @staticmethod
    def save_state(savable_object, parent):
        """
        Speichert den Zustand eines beliebigen Objekts, das die Speicher-Schnittstelle
        (`to_dict` und `get_save_meta`) implementiert.
        """
        if not hasattr(savable_object, "to_dict") or not hasattr(
            savable_object, "get_save_meta"
        ):
            ui_utils.show_message(
                "error",
                "Speicherfehler",
                "Das Objekt kann nicht gespeichert werden, da es die Speicherschnittstelle nicht implementiert.",
                parent=parent,
            )
            return False

        data = savable_object.to_dict()
        meta = savable_object.get_save_meta()

        # Füge Metadaten hinzu, die für alle Speicherstände gelten
        data[SaveLoadManager.SAVE_TYPE_KEY] = meta["save_type"]
        data["save_format_version"] = SaveLoadManager.SAVE_FORMAT_VERSION

        return SaveLoadManager._save_data(
            data=data,
            parent=parent,
            title=meta["title"],
            filetypes=meta["filetypes"],
            defaultextension=meta["defaultextension"],
        )

    @staticmethod
    def load_game_data(parent):
        """Lädt Spieldaten über die generische Methode."""
        return SaveLoadManager._load_data(
            parent=parent,
            title="Spiel laden...",
            filetypes=SaveLoadManager.GAME_FILE_TYPES,
            expected_type=SaveLoadManager.GAME_SAVE_TYPE,
        )

    @staticmethod
    def load_tournament_data(parent):
        """Lädt Turnierdaten über die generische Methode."""
        return SaveLoadManager._load_data(
            parent=parent,
            title="Turnier laden...",
            filetypes=SaveLoadManager.TOURNAMENT_FILE_TYPES,
            expected_type=SaveLoadManager.TOURNAMENT_SAVE_TYPE,
        )

    @staticmethod
    def restore_game_state(game, data):
        """
        Stellt den Zustand eines Game-Objekts aus geladenen Daten wieder her.

        Diese Methode nimmt eine neu erstellte `Game`-Instanz und das geladene
        `data`-Dictionary und überschreibt die Attribute des Spiels und seiner
        Spieler mit den geladenen Werten. Anschließend wird die Benutzeroberfläche
        (Scoreboards) aktualisiert, um den wiederhergestellten Zustand anzuzeigen.

        Args:
            game (Game): Die neue Spielinstanz, deren Zustand wiederhergestellt wird.
            data (dict): Das Dictionary mit den geladenen Spieldaten.
        """
        game.round = data["round"]
        game.current = data["current_player_index"]
        for i, p_data in enumerate(data["players"]):
            if i < len(game.players):
                player = game.players[i]
                # Kerndaten wiederherstellen
                player.name = p_data.get("name", player.name)
                player.id = p_data.get("id", player.id)
                player.score = p_data.get("score", player.score)
                player.throws = p_data.get("throws", [])
                player.stats = p_data.get("stats", {})
                # Spielspezifischen Zustand wiederherstellen
                player.state.update(p_data.get("state", {}))

        # --- Zustand für Legs & Sets wiederherstellen ---
        # Dies geschieht nach der Spieler-Wiederherstellung, um sicherzustellen,
        # dass die Game-Instanz korrekt konfiguriert ist.
        if game.is_leg_set_match:
            # Die Schlüssel in den geladenen Dictionaries sind Strings (wegen JSON),
            # wir müssen sie wieder in Integer (player.id) umwandeln.
            raw_leg_scores = data.get("player_leg_scores", {})
            game.player_leg_scores = {int(k): v for k, v in raw_leg_scores.items()}

            raw_set_scores = data.get("player_set_scores", {})
            game.player_set_scores = {int(k): v for k, v in raw_set_scores.items()}

            game.leg_start_player_index = data.get("leg_start_player_index", 0)

        # --- UI-Zustand nach dem Laden wiederherstellen ---
        for player in game.players:
            if player.sb and player.sb.score_window.winfo_exists():
                # Für zielbasierte Spiele (Cricket, Micky, etc.) ruft update_display
                # intern update_score auf und aktualisiert zusätzlich die Treffer-Anzeige.
                if hasattr(player.sb, "update_display"):
                    # Stelle sicher, dass 'hits' im state-Dictionary existiert
                    hits_data = player.state.get("hits", {})
                    player.sb.update_display(hits_data, player.score)
                else:
                    # Für andere Spiele (X01, Killer) reicht ein einfaches Update des Scores.
                    player.sb.update_score(player.score)
