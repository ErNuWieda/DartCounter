import tkinter as tk 
from tkinter import ttk
from . import scoreboard
from .scoreboard import ScoreBoard 

# SPIELERKLASSE
class Player:
    id = 1
    def __init__(self, root, name, game):
        self.name = name
        self.game_name = game.name
        self.hits = {}
        self.life_segment = ""
        self.lifes = game.lifes
        self.can_kill = False
        self.killer_throws = 0
        self.next_target = None
        self.score = 0
        self.game = game
        self.targets = self.game.targets

        if self.game.name in ('301', '501', '701'):
            self.score = int(self.game.name)
        elif self.targets:
            self.next_target = self.targets[0]
            for target in self.targets:
                self.hits[target] = 0 # Initial 0 Treffer    

        self.id = Player.id
        Player.id = self.id+1        
        self.has_opened = False
        self.throws = []
        self.sb = ScoreBoard(root, self, game)

    def __del__(self):
        self.sb.__del__()
        self.clear()

    def leave(self):
        self.game.leave(self.id)
        self.__del__()

    def clear(self):
        Player.id -= 1


    def reset_turn(self):
        self.throws = []

    def update_score_value(self, value, subtract=True):
        if subtract:
            self.score -= value
        else:
            self.score += value
        self.sb.update_score(self.score)
