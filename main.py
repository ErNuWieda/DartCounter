#!python3 
# -*- coding: utf-8 -*-

import tkinter as tk 
from tkinter import ttk, messagebox, Menu
from PIL import Image, ImageTk
import sys
import sv_ttk
import pathlib
from core.gamemgr import GameManager
from core.game import Game
from core.dartboard import DartBoard
from core.save_load_manager import SaveLoadManager
from core.sound_manager import SoundManager
from core.highscore_manager import HighscoreManager
from core.settings_manager import SettingsManager

def get_asset_path(relative_path):
    """
    Gibt den korrekten Pfad zu einer Asset-Datei zurück, egal ob das Skript
    als normale .py-Datei oder als gepackte Anwendung (PyInstaller) läuft.
    """
    try:
        # PyInstaller erstellt einen temporären Ordner und speichert den Pfad in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Wenn wir nicht im gepackten Modus sind, verwenden wir den normalen Pfad
        base_path = pathlib.Path(__file__).resolve().parent

    return base_path / pathlib.Path(relative_path)

class App:
    def __init__(self, root):
        self.root = root
        self.version = "v1.1"
        
        # Manager-Instanzen als Instanzvariablen
        self.settings_manager = SettingsManager()
        self.sound_manager = SoundManager(self.settings_manager, self.root)
        self.highscore_manager = HighscoreManager()
        self.game_instance = None

        # UI-Setup
        self._setup_window()
        self._setup_menu()
        self._setup_main_canvas()

    def _setup_window(self):
        # Theme anwenden (NACH dem Erstellen des root-Fensters, aber VOR dem Rest)
        sv_ttk.set_theme(self.settings_manager.get('theme', 'light'))

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
            self.game_instance.__del__()
            self.game_instance = None
        return True  # OK to proceed

    def _initialize_game_session(self, game_options, player_names):
        """Erstellt die Game- und Dartboard-Instanzen und richtet sie ein."""
        spiel_instanz = Game(self.root, game_options, player_names, self.sound_manager, self.highscore_manager)
        db_instanz = DartBoard(spiel_instanz)
        spiel_instanz.db = db_instanz
        spiel_instanz.setup_scoreboards()
        return spiel_instanz

    def new_game(self):
        if not self._check_and_close_existing_game("Neues Spiel", "Ein Spiel läuft bereits. Möchtest du es beenden und ein neues starten?"):
            return

        self.root.withdraw()
        gm = GameManager(self.root, self.sound_manager, self.settings_manager)
        self.root.wait_window(gm.settings_dlg)

        if gm.was_started:
            game_options = {
                "name": gm.game,
                "opt_in": gm.opt_in,
                "opt_out": gm.opt_out,
                "opt_atc": gm.opt_atc,
                "count_to": gm.count_to,
                "lifes": gm.lifes,
                "rounds": gm.shanghai_rounds
            }
            self.game_instance = self._initialize_game_session(game_options, gm.players)
            self.game_instance.announce_current_player_turn()
        else:
            self.root.deiconify()

    def load_game(self):
        if not self._check_and_close_existing_game("Spiel laden", "Ein Spiel läuft bereits. Möchtest du es beenden und ein anderes laden?"):
            return

        data = SaveLoadManager.load_game_data(self.root)
        if not data:
            return

        self.root.withdraw()
        game_options = {
            "name": data['game_name'],
            "opt_in": data['opt_in'],
            "opt_out": data['opt_out'],
            "opt_atc": data['opt_atc'],
            "count_to": str(data['count_to']),
            "lifes": str(data['lifes']),
            "rounds": str(data['rounds'])
        }
        player_names = [p['name'] for p in data['players']]

        loaded_game = self._initialize_game_session(game_options, player_names)
        SaveLoadManager.restore_game_state(loaded_game, data)
        self.game_instance = loaded_game
        self.game_instance.announce_current_player_turn()

    def save_game(self):
        if self.game_instance and not self.game_instance.end:
            SaveLoadManager.save_game_state(self.game_instance, self.game_instance.db.root)
        else:
            messagebox.showinfo("Spiel speichern", "Es läuft kein aktives Spiel, das gespeichert werden könnte.", parent=self.root)

    def show_highscores(self):
        if self.highscore_manager:
            self.highscore_manager.show_highscores_window(self.root)

    def quit_game(self):
        confirm = messagebox.askyesno("Programm beenden", "Dartcounter wirklich beenden?", parent=self.root)
        if confirm:
            if self.settings_manager:
                self.settings_manager.save_settings()
            if self.game_instance:
                self.game_instance.__del__()
            self.root.quit()

    def about(self):
        messagebox.showinfo(f"Dartcounter {self.version}", "Idee, Konzept und Code\nvon Martin Hehl\naka airnooweeda\n\nOptimiert mit KI-Unterstützung\n\n©2025 airnooweeda", parent=self.root)



if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
    
