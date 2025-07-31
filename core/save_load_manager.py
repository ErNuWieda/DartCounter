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
from tkinter import filedialog
import os
from .settings_manager import get_app_data_dir
from . import ui_utils

class SaveLoadManager:
    SAVE_FORMAT_VERSION = 2
    SAVE_TYPE_KEY = "save_type"
    GAME_SAVE_TYPE = "game"
    TOURNAMENT_SAVE_TYPE = "tournament"

    # Zentralisierte Dateitypen für Dialoge
    GAME_FILE_TYPES = (("Spiel-Speicherstände", "*.json"), ("Alle Dateien", "*.*"))
    TOURNAMENT_FILE_TYPES = (("Turnier-Speicherstände", "*.tourn.json"), ("Alle Dateien", "*.*"))

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
    def _collect_game_data(game):
        """
        Sammelt den kompletten Spielzustand und packt ihn in ein Dictionary.

        Diese private Hilfsmethode durchläuft das `game`-Objekt und alle
        zugehörigen `player`-Objekte, um einen serialisierbaren "Schnappschuss"
        des Spiels zu erstellen.

        Args:
            game (Game): Die aktive Spielinstanz, die gespeichert werden soll.

        Returns:
            dict or None: Ein Dictionary, das den gesamten Spielzustand repräsentiert,
                          oder None, wenn kein Spiel übergeben wurde.
        """
        if not game:
            return None

        players_data = []
        for p in game.players:
            player_dict = {
                'name': p.name,
                'id': p.id,
                'score': p.score,
                'throws': p.throws,
                'stats': p.stats,
                'state': p.state, # Kapselt alle spielspezifischen Daten
            }
            players_data.append(player_dict)

        game_data = {
            'save_format_version': SaveLoadManager.SAVE_FORMAT_VERSION,
            'save_type': SaveLoadManager.GAME_SAVE_TYPE,
            'game_name': game.name,
            'opt_in': game.opt_in,
            'opt_out': game.opt_out,
            'opt_atc': game.opt_atc,
            'count_to': game.count_to,
            'lifes': game.lifes,
            'rounds': game.rounds,
            'current_player_index': game.current,
            'round': game.round,
            'players': players_data,
        }
        return game_data

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
            filetypes=filetypes
        )

        if not filepath:
            return False  # User cancelled

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            ui_utils.show_message('info', "Erfolg", f"Daten erfolgreich gespeichert unter:\n{filepath}", parent=parent)
            return True
        except IOError as e:
            ui_utils.show_message('error', "Fehler beim Speichern", f"Die Daten konnten nicht gespeichert werden.\nFehler: {e}", parent=parent)
            return False

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
            filetypes=filetypes
        )

        if not filepath:
            return None  # User cancelled

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # --- Validierung ---
            file_version = data.get('save_format_version')
            file_type = data.get(SaveLoadManager.SAVE_TYPE_KEY)

            if file_version is None or file_type != expected_type:
                ui_utils.show_message('error', "Inkompatible Datei", f"Dies ist keine gültige '{expected_type}'-Speicherdatei.", parent=parent)
                return None
            if file_version != SaveLoadManager.SAVE_FORMAT_VERSION:
                ui_utils.show_message('error', "Inkompatibler Spielstand", f"Diese Speicherdatei (Version {file_version}) ist nicht mit der aktuellen Programmversion (erwartet Version {SaveLoadManager.SAVE_FORMAT_VERSION}) kompatibel.", parent=parent)
                return None

            return data
        except (IOError, json.JSONDecodeError) as e:
            ui_utils.show_message('error', "Fehler beim Laden", f"Die Datei konnte nicht geladen werden.\nFehler: {e}", parent=parent)
            return None

    @staticmethod
    def save_game_state(game, parent):
        """Sammelt Spieldaten und speichert sie über die generische Methode."""
        game_data = SaveLoadManager._collect_game_data(game)
        if not game_data:
            ui_utils.show_message('error', "Fehler", "Keine Spieldaten zum Speichern.", parent=parent)
            return False

        return SaveLoadManager._save_data(
            data=game_data,
            parent=parent,
            title="Spiel speichern unter...",
            filetypes=SaveLoadManager.GAME_FILE_TYPES,
            defaultextension=".json"
        )

    @staticmethod
    def save_tournament_state(tournament_manager, parent):
        """Sammelt Turnierdaten und speichert sie über die generische Methode."""
        tournament_data = tournament_manager.to_dict()
        tournament_data[SaveLoadManager.SAVE_TYPE_KEY] = SaveLoadManager.TOURNAMENT_SAVE_TYPE
        tournament_data['save_format_version'] = SaveLoadManager.SAVE_FORMAT_VERSION

        return SaveLoadManager._save_data(
            data=tournament_data,
            parent=parent,
            title="Turnier speichern unter...",
            filetypes=SaveLoadManager.TOURNAMENT_FILE_TYPES,
            defaultextension=".tourn.json"
        )

    @staticmethod
    def load_game_data(parent):
        """Lädt Spieldaten über die generische Methode."""
        return SaveLoadManager._load_data(
            parent=parent,
            title="Spiel laden...",
            filetypes=SaveLoadManager.GAME_FILE_TYPES,
            expected_type=SaveLoadManager.GAME_SAVE_TYPE
        )

    @staticmethod
    def load_tournament_data(parent):
        """Lädt Turnierdaten über die generische Methode."""
        return SaveLoadManager._load_data(
            parent=parent,
            title="Turnier laden...",
            filetypes=SaveLoadManager.TOURNAMENT_FILE_TYPES,
            expected_type=SaveLoadManager.TOURNAMENT_SAVE_TYPE
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
        game.round = data['round']
        game.current = data['current_player_index']
        for i, p_data in enumerate(data['players']):
            if i < len(game.players):
                player = game.players[i]
                # Kerndaten wiederherstellen
                player.name = p_data.get('name', player.name)
                player.id = p_data.get('id', player.id)
                player.score = p_data.get('score', player.score)
                player.throws = p_data.get('throws', [])
                player.stats = p_data.get('stats', {})
                # Spielspezifischen Zustand wiederherstellen
                player.state.update(p_data.get('state', {}))

        # --- UI-Zustand nach dem Laden wiederherstellen ---
        for player in game.players:
            if player.sb:  # Sicherstellen, dass das Scoreboard existiert
                # Aktualisiert die Hauptanzeige (Punkte, Leben, nächstes Ziel etc.)
                player.sb.update_score(player.score)
                # Aktualisiert spezifische Anzeigen wie Cricket-Treffer
                if hasattr(player.sb, 'update_display'):
                    player.sb.update_display(player.state['hits'], player.score)