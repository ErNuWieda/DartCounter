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
from unittest.mock import MagicMock, patch, ANY
from core.profile_manager_dialog import ProfileManagerDialog
from core.player_profile import PlayerProfile


@pytest.fixture
def mock_managers():
    """Erstellt Mocks für die Manager-Abhängigkeiten des Dialogs."""
    mock_profile_manager = MagicMock()
    mock_player_stats_manager = MagicMock()

    # Simuliere eine Liste von existierenden Profilen
    profile1 = PlayerProfile(profile_id=1, name="Alice", is_ai=False)
    profile2 = PlayerProfile(profile_id=2, name="RoboCop", is_ai=True, difficulty="Profi")
    mock_profile_manager.get_profiles.return_value = [profile1, profile2]

    return mock_profile_manager, mock_player_stats_manager


@pytest.fixture
def dialog(tk_root_session, mock_managers, monkeypatch):
    """
    Erstellt eine Instanz des ProfileManagerDialog für Tests.
    Alle externen UI-Interaktionen (Dialoge) werden gepatcht.
    """
    mock_profile_manager, mock_player_stats_manager = mock_managers

    # Patch für den EditProfileDialog, um zu verhindern, dass er sich öffnet
    monkeypatch.setattr("core.profile_manager_dialog.EditProfileDialog", MagicMock())
    # Patch für messagebox, um Bestätigungsdialoge abzufangen
    monkeypatch.setattr("core.profile_manager_dialog.messagebox", MagicMock())
    # Patch für wait_window, um zu verhindern, dass der Test auf einen gemockten Dialog wartet.
    # Dies ist die Ursache für den TclError.
    monkeypatch.setattr("core.profile_manager_dialog.ProfileManagerDialog.wait_window", MagicMock())

    dialog_instance = ProfileManagerDialog(
        tk_root_session, mock_profile_manager, mock_player_stats_manager
    )
    dialog_instance.update()
    yield dialog_instance
    if dialog_instance.winfo_exists():
        dialog_instance.destroy()


@pytest.mark.ui
class TestProfileManagerDialog:
    """Testet die UI-Logik des ProfileManagerDialog."""

    def test_initialization_populates_list(self, dialog, mock_managers):
        """Testet, ob der Dialog die Profilliste beim Start korrekt füllt."""
        mock_profile_manager, _ = mock_managers

        # Prüfen, ob die Profile aus dem Manager geladen wurden
        mock_profile_manager.get_profiles.assert_called_once()

        # Prüfen, ob die Einträge im Treeview vorhanden sind
        children = dialog.tree.get_children()
        assert len(children) == 2

        # Prüfe die Werte des ersten Eintrags (Alice)
        item1 = dialog.tree.item(children[0])
        assert item1["values"] == ["Alice", "Mensch", "-"]

        # Prüfe die Werte des zweiten Eintrags (RoboCop)
        item2 = dialog.tree.item(children[1])
        assert item2["values"] == ["RoboCop", "KI", "Profi"]

    def test_add_profile_opens_edit_dialog(self, dialog, monkeypatch):
        """Testet, ob der "Neues Profil"-Button den Edit-Dialog öffnet."""
        mock_edit_dialog_class = MagicMock()
        monkeypatch.setattr(
            "core.profile_manager_dialog.EditProfileDialog", mock_edit_dialog_class
        )

        # Simuliere einen Klick auf den "Neues Profil"-Button
        dialog._add_new_profile()

        # Prüfen, ob der Edit-Dialog ohne Profil-Daten aufgerufen wurde
        mock_edit_dialog_class.assert_called_once_with(dialog, dialog.profile_manager)

    def test_edit_profile_opens_edit_dialog_with_data(self, dialog, monkeypatch, mock_managers):
        """Testet, ob der "Profil bearbeiten"-Button den Edit-Dialog mit den korrekten Daten öffnet."""
        mock_profile_manager, _ = mock_managers
        mock_edit_dialog_class = MagicMock()
        monkeypatch.setattr(
            "core.profile_manager_dialog.EditProfileDialog", mock_edit_dialog_class
        )

        # Wähle das erste Item (Alice) im Treeview aus
        first_item_id = dialog.tree.get_children()[0]
        dialog.tree.focus(first_item_id)
        dialog.tree.selection_set(first_item_id)

        # Simuliere einen Klick auf den "Profil bearbeiten"-Button
        dialog._edit_selected_profile()

        # Prüfen, ob der Edit-Dialog mit dem Profil von Alice aufgerufen wurde
        expected_profile = mock_profile_manager.get_profiles.return_value[0]
        mock_edit_dialog_class.assert_called_once_with(
            dialog, dialog.profile_manager, profile_to_edit=expected_profile
        )

    def test_delete_profile_with_confirmation(self, dialog, monkeypatch, mock_managers):
        """Testet den Löschvorgang, wenn der Benutzer bestätigt."""
        mock_profile_manager, _ = mock_managers
        mock_messagebox = MagicMock()
        mock_messagebox.askyesno.return_value = True  # Simuliere "Ja" im Dialog
        monkeypatch.setattr("core.profile_manager_dialog.messagebox", mock_messagebox)

        # Wähle das zweite Item (RoboCop) aus
        item_to_delete_id = dialog.tree.get_children()[1]
        dialog.tree.focus(item_to_delete_id)
        dialog.tree.selection_set(item_to_delete_id)

        # Simuliere einen Klick auf den "Profil löschen"-Button
        dialog._delete_selected_profile()

        # Prüfen, ob der Bestätigungsdialog angezeigt wurde
        mock_messagebox.askyesno.assert_called_once()
        # Prüfen, ob die delete-Methode des Managers mit der korrekten ID aufgerufen wurde
        mock_profile_manager.delete_profile_by_id.assert_called_once_with(2)

    def test_delete_profile_cancelled(self, dialog, monkeypatch, mock_managers):
        """Testet, dass nichts passiert, wenn der Benutzer den Löschvorgang abbricht."""
        mock_profile_manager, _ = mock_managers
        mock_messagebox = MagicMock()
        mock_messagebox.askyesno.return_value = False  # Simuliere "Nein" im Dialog
        monkeypatch.setattr("core.profile_manager_dialog.messagebox", mock_messagebox)

        # Wähle ein Item aus
        item_to_delete_id = dialog.tree.get_children()[0]
        dialog.tree.focus(item_to_delete_id)
        dialog.tree.selection_set(item_to_delete_id)

        dialog._delete_selected_profile()

        mock_messagebox.askyesno.assert_called_once()
        # Die delete-Methode darf NICHT aufgerufen worden sein
        mock_profile_manager.delete_profile_by_id.assert_not_called()

    def test_recalculate_accuracy_for_human_player(self, dialog, monkeypatch, mock_managers):
        """Testet die Neuberechnung des Genauigkeitsmodells für einen menschlichen Spieler."""
        _, mock_player_stats_manager = mock_managers
        mock_messagebox = MagicMock()
        mock_messagebox.askyesno.return_value = True  # Bestätige die Neuberechnung
        monkeypatch.setattr("core.profile_manager_dialog.messagebox", mock_messagebox)

        # Wähle den menschlichen Spieler (Alice) aus
        human_player_item_id = dialog.tree.get_children()[0]
        dialog.tree.focus(human_player_item_id)
        dialog.tree.selection_set(human_player_item_id)

        dialog._recalculate_accuracy()

        # Prüfen, ob der Bestätigungsdialog angezeigt wurde
        mock_messagebox.askyesno.assert_called_once()
        # Prüfen, ob die Methode des Statistik-Managers aufgerufen wurde
        mock_player_stats_manager.update_accuracy_model.assert_called_once_with(
            "Alice", parent_window=dialog
        )