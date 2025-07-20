import json
from tkinter import filedialog, messagebox
import os

class SaveLoadManager:
    """
    Verwaltet das Speichern und Laden von Spielständen in/aus JSON-Dateien.
    """
    @staticmethod
    def _collect_game_data(game):
        """Sammelt den kompletten Spielzustand und packt ihn in ein Dictionary."""
        if not game:
            return None

        players_data = []
        for p in game.players:
            player_dict = {
                'name': p.name,
                'id': p.id,
                'score': p.score,
                'throws': p.throws,
                'hits': p.hits,
                'stats': p.stats,
                'life_segment': p.life_segment,
                'lifes': p.lifes,
                'can_kill': p.can_kill,
                'killer_throws': p.killer_throws,
                'next_target': p.next_target,
                'has_opened': p.has_opened,
            }
            players_data.append(player_dict)

        game_data = {
            'game_name': game.name,
            'opt_in': game.opt_in,
            'opt_out': game.opt_out,
            'opt_atc': game.opt_atc,
            'count_to': game.count_to,
            'lifes': game.lifes,
            'rounds': game.rounds,
            'current_player_index': game.current,
            'round': game.round,
            'players': players_data,
        }
        return game_data

    @staticmethod
    def save_game_state(game):
        """Öffnet einen Speichern-Dialog und schreibt den Spielzustand in eine JSON-Datei."""
        game_data = SaveLoadManager._collect_game_data(game)
        if not game_data:
            messagebox.showerror("Fehler", "Keine Spieldaten zum Speichern.")
            return

        filepath = filedialog.asksaveasfilename(
            initialdir=os.path.join(os.path.expanduser('~'), 'Documents'),
            title="Spiel speichern unter...",
            defaultextension=".json",
            filetypes=(("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*"))
        )

        if not filepath:
            return  # User cancelled

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(game_data, f, indent=4)
            messagebox.showinfo("Erfolg", f"Spiel erfolgreich gespeichert unter:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Das Spiel konnte nicht gespeichert werden.\nFehler: {e}")

    @staticmethod
    def load_game_data():
        """Öffnet einen Laden-Dialog und liest Spieldaten aus einer JSON-Datei."""
        filepath = filedialog.askopenfilename(
            initialdir=os.path.join(os.path.expanduser('~'), 'Documents'),
            title="Spiel laden...",
            filetypes=(("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*"))
        )

        if not filepath:
            return None  # User cancelled

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", f"Das Spiel konnte nicht geladen werden.\nFehler: {e}")
            return None

    @staticmethod
    def restore_game_state(game, data):
        """Stellt den Zustand eines Game-Objekts aus geladenen Daten wieder her."""
        game.round = data['round']
        game.current = data['current_player_index']
        for i, p_data in enumerate(data['players']):
            if i < len(game.players):
                player = game.players[i]
                for key, value in p_data.items():
                    setattr(player, key, value)

        # --- UI-Zustand nach dem Laden wiederherstellen ---
        for player in game.players:
            if player.sb:  # Sicherstellen, dass das Scoreboard existiert
                # Aktualisiert die Hauptanzeige (Punkte, Leben, nächstes Ziel etc.)
                player.sb.update_score(player.score)
                # Aktualisiert spezifische Anzeigen wie Cricket-Treffer, falls vorhanden
                if hasattr(player.sb, 'update_display'):
                    player.sb.update_display(player.hits, player.score)