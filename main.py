#!/usr/bin/python3 
# -*- coding: utf-8 -*-

import tkinter as tk 
from tkinter import ttk, messagebox, Menu
from PIL import Image, ImageTk
import sv_ttk
import pathlib
from core.gamemgr import GameManager
from core.game import Game
from core.dartboard import DartBoard
from core.save_load_manager import SaveLoadManager
from core.sound_manager import SoundManager
from core.highscore_manager import HighscoreManager
from core.settings_manager import SettingsManager

# Globale Variable, um die Instanz des laufenden Spiels zu halten
game_instance = None
sound_manager = None # Globale Instanz für den SoundManager
highscore_manager = None # Globale Instanz für den HighscoreManager
settings_manager = None # Globale Instanz für den SettingsManager

def setup_menu(root):
    menu_bar = Menu(root)
    file_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Datei", menu=file_menu)
    file_menu.add_command(label="Neues Spiel", command=new_game)
    file_menu.add_command(label="Spiel laden", command=load_game)
    file_menu.add_separator()
    file_menu.add_command(label="Spiel speichern", command=save_game)
    file_menu.add_separator()
    file_menu.add_command(label="Highscores", command=show_highscores)
    file_menu.add_separator()
    file_menu.add_command(label="Spiel beenden", command=quit_game)
    about_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Über", menu=about_menu)
    about_menu.add_command(label="Über Dartcounter", command=about)
    root.config(menu=menu_bar)


def new_game():
    global game_instance
    if game_instance and not game_instance.end:
        if not messagebox.askyesno("Neues Spiel", "Ein Spiel läuft bereits. Möchtest du es beenden und ein neues starten?"):
            return
        game_instance.__del__()
        game_instance = None

    root.withdraw()
    gm = GameManager(root, sound_manager, settings_manager)
    # Warten, bis das Einstellungsfenster geschlossen wird
    root.wait_window(gm.settings_dlg)

    if gm.was_started:
        game_options = (gm.game, gm.opt_in, gm.opt_out, gm.opt_atc, gm.count_to, gm.lifes, gm.shanghai_rounds)
        
        # Spiel- und Dartboard-Instanzen erstellen
        spiel_instanz = Game(root, game_options, gm.players, sound_manager, highscore_manager)
        db_instanz = DartBoard(spiel_instanz)
        spiel_instanz.db = db_instanz
        
        # Die neue Instanz als globale Instanz setzen
        game_instance = spiel_instanz
        
        # Das Spiel mit dem ersten Spieler starten
        game_instance.announce_current_player_turn()
    else:
        # Benutzer hat den Dialog geschlossen, ohne zu starten
        root.deiconify()

def load_game():
    global game_instance
    if game_instance and not game_instance.end:
        if not messagebox.askyesno("Spiel laden", "Ein Spiel läuft bereits. Möchtest du es beenden und ein anderes laden?"):
            return
        game_instance.__del__()
        game_instance = None

    data = SaveLoadManager.load_game_data()
    if not data:
        return  # Benutzer hat abgebrochen oder es gab einen Fehler

    root.withdraw()
    
    # Spieldaten aus den geladenen Daten extrahieren
    game_options = (
        data['game_name'], data['opt_in'], data['opt_out'], data['opt_atc'],
        str(data['count_to']), str(data['lifes']), str(data['rounds'])
    )
    player_names = [p['name'] for p in data['players']]

    # Spiel- und Dartboard-Instanzen erstellen und Zustand wiederherstellen
    loaded_game = Game(root, game_options, player_names, sound_manager, highscore_manager)
    db = DartBoard(loaded_game)
    loaded_game.db = db
    SaveLoadManager.restore_game_state(loaded_game, data)
    
    game_instance = loaded_game
    game_instance.announce_current_player_turn()

def save_game():
    if game_instance and not game_instance.end:
        SaveLoadManager.save_game_state(game_instance)
    else:
        messagebox.showinfo("Spiel speichern", "Es läuft kein aktives Spiel, das gespeichert werden könnte.")

def show_highscores():
    if highscore_manager:
        highscore_manager.show_highscores_window(root)

def quit_game():
    confirm = messagebox.askyesno("Programm beenden", "Dartcounter wirklich beenden?")
    if confirm:
        if settings_manager:
            settings_manager.save_settings()
        if game_instance:
            game_instance.__del__() # Spiel-Ressourcen sauber beenden
        root.quit()

def about():
    messagebox.showinfo(f"Dartcounter {version}", "Idee, Konzept und Code\nvon Martin Hehl\naka airnooweeda\n\nOptimiert mit KI-Unterstützung\n\n©2025 airnooweeda")


if __name__ == "__main__":
    ASSETS_BASE_DIR = pathlib.Path(__file__).resolve().parent / "assets"
    # Settings-Manager initialisieren (als ERSTES)
    settings_manager = SettingsManager()
    # Sound-Manager initialisieren (erfordert pygame)
    sound_manager = SoundManager(settings_manager) # SoundManager braucht SettingsManager
    # Highscore-Manager initialisieren
    highscore_manager = HighscoreManager()

    image_path = ASSETS_BASE_DIR / "darthead.png"
    version = "v1.1"

    # Fenster erstellen
    root = tk.Tk()

    # Theme anwenden (NACH dem Erstellen des root-Fensters, aber VOR dem Rest)
    sv_ttk.set_theme(settings_manager.get('theme', 'light'))


    root.geometry("300x300")
    root.title(f"Dartcounter {version}")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", quit_game)


    # Menü erstellen
    setup_menu(root)

    # Bild vorbereiten mit Fehlerbehandlung
    try:
        image = Image.open(image_path)
    except FileNotFoundError:
        messagebox.showerror("Fehler", f"Image nicht gefunden: {image_path}")
        root.quit()
        exit() # Beendet das Skript, da das Hauptbild fehlt
    except Exception as e:
        messagebox.showerror("Fehler", f"Fehler beim Laden des Images: {e}")
        root.quit()
        exit() # Beendet das Skript

    # Bild skalieren
    new_size = (275, 275)
    resized = image.resize(new_size, Image.Resampling.LANCZOS)
    photo = ImageTk.PhotoImage(resized)
    # Canvas erstellen
    canvas = tk.Canvas(root, width=new_size[0], height=new_size[1])
    canvas.pack(fill="both", expand=True)
    # Bild einfügen
    x_pos = (300 - new_size[0]) // 2
    y_pos = (300 - new_size[1]) // 2
    canvas.create_image(x_pos, y_pos, image=photo, anchor=tk.NW)
    canvas.image = photo
    canvas.bind("<Button-1>", lambda e: new_game())

    root.mainloop()
    
