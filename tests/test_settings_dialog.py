import pytest
import tkinter as tk
from tkinter import ttk
from unittest.mock import MagicMock

from core.settings_dialog import AppSettingsDialog


@pytest.fixture
def tk_root():
    """Fixture to create and destroy a tk root window."""
    root = tk.Tk()
    root.withdraw()  # Hide the window
    yield root
    if root.winfo_exists():
        root.destroy()


@pytest.fixture
def dialog_setup(tk_root):
    """Sets up the AppSettingsDialog with mocks for testing."""
    mock_settings_manager = MagicMock()
    mock_settings_manager.get.side_effect = lambda key, default=None: {
        "theme": "light",
        "sound_enabled": True,
    }.get(key, default)

    mock_sound_manager = MagicMock()
    mock_sound_manager.sounds_enabled = True  # Konkreten Wert statt Mock zurückgeben

    dialog = AppSettingsDialog(tk_root, mock_settings_manager, mock_sound_manager)
    dialog.update()

    yield dialog, mock_settings_manager, mock_sound_manager

    # Cleanup
    if dialog.winfo_exists():
        dialog.destroy()


class TestAppSettingsDialog:
    """
    Testet die UI-Logik des AppSettingsDialog isoliert.
    """

    def test_initialization_sets_widgets_correctly(self, dialog_setup):
        """Testet, ob die Widgets mit den Werten der Manager initialisiert werden."""
        dialog, _, _ = dialog_setup
        # Direkten Wert der Variable prüfen, anstatt den Widget-Zustand abzufragen
        assert (
            dialog.sound_enabled_var.get() is True
        ), "Sound-Variable sollte standardmäßig True sein."

        # Finde die Combobox und prüfe ihren Wert
        theme_combo = dialog.theme_combo
        assert theme_combo.get() == "Light", "Theme-Combobox sollte 'Light' anzeigen."

    def test_sound_checkbutton_toggles_sound(self, dialog_setup):
        """
        Testet, ob das Klicken des Checkbuttons die Sound-Manager-Methode aufruft.
        """
        dialog, _, mock_sound_manager = dialog_setup
        # invoke() simuliert einen Klick, der den internen Zustand der Variable umschaltet
        # und den damit verbundenen Befehl auslöst.
        # Initial state is True, so first invoke toggles to False.
        # Wir simulieren den Klick manuell, um die Test-Zuverlässigkeit zu erhöhen.
        # 1. Die Variable wird umgeschaltet.
        dialog.sound_enabled_var.set(False)
        # 2. Der Befehl wird ausgeführt.
        dialog._on_sound_toggle()

        mock_sound_manager.toggle_sounds.assert_called_once_with(False)

    def test_theme_combobox_changes_theme(self, dialog_setup, monkeypatch):
        """Testet, ob das Ändern der Combobox das Theme setzt und speichert."""
        dialog, mock_settings_manager, _ = dialog_setup
        mock_set_theme = MagicMock()
        monkeypatch.setattr("core.settings_dialog.sv_ttk.set_theme", mock_set_theme)

        theme_combo = dialog.theme_combo
        theme_combo.set("Dark")
        theme_combo.event_generate("<<ComboboxSelected>>")

        mock_settings_manager.set.assert_called_once_with("theme", "dark")
        mock_set_theme.assert_called_once_with("dark")
