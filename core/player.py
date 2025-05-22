import tkinter as tk
from tkinter import ttk
from . import scoreboard
from .scoreboard import ScoreBoard 


# SPIELERKLASSE
class Player:
    id = 1
    def __init__(self, root, name, game):
        self.name = name
        self.game = game
        self.round = game.round
        self.cricket_hits = {}
        self.atc_hit = {}
        self.atc_next_target = "1"
        self.cricket_score = 0 # Oder self.score umwidmen, siehe unten

        if self.game.name in ("Cricket", "Cut Throat"):
            self.score = 0 # Startpunktzahl bei Cricket ist 0
            # Definiere die relevanten Cricket-Ziele
            self.cricket_targets = ["20", "19", "18", "17", "16", "15", "Bull"]
            for target in self.cricket_targets:
                self.cricket_hits[target] = 0 # Initial 0 Treffer
        elif len(game.name) == 3: # x01 Spiele
            self.score = int(self.game.name)
        elif self.game.name == "Around the Clock": # Andere Spiele, die vielleicht bei 0 starten
            self.score = 0
            # Definiere die relevanten ATC-Ziele
            self.atc_targets = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "Bull"]
            for target in self.atc_targets:
                self.atc_hit[target] = 0 # Initial 0 Treffer

        self.id = Player.id
        Player.id = self.id+1        
        self.has_doubled_in = False
        self.throws = []
        self.sb = ScoreBoard(root, self, self.game)

    def __del__(self):
        self.sb.__del__()
        self.clear()

    def leave(self):
        self.game.leave(self.id)
        self.__del__()
        return

    def clear(self):
        Player.id -= 1


    def reset_turn(self):
        self.throws = []

    # Die alte update Methode könnte bleiben und nur für x01 genutzt werden,
    # oder man macht sie intelligenter:
    def update_score_value(self, value, subtract=True):
        if subtract:
            self.score -= value
        else:
            self.score += value
        self.sb.update_score(self.score)
