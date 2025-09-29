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
from core.edit_profile_dialog import EditProfileDialog
from core.player_profile import PlayerProfile


@pytest.fixture
def mock_profile_manager():
    """Erstellt einen Mock für den ProfileManager mit einem menschlichen Profil als Vorlage."""
    manager = MagicMock()
    human_template = PlayerProfile(
        profile_id=1,
        name="HumanTemplate",
        is_ai=False,
        accuracy_model={"T20": {"mean_offset_x": 1.0}},
    )
    manager.get_profile_by_name.return_value = human_template
    manager.get_profiles.return_value = [human_template]
    return manager


@pytest.fixture
def dialog_dependencies(monkeypatch):
    """Patcht externe UI-Dialoge, die nicht messagebox sind."""
    # Erstelle die Mocks zuerst, damit wir sie zurückgeben können.
    mock_filedialog = MagicMock()
    mock_messagebox = MagicMock()
    mock_colorchooser = MagicMock()

    monkeypatch.setattr("core.edit_profile_dialog.filedialog", mock_filedialog)
    # WICHTIG: Wir müssen das Modul patchen, das im zu testenden Code importiert wird.
    # EditProfileDialog importiert 'messagebox' aus 'tkinter.messagebox'.
    monkeypatch.setattr("core.edit_profile_dialog.messagebox", mock_messagebox)
    monkeypatch.setattr("core.edit_profile_dialog.CustomColorChooserDialog", mock_colorchooser)

    # Deaktiviere die blockierenden Methoden des Dialogs selbst, um UI-Hänger
    # und "window not viewable" Fehler zu vermeiden.
    monkeypatch.setattr("core.edit_profile_dialog.EditProfileDialog.grab_set", lambda self: None)
    monkeypatch.setattr("core.edit_profile_dialog.EditProfileDialog.wait_window", lambda self: None)

    mocks = {"filedialog": mock_filedialog, "messagebox": mock_messagebox, "colorchooser": mock_colorchooser}
    return mocks


@pytest.mark.ui
class TestEditProfileDialog:
    """Testet die UI-Logik und Interaktionen des EditProfileDialog."""

    def test_initialization_new_profile(
        self, tk_root_session, mock_profile_manager, dialog_dependencies
    ):
        """Testet, ob der Dialog für ein neues Profil mit Standardwerten startet."""
        dialog = EditProfileDialog(tk_root_session, mock_profile_manager)
        dialog.update()

        assert dialog.title() == "Neues Profil erstellen"
        assert dialog.name_entry.get() == ""
        assert dialog.is_ai_var.get() is False
        assert dialog.difficulty_var.get() == "Anfänger"
        # Prüfen, ob die AI-Einstellungen initial verborgen sind
        assert not dialog.ai_settings_frame.winfo_ismapped()

        dialog.destroy()

    def test_initialization_edit_profile(
        self, tk_root_session, mock_profile_manager, dialog_dependencies
    ):
        """Testet, ob der Dialog beim Bearbeiten die Profildaten korrekt lädt."""
        profile_to_edit = PlayerProfile(
            profile_id=5,
            name="RoboCop",
            is_ai=True,
            difficulty="Profi",
            preferred_double=16,
            dart_color="#00ff00",
        )
        dialog = EditProfileDialog(
            tk_root_session, mock_profile_manager, profile_to_edit=profile_to_edit
        )
        # KORREKTUR: Expliziter Aufruf des Event-Handlers, um die UI-Sichtbarkeit
        # basierend auf den geladenen Profildaten zu aktualisieren.
        dialog._on_player_type_change()
        dialog.update()

        assert dialog.title() == "Profil bearbeiten"
        assert dialog.name_entry.get() == "RoboCop"
        assert dialog.is_ai_var.get() is True
        assert dialog.difficulty_var.get() == "Profi"
        assert dialog.preferred_double_var.get() == "16"
        assert str(dialog.color_preview_label.cget("bg")) == "#00ff00"
        # Prüfen, ob die AI-Einstellungen sichtbar sind
        dialog.update_idletasks()  # Erzwinge UI-Update
        # KORREKTUR: winfo_ismapped() ist in Tests unzuverlässig.
        # Stattdessen prüfen wir, ob das Widget vom Grid-Manager verwaltet wird.
        # grid_info() gibt ein leeres Dict zurück, wenn das Widget via grid_remove() versteckt wurde.
        assert dialog.ai_settings_frame.grid_info(), "AI-Einstellungs-Frame sollte sichtbar sein."

        dialog.destroy()

    def test_player_type_toggle_shows_hides_widgets(
        self, tk_root_session, mock_profile_manager, dialog_dependencies
    ):
        """Testet, ob das Umschalten des Spielertyps die korrekten UI-Elemente anzeigt."""
        dialog = EditProfileDialog(tk_root_session, mock_profile_manager)
        # KORREKTUR: Expliziter Aufruf des Event-Handlers, um den initialen Zustand
        # (Mensch-Profil) korrekt herzustellen.
        dialog._on_player_type_change()
        dialog.update()

        # Initial: Mensch -> AI-Settings versteckt, Double-Out sichtbar
        assert not dialog.ai_settings_frame.grid_info()
        assert dialog.double_out_frame.grid_info(), "Double-Out-Frame sollte initial sichtbar sein."

        # Umschalten auf KI
        dialog.is_ai_var.set(True)
        dialog._on_player_type_change()
        dialog.update_idletasks()  # Erzwinge UI-Update
        # Jetzt: KI -> AI-Settings sichtbar, Double-Out versteckt
        assert dialog.ai_settings_frame.grid_info(), "AI-Einstellungs-Frame sollte nach Umschalten sichtbar sein."
        assert not dialog.double_out_frame.grid_info(), "Double-Out-Frame sollte nach Umschalten versteckt sein."

        dialog.destroy()

    def test_difficulty_toggle_shows_adaptive_options(
        self, tk_root_session, mock_profile_manager, dialog_dependencies
    ):
        """Testet, ob bei Auswahl von "Adaptiv" die Klon-Vorlage erscheint."""
        dialog = EditProfileDialog(tk_root_session, mock_profile_manager)
        dialog.is_ai_var.set(True)  # Set to AI mode
        dialog._on_player_type_change()
        dialog.update_idletasks()
        dialog.update()  # KORREKTUR: update() erzwingt ein Neuzeichnen.

        # Initial (nicht-adaptiv): Klon-Vorlage versteckt
        assert not dialog.adaptive_template_label.grid_info()

        # Umschalten auf Adaptiv
        dialog.difficulty_var.set("Adaptiv")
        dialog._on_difficulty_change()
        dialog.update_idletasks()
        dialog.update()  # KORREKTUR: update() erzwingt ein Neuzeichnen.

        # Jetzt: Klon-Vorlage sichtbar
        assert dialog.adaptive_template_label.grid_info(), "Vorlage für adaptive KI sollte sichtbar sein."

        dialog.destroy()

    def test_save_new_human_profile(
        self, tk_root_session, mock_profile_manager, dialog_dependencies
    ):
        """Testet das Speichern eines neuen menschlichen Profils."""
        mock_profile_manager.add_profile.return_value = True
        dialog = EditProfileDialog(tk_root_session, mock_profile_manager)

        # Eingaben simulieren
        dialog.name_entry.insert(0, "New Player")
        dialog.preferred_double_var.set("18")

        # Speichern
        dialog._on_save()

        mock_profile_manager.add_profile.assert_called_once_with(
            "New Player", None, "#ff0000", is_ai=False, difficulty=None, preferred_double=18, accuracy_model=None
        )
        assert dialog.saved_successfully is True

    def test_save_new_adaptive_ai_profile(
        self, tk_root_session, mock_profile_manager, dialog_dependencies
    ):
        """Testet das Speichern einer neuen adaptiven KI."""
        mock_profile_manager.add_profile.return_value = True
        dialog = EditProfileDialog(tk_root_session, mock_profile_manager)

        # Eingaben simulieren
        dialog.name_entry.insert(0, "AI Clone")
        dialog.is_ai_var.set(True)
        dialog.difficulty_var.set("Adaptiv")
        dialog.adaptive_template_var.set("HumanTemplate")

        # Speichern
        dialog._on_save()

        # Überprüfen, ob das Genauigkeitsmodell der Vorlage übergeben wurde
        expected_model = {"T20": {"mean_offset_x": 1.0}}
        mock_profile_manager.add_profile.assert_called_once_with(
            "AI Clone", None, "#ff0000", is_ai=True, difficulty="Adaptiv", preferred_double=None, accuracy_model=expected_model
        )
        assert dialog.saved_successfully is True

    def test_save_fails_on_empty_name(
        self, tk_root_session, mock_profile_manager, dialog_dependencies
    ):
        """Testet, ob das Speichern bei leerem Namen fehlschlägt und eine Meldung anzeigt."""
        dialog = EditProfileDialog(tk_root_session, mock_profile_manager)
        mock_messagebox = dialog_dependencies["messagebox"]

        dialog._on_save()

        mock_messagebox.showerror.assert_called_once()
        mock_profile_manager.add_profile.assert_not_called()
        assert dialog.saved_successfully is False

    def test_save_fails_on_duplicate_name(
        self, tk_root_session, mock_profile_manager, dialog_dependencies
    ):
        """Testet, ob das Speichern bei einem Duplikat-Namen fehlschlägt."""
        mock_profile_manager.add_profile.return_value = False  # Simuliere Duplikat
        dialog = EditProfileDialog(tk_root_session, mock_profile_manager)
        mock_messagebox = dialog_dependencies["messagebox"]

        dialog.name_entry.insert(0, "Existing Player")
        dialog._on_save()

        mock_messagebox.showerror.assert_called_once()
        assert dialog.saved_successfully is False
