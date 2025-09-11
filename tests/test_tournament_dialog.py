import pytest
import tkinter as tk
from unittest.mock import MagicMock, ANY

# Die zu testende Klasse
from core.tournament_dialog import TournamentSettingsDialog


@pytest.fixture
def tk_root():
    """Fixture zum Erstellen und Zerstören eines tk-Root-Fensters."""
    root = tk.Tk()
    root.withdraw()  # Fenster ausblenden
    yield root
    if root.winfo_exists():
        root.destroy()


@pytest.fixture
def dialog_setup(tk_root, monkeypatch):
    """Richtet den TournamentSettingsDialog mit Mocks für den Test ein."""

    mock_settings_manager = MagicMock()
    mock_settings_manager.get.return_value = [
        "ProfA",
        "Guest1",
    ]  # für last_tournament_players

    mock_profile_manager = MagicMock()
    mock_profile_a = MagicMock()
    mock_profile_a.name = "ProfA"
    mock_profile_b = MagicMock()
    mock_profile_b.name = "ProfB"
    mock_profile_manager.get_profiles.return_value = [mock_profile_a, mock_profile_b]

    dialog = TournamentSettingsDialog(tk_root, mock_profile_manager, mock_settings_manager)
    dialog.update()

    yield dialog, mock_settings_manager, mock_profile_manager

    # Aufräumen: Zerstöre den Dialog, falls er noch existiert
    if dialog and dialog.winfo_exists():
        dialog.destroy()


class TestTournamentSettingsDialog:
    """
    Testet die UI-Logik der TournamentSettingsDialog-Klasse isoliert.
    """

    def test_initialization_loads_last_players(self, dialog_setup):
        """Testet, ob der Dialog initialisiert und die zuletzt verwendeten Spieler korrekt lädt."""
        dialog, mock_settings_manager, _ = dialog_setup
        mock_settings_manager.get.assert_called_once_with("last_tournament_players", [])

        # Prüfen, ob die ersten beiden Spielereinträge auf die geladenen Namen gesetzt sind
        assert dialog.player_name_entries[0].get() == "ProfA"
        assert dialog.player_name_entries[1].get() == "Guest1"
        assert dialog.player_name_entries[2].get() == ""  # Sollte leer sein
        assert dialog.player_name_entries[3].get() == ""  # Sollte leer sein

    def test_start_button_collects_data_and_saves_settings(self, dialog_setup):
        """Testet, ob der Start-Button die Daten korrekt sammelt und die Einstellungen speichert."""
        dialog, mock_settings_manager, _ = dialog_setup
        # Benutzereingaben simulieren
        dialog.player_count_var.set("2")
        dialog._update_player_entries()  # Manuelles Auslösen des Updates
        dialog.player_name_entries[0].set("Alice")
        dialog.player_name_entries[1].set("Bob")
        dialog.game_mode_var.set("701")

        # Button-Klick simulieren
        dialog._on_start()

        assert not dialog.cancelled
        assert dialog.player_names == ["Alice", "Bob"]
        assert dialog.game_mode == "701"

        # Prüfen, ob die Einstellungen gespeichert wurden
        mock_settings_manager.set.assert_called_once_with(
            "last_tournament_players", ["Alice", "Bob"]
        )

    def test_start_button_shows_error_on_duplicate_names(self, dialog_setup, monkeypatch):
        """Testet, ob ein Fehler angezeigt wird, wenn die Spielernamen nicht eindeutig sind."""
        dialog, _, _ = dialog_setup
        mock_showerror = MagicMock()
        monkeypatch.setattr("core.tournament_dialog.messagebox.showerror", mock_showerror)

        dialog.player_count_var.set("2")
        dialog._update_player_entries()
        dialog.player_name_entries[0].set("SameName")
        dialog.player_name_entries[1].set("SameName")

        dialog._on_start()

        assert dialog.cancelled  # Sollte nicht fortfahren
        mock_showerror.assert_called_once_with(
            "Fehler", "Spielernamen müssen eindeutig sein.", parent=dialog
        )

    def test_update_available_profiles_removes_selected_names(self, dialog_setup):
        """Testet, ob die Profilliste korrekt gefiltert wird."""
        dialog, _, _ = dialog_setup
        # "ProfA" ist bereits durch setUp ausgewählt.
        # Die Liste für die zweite Combobox sollte "ProfA" nicht enthalten.
        available_for_second = tuple(dialog.player_name_entries[1]["values"])
        assert "ProfA" not in available_for_second
        assert "ProfB" in available_for_second

        # Die erste Box sollte "ProfA" aber noch zur Auswahl haben.
        available_for_first = tuple(dialog.player_name_entries[0]["values"])
        assert "ProfA" in available_for_first
