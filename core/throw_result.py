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

from dataclasses import dataclass
from typing import Literal

StatusType = Literal['ok', 'win', 'bust', 'info', 'warning', 'error', 'invalid_open', 'invalid_target']

@dataclass
class ThrowResult:
    """Eine Datenklasse, die das Ergebnis eines Wurfs strukturiert darstellt."""
    status: StatusType
    message: str | None = None
    sound: str | None = None # e.g., 'win', 'bust', 'hit'