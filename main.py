#!/bin/python 
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, Menu
from PIL import Image, ImageTk
import pathlib
from core.gamemgr import GameManager

def setup_menu(root):
    menu_bar = Menu(root)
    file_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Datei", menu=file_menu)
    file_menu.add_command(label="Neues Spiel", command=new_game)
    file_menu.add_command(label="Spiel laden", command=load_game)
    file_menu.add_separator()
    file_menu.add_command(label="Spiel speichern", command=save_game)
    file_menu.add_separator()
    file_menu.add_command(label="Spiel beenden", command=quit_game)
    about_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Über", menu=about_menu)
    about_menu.add_command(label="Über Dartcounter", command=about)
    root.config(menu=menu_bar)


def new_game():
    root.withdraw()
    gm = GameManager(root)

def load_game():
    messagebox.showinfo("Spiel laden", "Noch nicht implementiert!")

def save_game():
    messagebox.showinfo("Spiel speichern", "Noch nicht implementiert!")

def quit_game():
    confirm = messagebox.askyesno("Programm beenden", "Dartcounter wirklich beenden?")
    if confirm:
        root.quit()

def about():
    messagebox.showinfo(f"Dartcounter {version}", "Idee, Konzept und Code\nvon Martin Hehl\naka airnooweeda\n\nOptimiert mit KI-Unterstützung\n\n©2025 airnooweeda")


if __name__ == "__main__":
    ASSETS_BASE_DIR = pathlib.Path(__file__).resolve().parent / "assets"    
    image_path = ASSETS_BASE_DIR / "darthead.png"
    version = "v1.1"


    # Fenster erstellen
    root = tk.Tk()
    root.geometry("300x300")
    root.title(f"Dartcounter {version}")
    root.resizable(False, False)
    root.protocol("WM_DELETE_WINDOW", quit_game)
    root.bind("<Escape>", lambda e: quit_game())


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

    # Bildschirmgröße
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    target_height = int(screen_height * 0.33)
    # Bild skalieren
    scale = target_height / image.height
    new_size = (int(image.width * scale), int(image.height * scale))
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
    