#!python3 
# -*- coding: utf-8 -*-

import tkinter as tk 
from tkinter import ttk, messagebox, Menu
from PIL import Image, ImageTk
import sys
import sv_ttk
from core.settings_manager import SettingsManager
import pathlib
from core.gamemgr import GameManager
from core.game import Game
from core.dartboard import DartBoard
from core.save_load_manager import SaveLoadManager
from core.sound_manager import SoundManager
from core.player_stats_manager import PlayerStatsManager
from core.highscore_manager import HighscoreManager
from core.settings_dialog import AppSettingsDialog

def get_asset_path(relative_path):
    """
    Gibt den korrekten Pfad zu einer Asset-Datei zurück, egal ob das Skript
    als normale .py-Datei oder als gepackte Anwendung (PyInstaller) läuft.
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller erstellt einen temporären Ordner und speichert den Pfad in _MEIPASS
        base_path = pathlib.Path(sys._MEIPASS)
    else:
        # Wenn wir nicht im gepackten Modus sind, verwenden wir den normalen Pfad
        base_path = pathlib.Path(__file__).resolve().parent

    return base_path / pathlib.Path(relative_path)

class App:
    """
    Die Hauptanwendungsklasse, die als zentraler Orchestrator fungiert.

    Verantwortlichkeiten:
    - Initialisierung des Hauptfensters und der Menüs.
    - Verwaltung des Lebenszyklus der Anwendung.
    - Instanziierung und Koordination der verschiedenen Manager (Settings, Sound, etc.).
    - Starten, Laden und Beenden von Spielsitzungen (`Game`-Instanzen).
    """
    def __init__(self, root):
        self.root = root
        self.version = "v1.2.0"
        
        # Manager-Instanzen als Instanzvariablen
        self.settings_manager = SettingsManager()
        self.sound_manager = SoundManager(self.settings_manager, self.root)
        self.highscore_manager = HighscoreManager()
        self.player_stats_manager = PlayerStatsManager()
        self.game_instance = None

        # UI-Setup
        self._setup_window()
        self._setup_menu()
        self._setup_main_canvas()

    def _setup_window(self):
        # Theme anwenden (NACH dem Erstellen des root-Fensters, aber VOR dem Rest)
        theme = self.settings_manager.get('theme', 'light')
        # Sicherstellen, dass nur gültige Themes verwendet werden, um Abstürze zu vermeiden
        if theme not in ('light', 'dark'):
            print(f"Warnung: Ungültiges Theme '{theme}' in den Einstellungen gefunden. Fallback auf 'light'.")
            theme = 'light'
            self.settings_manager.set('theme', 'light') # Korrigiert die Einstellung für zukünftige Starts
        sv_ttk.set_theme(theme)

        self.root.geometry("300x300")
        self.root.title(f"Dartcounter {self.version}")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)

    def _setup_menu(self):
        menu_bar = Menu(self.root)
        file_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Datei", menu=file_menu)
        file_menu.add_command(label="Neues Spiel", command=self.new_game)
        file_menu.add_command(label="Spiel laden", command=self.load_game)
        file_menu.add_separator()
        file_menu.add_command(label="Spiel speichern", command=self.save_game)
        file_menu.add_separator()
        file_menu.add_command(label="Einstellungen", command=self.open_settings_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Spielerstatistiken", command=self.show_player_stats)
        file_menu.add_command(label="Highscores", command=self.show_highscores)
        file_menu.add_separator()
        file_menu.add_command(label="Spiel beenden", command=self.quit_game)
        about_menu = Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Über", menu=about_menu)
        about_menu.add_command(label="Über Dartcounter", command=self.about)
        self.root.config(menu=menu_bar)

    def _setup_main_canvas(self):
        assets_base_dir = get_asset_path("assets")
        image_path = assets_base_dir / "darthead.png"
        try:
            image = Image.open(image_path)
        except FileNotFoundError:
            messagebox.showerror("Fehler", f"Image nicht gefunden: {image_path}", parent=self.root)
            self.root.quit()
            return
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden des Images: {e}", parent=self.root)
            self.root.quit()
            return

        new_size = (275, 275)
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized)
        canvas = tk.Canvas(self.root, width=new_size[0], height=new_size[1])
        canvas.pack(fill="both", expand=True)
        x_pos = (300 - new_size[0]) // 2
        y_pos = (300 - new_size[1]) // 2
        canvas.create_image(x_pos, y_pos, image=photo, anchor=tk.NW)
        canvas.image = photo
        canvas.bind("<Button-1>", lambda e: self.new_game())

    def _check_and_close_existing_game(self, title, message):
        """Prüft, ob ein Spiel läuft, fragt den Benutzer und beendet es ggf."""
        if self.game_instance and not self.game_instance.end:
            if not messagebox.askyesno(title, message, parent=self.root):
                return False  # User cancelled
            self.game_instance.destroy() # Explizit die Ressourcen des Spiels freigeben
            self.game_instance = None
        return True  # OK to proceed

    def _initialize_game_session(self, game_options, player_names):
        """Erstellt die Game-Instanz, die ihre eigene UI initialisiert."""
        return Game(self.root, game_options, player_names, self.sound_manager, self.highscore_manager, self.player_stats_manager)

    def _create_game_options(self, source):
        """Erstellt ein standardisiertes game_options-Dictionary aus verschiedenen Quellen."""
        # Wir verwenden Duck-Typing (hasattr), da isinstance in Tests mit
        # gemockten Klassen fehlschlägt. Dies ist robuster.
        if hasattr(source, 'configure_game'):
            return {
                "name": source.game,
                "opt_in": source.opt_in,
                "opt_out": source.opt_out,
                "opt_atc": source.opt_atc,
                "count_to": source.count_to,
                "lifes": source.lifes,
                "rounds": source.rounds
            }
        # Annahme: source ist ein Dictionary aus einer Speicherdatei
        return {
            "name": source['game_name'],
            "opt_in": source['opt_in'],
            "opt_out": source['opt_out'],
            "opt_atc": source['opt_atc'],
            "count_to": str(source['count_to']),
            "lifes": str(source['lifes']),
            "rounds": str(source['rounds'])
        }

    def new_game(self):
        """Startet den Workflow zum Erstellen eines neuen Spiels."""
        if not self._check_and_close_existing_game("Neues Spiel", "Ein Spiel läuft bereits. Möchtest du es beenden und ein neues starten?"):
            return

        self.root.withdraw()
        gm = GameManager(self.sound_manager, self.settings_manager)

        if gm.configure_game(self.root):
            game_options = self._create_game_options(gm)
            self.game_instance = self._initialize_game_session(game_options, gm.players)
            self.game_instance.announce_current_player_turn()
        else:
            self.root.deiconify()

    def load_game(self):
        """Startet den Workflow zum Laden eines gespeicherten Spiels."""
        if not self._check_and_close_existing_game("Spiel laden", "Ein Spiel läuft bereits. Möchtest du es beenden und ein anderes laden?"):
            return

        data = SaveLoadManager.load_game_data(self.root)
        if not data:
            return

        self.root.withdraw()
        game_options = self._create_game_options(data)
        player_names = [p['name'] for p in data['players']]

        loaded_game = self._initialize_game_session(game_options, player_names)
        SaveLoadManager.restore_game_state(loaded_game, data)
        self.game_instance = loaded_game
        self.game_instance.announce_current_player_turn()

    def open_settings_dialog(self):
        """Öffnet einen Dialog für globale Anwendungseinstellungen."""
        dialog = AppSettingsDialog(self.root, self.settings_manager, self.sound_manager)
        self.root.wait_window(dialog)

    def save_game(self):
        """Speichert den Zustand des aktuell laufenden Spiels."""
        # Spiel kann nur gespeichert werden, wenn eine Instanz existiert, das Spiel nicht beendet ist UND das Dartboard-Fenster (db) noch existiert.
        if self.game_instance and not self.game_instance.end and self.game_instance.db:
            SaveLoadManager.save_game_state(self.game_instance, self.root)
        else:
            messagebox.showinfo("Spiel speichern", "Es läuft kein aktives Spiel, das gespeichert werden könnte.", parent=self.root)

    def show_highscores(self):
        """Öffnet das Fenster zur Anzeige der Highscores."""
        if self.highscore_manager:
            self.highscore_manager.show_highscores_window(self.root)

    def show_player_stats(self):
        """Öffnet das Fenster zur Anzeige der Spielerstatistiken."""
        self.player_stats_manager.show_stats_window(self.root)

    def quit_game(self):
        """Beendet die Anwendung nach einer Bestätigungsabfrage."""
        confirm = messagebox.askyesno("Programm beenden", "Dartcounter wirklich beenden?", parent=self.root)
        if confirm:
            if self.settings_manager:
                self.settings_manager.save_settings()
            if self.highscore_manager and self.highscore_manager.db_manager:
                self.highscore_manager.db_manager.close_connection()
            if self.game_instance:
                self.game_instance.destroy() # Explizit die Ressourcen des Spiels freigeben
            self.root.quit()

    def about(self):
        """Zeigt ein "Über"-Dialogfenster mit Informationen zur Anwendung an."""
        messagebox.showinfo(f"Dartcounter {self.version}", "Idee, Konzept und Code\nvon Martin Hehl\naka airnooweeda\n\nOptimiert mit KI-Unterstützung\n\n©2025 airnooweeda", parent=self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
    
