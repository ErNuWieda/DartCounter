import tkinter as tk
import os
import sys
import pathlib
import time
from PIL import Image
from PIL import ImageGrab
from unittest.mock import MagicMock

# Pfad-Setup
SCRIPT_DIR = pathlib.Path(__file__).parent
sys.path.append(str(SCRIPT_DIR))

from core.dartboard import DartBoard
from core.settings_manager import SettingsManager

class ScreenshotTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Haupt-Root verstecken
        
        # Mocks für GVM
        self.mock_gvm = MagicMock()
        self.mock_gvm.settings_manager = SettingsManager()
        self.mock_gvm.game_options.name = "501"
        self.mock_gvm.game_options.opt_in = "Single"
        self.mock_gvm.game_options.opt_out = "Double"
        # Der Mock für den GameController muss vorhanden sein, damit Buttons gebunden werden können
        self.mock_gvm.game_controller = MagicMock()

    def _setup_board(self):
        """Erstellt eine frische Dartboard-Instanz für einen sauberen Screenshot."""
        if hasattr(self, 'db') and self.db.root and self.db.root.winfo_exists():
            self.db.root.destroy()
        self.db = DartBoard(self.mock_gvm, self.root)
        self.db.root.deiconify()
        # Warten, bis das Fenster vom Window-Manager wirklich gemappt wurde
        self.db.root.wait_visibility()
        self.db.root.update()

    def capture(self, filename):
        """Speichert einen Screenshot des Dartboard-Fensters."""
        output_path = SCRIPT_DIR / "assets" / filename
        output_path.parent.mkdir(exist_ok=True)

        try:
            # Fenster in den Vordergrund holen und zeichnen
            self.db.root.lift()
            self.db.root.update_idletasks()
            self.db.root.update()
            
            time.sleep(0.2)
            
            x = self.db.root.winfo_rootx()
            y = self.db.root.winfo_rooty()
            w = self.db.root.winfo_width()
            h = self.db.root.winfo_height()

            # Versuch 1: Klassischer Screenshot (funktioniert unter X11)
            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            img.save(output_path)
            print(f"✅ Screenshot gespeichert: {output_path}")

        except OSError:
            # Fallback für Wayland: Direkter Canvas-Export via Postscript
            print(f"⚠️ ImageGrab fehlgeschlagen (Wayland?). Nutze Canvas-Export-Fallback...")
            try:
                ps_path = output_path.with_suffix(".ps")
                # Exportiert nur den Canvas-Inhalt (ohne die Buttons unten), funktioniert ohne Screen-Access
                self.db.canvas.postscript(file=str(ps_path), colormode="color")
                
                # Postscript in PNG umwandeln (benötigt 'ghostscript' auf dem System)
                with Image.open(ps_path) as ps_img:
                    ps_img.save(output_path)
                ps_path.unlink() # Temporäre Datei löschen
                print(f"✅ Screenshot via Postscript erstellt: {output_path}")
            except Exception as e:
                print(f"\n❌ FEHLER beim Screenshot: {e}")
                if os.environ.get("XDG_SESSION_TYPE") == "wayland":
                    print("\n💡 HINWEIS: Unter Wayland ist der direkte Bildschirmzugriff gesperrt.")
                    print("Lösung 1: Gnome mit X11 starten (dein Plan 😉)")
                    print("Lösung 2: 'sudo apt install ghostscript' für den Postscript-Fallback.")
                    print("Lösung 3: GDK_BACKEND=x11 python3 capture_highlights.py")
            self.root.quit()
            sys.exit(1)
        

    def run_sequence(self, effects):
        """Arbeitet eine Liste von Effekten nacheinander ab."""
        if not effects:
            print("\n✨ Alle Screenshots wurden erfolgreich erstellt!")
            self.root.quit()
            return

        name, effect_func, filename = effects.pop(0)
        print(f"Verarbeite: {name}...")
        
        self._setup_board()
        effect_func()
        
        # Kurz warten bis der Effekt gezeichnet ist, dann capturen und weiter
        self.db.root.after(1000, lambda: self.capture(filename))
        self.db.root.after(1500, lambda: self.run_sequence(effects))

    def start(self, mode="all"):
        all_tasks = [
            ("180", lambda: self.db.show_180_effect(), "effect_180.png"),
            ("Big Fish", lambda: self.db.show_big_fish_effect(), "effect_big_fish.png"),
            ("No Score", lambda: self.db.show_no_score_effect(is_bust=False), "effect_no_score.png"),
            ("Low Score", lambda: self.db.show_low_score_effect(), "effect_low_score.png"),
            ("Bust", lambda: self.db.show_no_score_effect(is_bust=True), "effect_bust.png"),
        ]
        
        if mode != "all":
            tasks = [t for t in all_tasks if mode.lower() in t[0].lower().replace(" ", "")]
        else:
            tasks = all_tasks
            
        if not tasks:
            print(f"Fehler: Modus '{mode}' unbekannt.")
            return

        self.run_sequence(tasks)
        self.root.mainloop()

if __name__ == "__main__":
    # Abhängigkeit prüfen
    try:
        from PIL import ImageGrab
    except ImportError:
        print("Fehler: Pillow ist erforderlich. 'pip install Pillow'")
        sys.exit(1)

    tool = ScreenshotTool()
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    tool.start(mode)