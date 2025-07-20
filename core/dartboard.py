import tkinter as tk 
from tkinter import messagebox
from PIL import Image, ImageTk
import math
import pathlib
import os


class DartBoard:
    """
    Verwaltet das interaktive Dartboard-Fenster.

    Diese Klasse ist verantwortlich für die Darstellung des Dartboards, die
    Erkennung von Würfen durch Mausklicks und die Kommunikation dieser Würfe
    an die zentrale `Game`-Instanz. Sie berechnet anhand von polaren Koordinaten,
    welcher Ring und welches Segment getroffen wurde.

    Class Constants:
        ASSETS_BASE_DIR (pathlib.Path): Der Basispfad zum 'assets'-Verzeichnis.
        DARTBOARD_PATH (pathlib.Path): Pfad zum Dartboard-Bild.
        DART_PATH (pathlib.Path): Pfad zum Dart-Symbolbild.
        ORIGINAL_SIZE (int): Die Kantenlänge des quadratischen Originalbildes in Pixel.
        RADIEN (dict): Ein Dictionary mit den Radien der verschiedenen Ringe
                       im Originalbild.
        SEGMENTS (list[int]): Eine Liste der Zahlenwerte der Segmente, geordnet
                              nach ihrem Winkel auf dem Board.

    Attributes:
        spiel (Game): Eine Referenz auf die übergeordnete Spielinstanz.
        root (tk.Toplevel): Das Fenster, in dem das Dartboard angezeigt wird.
        canvas (tk.Canvas): Das Canvas-Widget, das das Dartboard-Bild enthält.
    """
    ASSETS_BASE_DIR = pathlib.Path(__file__).resolve().parent.parent / "assets"    
    DARTBOARD_PATH = ASSETS_BASE_DIR / "dartboard.png"
    DART_PATH = ASSETS_BASE_DIR / "dart.png"
    ORIGINAL_SIZE = 2200  # Originalbildgröße in px
    RADIEN = {
        "bullseye": 30,
        "bull": 80,
        "triple_inner": 470,
        "triple_outer": 520,
        "double_inner": 785,
        "double_outer": 835,
        "außen": 836
    }
    SEGMENTS = [6, 13, 4, 18, 1,
                20, 5, 12, 9, 14,
                11, 8, 16, 7, 19,
                3, 17, 2, 15, 10][::1]

    def __init__(self, spiel):
        """
        Initialisiert das Dartboard-Fenster.

        Erstellt ein neues Toplevel-Fenster, lädt und skaliert die Bilder,
        erstellt das Canvas und die Buttons.

        Args:
            spiel (Game): Die Instanz des laufenden Spiels.
        """
        self.radien = DartBoard.RADIEN
        self.segments = DartBoard.SEGMENTS
        self.original_size = DartBoard.ORIGINAL_SIZE
        self.dartboard_path = DartBoard.DARTBOARD_PATH
        self.dart_path = DartBoard.DART_PATH
        self.skaliert = None
        self.center_x = None
        self.center_y = None
        self.spiel = spiel
        self.canvas = None # Wird in _create_board gesetzt
        self.root = tk.Toplevel()
        if len(spiel.name) == 3: # = x01-Spiele
            title = f"{spiel.name} - {spiel.opt_in}-in, {spiel.opt_out}-out"
        elif spiel.name == "Around the Clock":
            title = f"{spiel.name} - {spiel.opt_atc}"
        else:
            title = f"{spiel.name}"         
        self.root.title(title)
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)
        self.root.resizable(False, False)
        self._create_board()

        # Dart-Bild laden und vorbereiten
        self.dart_photo_image = None
        self.dart_image_ids_on_canvas = [] # Speichert IDs mehrerer Darts für den aktuellen Zug
        try:
            dart_img_pil = Image.open(self.dart_path)
            # Größe für das Dart-Bild definieren (z.B. 20x50 Pixel)
            # Passen Sie diese Dimensionen an das Seitenverhältnis Ihres dart.png und die gewünschte Größe an
            dart_display_width = 75
            dart_display_height = dart_display_width
            dart_img_pil_resized = dart_img_pil.resize((dart_display_width, dart_display_height), Image.Resampling.LANCZOS)
            self.dart_photo_image = ImageTk.PhotoImage(dart_img_pil_resized)
        except FileNotFoundError:
            print(f"Warnung: Dart-Bild nicht gefunden unter {self.dart_path}")
        except Exception as e:
            print(f"Warnung: Dart-Bild konnte nicht geladen werden: {e}")

    def clear_dart_images_from_canvas(self):
        """
        Entfernt alle für den aktuellen Zug angezeigten Dart-Bilder vom Canvas.
        """
        if self.canvas:
            for dart_id in self.dart_image_ids_on_canvas:
                self.canvas.delete(dart_id)
        self.dart_image_ids_on_canvas = []

    def clear_last_dart_image_from_canvas(self):
        """
        Entfernt das zuletzt hinzugefügte Dart-Bild vom Canvas.
        Wird von der Undo-Funktion verwendet.
        """
        if self.canvas and self.dart_image_ids_on_canvas:
            dart_id = self.dart_image_ids_on_canvas.pop()
            self.canvas.delete(dart_id)

    def quit_game(self):
        """
        Zeigt einen Bestätigungsdialog an und beendet das Spiel, wenn bestätigt.
        Delegiert die Bereinigung an die `Game`-Instanz.
        """
        confirm = messagebox.askyesno("Spiel beenden", "Soll das Spiel wirklich beendet werden?")
        if confirm:
            self.spiel.__del__()
            self.root.destroy()

    # POLARER WINKEL + DISTANZ
    def polar_angle(self, x, y):
        """
        Berechnet den polaren Winkel eines Punktes relativ zum Zentrum des Boards.

        Args:
            x (int): Die x-Koordinate des Klicks.
            y (int): Die y-Koordinate des Klicks.

        Returns:
            float: Der Winkel in Grad (0-360).
        """
        dx = x - self.center_x
        dy = self.center_y - y
        angle = math.atan2(dy, dx)
        return (math.degrees(angle) + 360) % 360

    def distance(self, x, y):
        """
        Berechnet die euklidische Distanz eines Punktes vom Zentrum des Boards.

        Args:
            x (int): Die x-Koordinate des Klicks.
            y (int): Die y-Koordinate des Klicks.

        Returns:
            float: Die Distanz in Pixeln.
        """
        return math.sqrt((x - self.center_x) ** 2 + (y - self.center_y) ** 2)

    # RING + SEGMENT ERMITTELN
    def get_ring_segment(self,x, y):
        """
        Ermittelt den getroffenen Ring und das Segment basierend auf Klickkoordinaten.

        Args:
            x (int): Die x-Koordinate des Klicks.
            y (int): Die y-Koordinate des Klicks.

        Returns:
            tuple[str, int]: Ein Tupel bestehend aus dem Namen des Rings und dem Zahlenwert des Segments.
        """
        dist = self.distance(x, y)
        angle = self.polar_angle(x, y)
        idx = int((angle+9) // 18) % 20
        segment = self.segments[idx]

        if dist <= self.skaliert["bullseye"]:
            return "Bullseye", 50
        elif dist <= self.skaliert["bull"]:
            return "Bull", 25
        elif self.skaliert["triple_inner"] < dist < self.skaliert["triple_outer"]:
            return "Triple", segment
        elif self.skaliert["double_inner"] < dist < self.skaliert["double_outer"]:
            return "Double", segment
        elif dist < self.skaliert["außen"]:
            return "Single", segment
        else:
            return "Miss", 0

    def on_click(self, event):
        """
        Event-Handler, der bei einem Mausklick auf das Canvas ausgelöst wird.

        Platziert ein Dart-Symbol an der Klickposition, ermittelt den Wurf
        und leitet ihn an die `Game`-Instanz zur Verarbeitung weiter.

        Args:
            event (tk.Event): Das von Tkinter generierte Event-Objekt.
        """
        # Neues Dart-Bild auf dem Canvas platzieren, falls das Bild geladen ist
        # event.x, event.y werden direkt für die visuelle Position des Dart-Bild-Zentrums verwendet.
        if self.dart_photo_image and self.canvas:
            # Der Anker ist standardmäßig tk.CENTER. Passen Sie x, y oder den Anker an,
            # wenn die "Spitze" des Dart-Bildes nicht dessen Zentrum ist (z.B. anchor=tk.W, wenn die Spitze links in der Mitte ist).
            dart_id = self.canvas.create_image(event.x-5, event.y-20, image=self.dart_photo_image)
            self.dart_image_ids_on_canvas.append(dart_id)

        ring, segment = self.get_ring_segment(event.x+7, event.y+7)
        msg = self.spiel.throw(ring, segment)
        if msg:
            if self.spiel.shanghai_finish:
                msg = "SHANGHAI-FINISH!\n"+msg
            tk.messagebox.showinfo("Dartcounter", msg)

    def _create_board(self):
        """
        Erstellt und konfiguriert das Dartboard-Canvas und die zugehörigen Widgets.

        Diese private Methode skaliert das Dartboard-Bild auf die Bildschirmhöhe,
        erstellt das Canvas, platziert das Bild und bindet den Klick-Handler.
        """
        # Bildschirmgröße
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        target_height = int(screen_height * 0.90)

        # Bildgröße skalieren
        SCALE = target_height / self.original_size
        # Radien skalieren
        self.skaliert = {k: int(v * SCALE) for k, v in self.radien.items()}
        # Bild vorbereiten
        image = Image.open(self.dartboard_path)
        # Bild skalieren
        new_size = (int(image.width * SCALE), int(image.height * SCALE))
        self.center_x, self.center_y = new_size[0] // 2, new_size[1] // 2
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(resized)
        # Canvas erstellen
        canvas = tk.Canvas(self.root, width=new_size[0], height=new_size[1])
        self.canvas = canvas # Canvas der Instanzvariable zuweisen
        canvas.pack(fill="both", expand=True)
        # Bild einfügen
        canvas.create_image(0, 0, image=photo, anchor=tk.NW)
        canvas.image = photo

        canvas.bind("<Button-1>", self.on_click)
        # Buttons erstellen
        btn_frame = tk.Frame(self.root)
        btn_frame.pack() 
        undo_button = tk.Button(btn_frame, text=" Zurück  ", fg="red", command=self.spiel.undo)
        undo_button.pack(pady=5)
        done_button = tk.Button(btn_frame, text=" Weiter  ", fg="green", command=self.spiel.next_player)
        done_button.pack(pady=5)
        quit_button = tk.Button(btn_frame, text="Beenden", command=self.quit_game)
        quit_button.pack(pady=5)

        canvas.create_window(
            new_size[0], new_size[1],
            window=btn_frame,
            anchor="se"
        )
        
