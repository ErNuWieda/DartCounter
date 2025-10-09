import tkinter as tk
import pytest
from tkinter import ttk
from unittest.mock import MagicMock, patch, call, ANY
from datetime import date

from core.game import HIGHSCORE_MODES
from core.highscore_manager import HighscoreManager


@pytest.mark.db
class TestHighscoreManager:
    """
    Testet den HighscoreManager.
    Verwendet eine echte, aber versteckte Tk-Instanz, um UI-Interaktionen
    zuverlässig zu testen, ohne Fenster anzuzeigen oder Tests aufzuhängen.
    """

    # Nutze die session-weite, unsichtbare tk_root_session Fixture aus conftest.py
    # anstelle einer eigenen Tk-Instanz pro Testklasse.
    # Dies wird automatisch an die Methoden übergeben, die es benötigen.
    # Wir müssen es hier nur deklarieren, damit pytest es erkennt.

    @pytest.fixture(autouse=True)
    def setup_method(self, tk_root_session):
        """Wird vor jedem Test ausgeführt."""
        self.created_dialogs = []
        original_toplevel = tk.Toplevel

        def toplevel_wrapper(*args, **kwargs):
            dialog = original_toplevel(*args, **kwargs)
            self.created_dialogs.append(dialog)
            return dialog

        # KORREKTE REIHENFOLGE & PFAD:
        # Zuerst die Methode auf der Originalklasse patchen.
        # Wir müssen den Pfad patchen, wo das Objekt *verwendet* wird.
        # In diesem Fall wird `wait_window` auch in `ui_utils` aufgerufen.
        self.patcher_wait = patch("core.ui_utils.tk.Toplevel.wait_window")
        self.mock_wait = self.patcher_wait.start()

        # ...DANN die gesamte Klasse durch unseren Wrapper ersetzen.
        self.patcher_toplevel = patch("tkinter.Toplevel", new=toplevel_wrapper)
        self.mock_toplevel = self.patcher_toplevel.start()

        # Patch für die neuen UI-Utilities
        patcher_ui_utils = patch("core.highscore_manager.ui_utils")
        self.mock_ui_utils = patcher_ui_utils.start()

        # Patch für die DatabaseManager-Abhängigkeit
        patcher_db = patch("core.highscore_manager.DatabaseManager")
        MockDatabaseManager = patcher_db.start()

        # Setze alle Mocks zurück, um saubere Tests zu gewährleisten
        MockDatabaseManager.reset_mock()

        # Erstelle eine Mock-Instanz des DatabaseManager
        self.mock_db_instance = MockDatabaseManager.return_value
        self.mock_db_instance.is_connected = True  # Standardmäßig verbunden

        self.highscore_manager = HighscoreManager(self.mock_db_instance)
        self.windows_to_destroy = []
        self.root = tk_root_session
        yield
        # --- Teardown ---
        self.patcher_toplevel.stop()
        self.patcher_wait.stop()
        patcher_ui_utils.stop()
        patcher_db.stop()
        for window in self.windows_to_destroy:
            if window and window.winfo_exists():
                window.destroy()

    def test_initialization_handles_no_db_connection(self, setup_method):
        """
        Testet, dass der Manager auch ohne DB-Verbindung initialisiert werden kann.
        """
        # Wir erstellen eine neue, getrennte Instanz für diesen spezifischen Testfall,
        # um die in setUp() erstellte Instanz nicht zu stören.
        mock_db_instance_disconnected = MagicMock()
        mock_db_instance_disconnected.is_connected = False

        highscore_manager = HighscoreManager(mock_db_instance_disconnected)

        # Die einzige Behauptung ist, dass die Initialisierung nicht abstürzt
        assert highscore_manager is not None

    def test_show_highscores_window_db_not_connected(self, setup_method):
        """Testet das Verhalten, wenn das Fenster ohne DB-Verbindung geöffnet wird."""
        self.mock_db_instance.is_connected = False
        window = self.highscore_manager.show_highscores_window(self.root)
        assert window is None, "Es sollte kein Fenster erstellt werden."
        self.mock_ui_utils.show_message.assert_called_once_with(
            "warning", ANY, ANY, parent=self.root
        )

    def test_show_highscores_window_successful(self, setup_method):
        """Testet die korrekte Erstellung des Highscore-Fensters und die Datenanzeige."""
        # Mock-Daten für verschiedene Spielmodi
        mock_scores_301 = [
            {
                "player_name": "Alice",
                "score_metric": 18,
                "date": date(2023, 1, 1),
            }
        ]
        mock_scores_cricket = [
            {
                "player_name": "Bob",
                "score_metric": 2.57,
                "date": date(2023, 1, 2),
            }
        ]

        # Erstelle eine dynamische Liste von Rückgabewerten für den Mock.
        # Dies stellt sicher, dass der Test auch bei Hinzufügen neuer Spielmodi funktioniert.
        side_effect_list = []
        for mode in HIGHSCORE_MODES:
            if mode == "301":
                side_effect_list.append(mock_scores_301)
            elif mode == "Cricket":
                side_effect_list.append(mock_scores_cricket)
            else:
                side_effect_list.append([])  # Leere Liste für alle anderen Modi

        self.mock_db_instance.get_scores.side_effect = side_effect_list

        window = self.highscore_manager.show_highscores_window(self.root)
        self.windows_to_destroy.append(window)
        window.update()  # Widgets zeichnen

        # Überprüfe den Widget-Typ über winfo_class(), das ist robuster in Tests.
        assert window.winfo_class() == "Toplevel"
        notebook = window.winfo_children()[0]
        assert notebook.winfo_class() == "TNotebook"

        # Finde die Indizes der relevanten Tabs dynamisch
        tab_texts = [notebook.tab(i, "text") for i in range(notebook.index("end"))]
        idx_301 = tab_texts.index("301")
        idx_cricket = tab_texts.index("Cricket")

        # Überprüfen, ob die Daten im ersten Tab (301) korrekt sind
        tree_301 = notebook.tabs()[idx_301]
        treeview_301 = window.nametowidget(tree_301).winfo_children()[0]
        assert len(treeview_301.get_children()) == 1
        item = treeview_301.item(treeview_301.get_children()[0])
        assert item["values"] == ["1.", "Alice", 18, "2023-01-01"]

        # Überprüfen, ob die Daten im Cricket-Tab korrekt sind
        tree_cricket = notebook.tabs()[idx_cricket]
        treeview_cricket = window.nametowidget(tree_cricket).winfo_children()[0]
        assert len(treeview_cricket.get_children()) == 1
        item_cricket = treeview_cricket.item(treeview_cricket.get_children()[0])
        assert item_cricket["values"] == ["1.", "Bob", "2.57", "2023-01-02"]

    def _find_button_by_text(self, window, text, retries=5, delay=100):
        """
        Sucht rekursiv nach einem Button-Widget innerhalb eines Parent-Widgets
        anhand seines Textes.
        """
        for _ in range(retries):
            for widget in window.winfo_children():
                if isinstance(widget, (ttk.Button, tk.Button)) and text in str(widget.cget("text")):
                    return widget
                # Rekursiver Aufruf, um auch in verschachtelten Frames zu suchen
                found = self._find_button_by_text(widget, text, retries=1)
                if found:
                    return found
            window.update_idletasks()
            window.after(delay)  # Kurze Pause, damit das UI sich aufbauen kann
        return None  # Button nicht gefunden

    def _wait_for_dialog(self, title, timeout_ms=1000):
        """
        Wartet explizit auf das Erscheinen eines neuen Toplevel-Dialogs
        mit einem bestimmten Titel.
        """
        start_time = self.root.tk.call("clock", "milliseconds")
        while True:
            self.root.update()
            for dialog in self.created_dialogs:
                if dialog.winfo_exists() and dialog.title() == title:
                    return dialog
            elapsed = self.root.tk.call("clock", "milliseconds") - start_time
            if elapsed > timeout_ms:
                pytest.fail(f"Timeout: Dialog mit Titel '{title}' nicht erschienen.")
            self.root.after(50)

    def test_prompt_and_reset_single_mode_confirmed(self, setup_method):
        """Testet das Zurücksetzen eines einzelnen Modus nach Bestätigung."""
        # Simuliere "Ja" im finalen Bestätigungsdialog
        self.mock_ui_utils.ask_question.return_value = True

        # Öffne das Highscore-Fenster
        window = self.highscore_manager.show_highscores_window(self.root)
        self.windows_to_destroy.append(window)
        window.update()

        # 1. Wähle den zweiten Tab (501) im Hauptfenster aus, BEVOR der Dialog geöffnet wird.
        notebook = window.winfo_children()[0]
        notebook.select(1)

        # 2. Klicke den Haupt-Reset-Button, um den Auswahl-Dialog zu öffnen
        reset_button = self._find_button_by_text(window, "zurücksetzen")
        assert reset_button is not None
        reset_button.invoke()

        # 3. Finde den neu erstellten modalen Dialog mit einer robusten Wartefunktion
        reset_dialog = self._wait_for_dialog("Highscores zurücksetzen")
        self.windows_to_destroy.append(reset_dialog)

        # 4. Finde den "Nur '501'"-Button im modalen Dialog und klicke ihn
        single_reset_button = self._find_button_by_text(reset_dialog, "Nur '501'")
        assert single_reset_button is not None, "Button zum Zurücksetzen des einzelnen Modus nicht gefunden."
        single_reset_button.invoke()

        # Überprüfe die Ergebnisse
        self.mock_ui_utils.ask_question.assert_called_once()
        self.mock_db_instance.reset_scores.assert_called_once_with("501")
        self.mock_ui_utils.show_message.assert_called_once()
        assert not window.winfo_exists(), "Das Highscore-Fenster sollte nach dem Reset geschlossen sein."
        assert not reset_dialog.winfo_exists(), "Der Reset-Dialog sollte nach dem Reset geschlossen sein."

    def test_prompt_and_reset_all_modes_confirmed(self, setup_method):
        """Testet das Zurücksetzen aller Modi nach Bestätigung."""
        self.mock_ui_utils.ask_question.return_value = True
        window = self.highscore_manager.show_highscores_window(self.root)
        self.windows_to_destroy.append(window)
        window.update()

        # 1. Klicke den Haupt-Reset-Button
        reset_button = self._find_button_by_text(window, "zurücksetzen")
        reset_button.invoke()

        # 2. Finde den modalen Dialog mit einer robusten Wartefunktion
        reset_dialog = self._wait_for_dialog("Highscores zurücksetzen")
        self.windows_to_destroy.append(reset_dialog)

        # 3. Finde den "Alle zurücksetzen"-Button und klicke ihn
        all_reset_button = self._find_button_by_text(reset_dialog, "Alle zurücksetzen")
        assert all_reset_button is not None, "Button 'Alle zurücksetzen' nicht gefunden."
        all_reset_button.invoke()

        self.mock_db_instance.reset_scores.assert_called_once_with(None)
        self.mock_ui_utils.show_message.assert_called_once()
        assert not window.winfo_exists()
        assert not reset_dialog.winfo_exists()

    def test_prompt_and_reset_cancelled(self, setup_method):
        """Testet, dass nichts passiert, wenn der Benutzer den Reset abbricht."""
        window = self.highscore_manager.show_highscores_window(self.root)
        self.windows_to_destroy.append(window)
        window.update()

        # 1. Klicke den Haupt-Reset-Button
        reset_button = self._find_button_by_text(window, "zurücksetzen")
        reset_button.invoke()

        # 2. Finde den modalen Dialog mit einer robusten Wartefunktion
        reset_dialog = self._wait_for_dialog("Highscores zurücksetzen")
        self.windows_to_destroy.append(reset_dialog)

        # 3. Finde den "Abbrechen"-Button und klicke ihn
        cancel_button = self._find_button_by_text(reset_dialog, "Abbrechen")
        assert cancel_button is not None
        cancel_button.invoke()

        self.mock_db_instance.reset_scores.assert_not_called()
        self.mock_ui_utils.show_message.assert_not_called()
        assert window.winfo_exists(), "Das Highscore-Fenster sollte nach dem Abbrechen geöffnet bleiben."
        assert not reset_dialog.winfo_exists(), "Der Reset-Dialog sollte nach dem Abbrechen geschlossen sein."
