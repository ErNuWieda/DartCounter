# Dartcounter Deluxe
# Copyright (C) 2025 Martin Hehl (airnooweeda)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Definiert die SQLAlchemy-Datenmodelle für die Anwendung.
Diese Klassen repräsentieren die Tabellen in der Datenbank.
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base
from datetime import datetime

# Die 'declarative_base' ist die Basisklasse, von der alle unsere Modelle erben.
Base = declarative_base()


class Highscore(Base):
    __tablename__ = "highscores"
    id = Column(Integer, primary_key=True)
    game_mode = Column(String(50), nullable=False)
    player_name = Column(String(100), nullable=False)
    score_metric = Column(Float, nullable=False)
    date = Column(Date, nullable=False, default=datetime.utcnow)


class PlayerProfileORM(Base):
    """
    SQLAlchemy ORM-Modell für die Tabelle 'player_profiles'.
    Der Suffix 'ORM' wird verwendet, um Namenskollisionen mit der
    Anwendungs-Datenklasse 'PlayerProfile' zu vermeiden.
    """

    __tablename__ = "player_profiles"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    avatar_path = Column(String)
    dart_color = Column(String(7), nullable=False, default="#ff0000")
    is_ai = Column(Boolean, default=False)
    difficulty = Column(String(20))
    preferred_double = Column(Integer)
    # Speichert das statistische Modell der Wurfgenauigkeit als JSON
    accuracy_model = Column(JSONB)


class GameRecord(Base):
    __tablename__ = "game_records"
    id = Column(Integer, primary_key=True)
    # In einem idealen Schema wäre dies eine Fremdschlüsselbeziehung zur ID des Spielerprofils.
    # Wir bleiben hier aber beim bestehenden Schema, das den Namen verwendet.
    player_name = Column(String(100), nullable=False)
    game_mode = Column(String(50), nullable=False)
    game_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_win = Column(Boolean, nullable=False)
    average = Column(Float)
    mpr = Column(Float)
    checkout_percentage = Column(Float)
    highest_finish = Column(Integer)
    # JSONB wird für PostgreSQL verwendet, für andere DBs würde man JSON nehmen.
    all_throws_coords = Column(JSONB)

    def __repr__(self):
        return (
            f"<GameRecord(player='{self.player_name}', game='{self.game_mode}', win={self.is_win})>"
        )
