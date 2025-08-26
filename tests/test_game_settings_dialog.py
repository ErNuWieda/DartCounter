import pytest
import tkinter as tk # Import real tkinter
from unittest.mock import MagicMock, ANY

# Die zu testende Klasse
from core.gamemgr import GameSettingsDialog

@pytest.fixture
def tk_root():
    """Fixture to create and destroy a tk root window."""
    root = tk.Tk()
    # Verhindert, dass das Hauptfenster angezeigt wird
    root.withdraw()
    yield root
    if root and root.winfo_exists():
        root.destroy()

@pytest.fixture
def dialog_setup(tk_root, monkeypatch):
    """
    Setzt für jeden Test einen neuen Dialog in einer Test-Umgebung auf.
    """
    # Patch wait_window, um zu verhindern, dass der modale Dialog den Test blockiert.
    # Dies ist notwendig, da der Dialog selbst `wait_window` aufruft, wenn der
    # Profile-Manager-Dialog geöffnet wird.
    monkeypatch.setattr(tk.Toplevel, 'wait_window', lambda self, window: None)

    # Patch die globale Spielkonfiguration, um den Test vom Dateisystem zu entkoppeln.
    # Dies stellt sicher, dass die Tests auch in einer CI-Umgebung, in der die
    # Konfigurationsdatei möglicherweise nicht gefunden wird, zuverlässig laufen.
    mock_game_config = {
        "301": {"frame": "x01_options", "defaults": {"count_to": "301"}, "min_players": 1},
        "501": {"frame": "x01_options", "defaults": {"count_to": "501"}, "min_players": 1},
        "701": {"frame": "x01_options", "defaults": {"count_to": "701"}, "min_players": 1},
        "Killer": {"frame": "killer_options", "defaults": {"lifes": "3"}, "min_players": 2},
        "Shanghai": {"frame": "shanghai_options", "defaults": {"rounds": "7"}, "min_players": 1},
        # Füge hier bei Bedarf weitere Spielmodi für Tests hinzu.
    }
    monkeypatch.setattr('core.gamemgr.GAME_CONFIG', mock_game_config)

    mock_settings_manager = MagicMock()
    mock_settings_manager.get.return_value = ["P1", "P2", "", ""] # für last_player_names

    mock_profile_manager = MagicMock()
    mock_profile1 = MagicMock()
    mock_profile1.name = "ProfA"
    mock_profile2 = MagicMock()
    mock_profile2.name = "ProfB"
    mock_profile_manager.get_profiles.return_value = [mock_profile1, mock_profile2]

    # Instanziiere den Dialog mit der echten, aber versteckten Wurzel
    dialog = GameSettingsDialog(tk_root, mock_settings_manager, mock_profile_manager)
    # update() ist notwendig, damit die Widgets gezeichnet und ihre Werte gesetzt werden
    # Setze Standardwerte, um ValueErrors zu vermeiden
    dialog.count_to_var.set("301")
    dialog.player_count_var.set("1") # Explizite Initialisierung der Spieleranzahl
    dialog.lifes_var.set("3")
    dialog.rounds_var.set("7")
    dialog.legs_to_win_var.set("1")
    dialog.sets_to_win_var.set("1")

    dialog.update()

    yield dialog, mock_settings_manager, mock_profile_manager

    # Aufräumen nach jedem Test
    if dialog and dialog.winfo_exists():
        dialog.destroy()

class TestGameSettingsDialog:
    """
    Testet die UI-Logik der GameSettingsDialog-Klasse isoliert.
    Verwendet eine echte, aber versteckte Tk-Instanz, um UI-Interaktionen
    zuverlässig zu testen, ohne Fenster anzuzeigen.
    """
    def test_initialization_and_default_state(self, dialog_setup):
        """Testet, ob der Dialog korrekt initialisiert wird und die Standardoptionen (X01) anzeigt."""
        dialog, mock_settings_manager, _ = dialog_setup
        mock_settings_manager.get.assert_called_with('last_player_names', ANY)

        # Prüfen, ob die Comboboxen die korrekten Werte haben
        assert dialog.player_name_entries[0].get() == "P1"
        assert dialog.player_name_entries[1].get() == "P2"

        # Prüfen, ob der korrekte Options-Frame sichtbar ist
        assert dialog.game_option_frames['x01_options'].grid_info()
        assert not dialog.game_option_frames['killer_options'].grid_info()
        assert not dialog.game_option_frames['shanghai_options'].grid_info()

    def test_set_game_changes_visible_options(self, dialog_setup):
        """Testet, ob bei einer Spielauswahl der korrekte Options-Frame angezeigt wird."""
        dialog, _, _ = dialog_setup
        # Simuliere die Auswahl von "Killer" durch den Benutzer
        dialog.game_var.set("Killer")
        # Löst den Callback aus, der die Frames umschaltet
        dialog._on_game_selected()
        dialog.update() # Verarbeite das Event

        # Überprüfe die Sichtbarkeit der Frames
        assert not dialog.game_option_frames['x01_options'].grid_info()
        assert dialog.game_option_frames['killer_options'].grid_info()

    def test_start_button_collects_data_and_sets_flag(self, dialog_setup):
        """Testet, ob der Start-Button die Daten korrekt sammelt und den Dialog schließt."""
        dialog, mock_settings_manager, _ = dialog_setup
        # Benutzereingaben simulieren
        dialog.player_count_var.set("2")
        dialog._on_player_count_changed() # Löst den Callback aus, um Entries zu aktivieren/deaktivieren
        dialog.player_name_entries[0].set("Martin")
        dialog.player_name_entries[1].set("Gemini")

        # Spieloptionen simulieren
        dialog.game_var.set("501")
        dialog._on_game_selected() # Callback manuell auslösen
        dialog.opt_out_var.set("Double") # Den Wert direkt über die Variable setzen

        # Klick auf den Start-Button simulieren
        dialog._on_start()
 
        # Überprüfe das Ergebnis
        assert dialog.was_started
        assert dialog.result is not None
        assert dialog.result['players'] == ["Martin", "Gemini"]
        assert dialog.result['game'] == "501"
        assert dialog.result['opt_out'] == "Double"

        expected_saved_names = ["Martin", "Gemini", "", ""]
        mock_settings_manager.set.assert_called_once_with('last_player_names', expected_saved_names)
        assert not dialog.winfo_exists(), "Der Dialog sollte nach dem Start geschlossen sein."

    def test_start_button_shows_error_on_duplicate_names(self, dialog_setup, monkeypatch):
        """Testet, ob ein Fehler angezeigt wird, wenn Spielernamen doppelt sind."""
        dialog, _, _ = dialog_setup
        mock_messagebox = MagicMock()
        monkeypatch.setattr('core.gamemgr.messagebox', mock_messagebox)

        dialog.player_count_var.set("2")
        dialog._on_player_count_changed()
        dialog.player_name_entries[0].set("Martin")
        dialog.player_name_entries[1].set("Martin") # Duplikat

        dialog._on_start()

        assert not dialog.was_started
        mock_messagebox.showerror.assert_called_once_with("Fehler", "Spielernamen müssen eindeutig sein.", parent=dialog)
        assert dialog.winfo_exists(), "Der Dialog sollte nach einem Fehler offen bleiben."

    def test_cancel_button_sets_flag_and_destroys(self, dialog_setup):
        """Testet, ob der Abbrechen-Button den Dialog korrekt beendet."""
        dialog, _, _ = dialog_setup
        dialog._on_cancel()
        assert not dialog.was_started
        assert dialog.result is None
        assert not dialog.winfo_exists(), "Der Dialog sollte nach dem Abbrechen geschlossen sein."
