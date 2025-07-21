import json
from tkinter import filedialog, messagebox
import os

class SaveLoadManager:
    SAVE_FORMAT_VERSION = 2

    """
    Verwaltet das Speichern und Laden von Spielständen als statische Utility-Klasse.

    Diese Klasse enthält ausschließlich statische Methoden und wird nicht instanziiert.
    Sie ist verantwortlich für:
    - Das Sammeln aller relevanten Daten aus einer laufenden `Game`-Instanz.
    - Das Öffnen von Systemdialogen zum Auswählen von Speicher- oder Ladeorten.
    - Das Serialisieren des Spielzustands in eine JSON-Datei.
    - Das Deserialisieren einer JSON-Datei zurück in ein Python-Dictionary.
    - Das Wiederherstellen des Zustands einer `Game`-Instanz aus den geladenen Daten.
    """
    @staticmethod
    def _collect_game_data(game):
        """
        Sammelt den kompletten Spielzustand und packt ihn in ein Dictionary.

        Diese private Hilfsmethode durchläuft das `game`-Objekt und alle
        zugehörigen `player`-Objekte, um einen serialisierbaren "Schnappschuss"
        des Spiels zu erstellen.

        Args:
            game (Game): Die aktive Spielinstanz, die gespeichert werden soll.

        Returns:
            dict or None: Ein Dictionary, das den gesamten Spielzustand repräsentiert,
                          oder None, wenn kein Spiel übergeben wurde.
        """
        if not game:
            return None

        players_data = []
        for p in game.players:
            player_dict = {
                'name': p.name,
                'id': p.id,
                'score': p.score,
                'throws': p.throws,
                'stats': p.stats,
                'state': p.state, # Kapselt alle spielspezifischen Daten
            }
            players_data.append(player_dict)

        game_data = {
            'save_format_version': SaveLoadManager.SAVE_FORMAT_VERSION,
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
    def save_game_state(game, parent):
        """
        Orchestriert den Speichervorgang.

        Ruft `_collect_game_data` auf, öffnet einen "Speichern unter"-Dialog
        für den Benutzer und schreibt die resultierenden Daten in die
        ausgewählte JSON-Datei.

        Args:
            game (Game): Die zu speichernde Spielinstanz.
            parent (tk.Widget): Das übergeordnete Fenster für Dialoge.
        """
        game_data = SaveLoadManager._collect_game_data(game)
        if not game_data:
            messagebox.showerror("Fehler", "Keine Spieldaten zum Speichern.", parent=parent)
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
            messagebox.showinfo("Erfolg", f"Spiel erfolgreich gespeichert unter:\n{filepath}", parent=parent)
        except Exception as e:
            messagebox.showerror("Fehler beim Speichern", f"Das Spiel konnte nicht gespeichert werden.\nFehler: {e}", parent=parent)

    @staticmethod
    def load_game_data(parent):
        """
        Orchestriert den Ladevorgang von der Datei bis zum Dictionary.

        Öffnet einen "Öffnen"-Dialog, damit der Benutzer eine Speicherdatei
        auswählen kann. Liest die JSON-Datei und gibt ihren Inhalt als
        Python-Dictionary zurück.

        Returns:
            dict or None: Die geladenen Spieldaten als Dictionary oder None,
                          wenn der Vorgang abgebrochen wurde oder ein Fehler auftrat.
        Args:
            parent (tk.Widget): Das übergeordnete Fenster für Dialoge.
        """
        filepath = filedialog.askopenfilename(
            initialdir=os.path.join(os.path.expanduser('~'), 'Documents'),
            title="Spiel laden...",
            filetypes=(("JSON-Dateien", "*.json"), ("Alle Dateien", "*.*"))
        )

        if not filepath:
            return None  # User cancelled

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # --- Versionsprüfung ---
            file_version = data.get('save_format_version')
            if file_version is None:
                messagebox.showerror("Inkompatibler Spielstand", "Diese Speicherdatei ist veraltet und kann nicht geladen werden.", parent=parent)
                return None
            if file_version != SaveLoadManager.SAVE_FORMAT_VERSION:
                messagebox.showerror("Inkompatibler Spielstand", f"Diese Speicherdatei (Version {file_version}) ist nicht mit der aktuellen Programmversion (erwartet Version {SaveLoadManager.SAVE_FORMAT_VERSION}) kompatibel.", parent=parent)
                return None

            return data
        except Exception as e:
            messagebox.showerror("Fehler beim Laden", f"Das Spiel konnte nicht geladen werden.\nFehler: {e}", parent=parent)
            return None

    @staticmethod
    def restore_game_state(game, data):
        """
        Stellt den Zustand eines Game-Objekts aus geladenen Daten wieder her.

        Diese Methode nimmt eine neu erstellte `Game`-Instanz und das geladene
        `data`-Dictionary und überschreibt die Attribute des Spiels und seiner
        Spieler mit den geladenen Werten. Anschließend wird die Benutzeroberfläche
        (Scoreboards) aktualisiert, um den wiederhergestellten Zustand anzuzeigen.

        Args:
            game (Game): Die neue Spielinstanz, deren Zustand wiederhergestellt wird.
            data (dict): Das Dictionary mit den geladenen Spieldaten.
        """
        game.round = data['round']
        game.current = data['current_player_index']
        for i, p_data in enumerate(data['players']):
            if i < len(game.players):
                player = game.players[i]
                # Kerndaten wiederherstellen
                player.name = p_data.get('name', player.name)
                player.id = p_data.get('id', player.id)
                player.score = p_data.get('score', player.score)
                player.throws = p_data.get('throws', [])
                player.stats = p_data.get('stats', {})
                # Spielspezifischen Zustand wiederherstellen
                player.state.update(p_data.get('state', {}))

        # --- UI-Zustand nach dem Laden wiederherstellen ---
        for player in game.players:
            if player.sb:  # Sicherstellen, dass das Scoreboard existiert
                # Aktualisiert die Hauptanzeige (Punkte, Leben, nächstes Ziel etc.)
                player.sb.update_score(player.score)
                # Aktualisiert spezifische Anzeigen wie Cricket-Treffer
                if hasattr(player.sb, 'update_display'):
                    player.sb.update_display(player.state['hits'], player.score)