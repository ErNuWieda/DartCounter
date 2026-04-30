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

import pytest
from unittest.mock import MagicMock

# Klasse, die getestet wird
from core.tournament_manager import TournamentManager


@pytest.fixture
def tm_4_players():
    """Fixture für ein Turnier mit 4 Spielern."""
    # shuffle=False macht den Test deterministisch
    players = ["Alice", "Bob", "Charlie", "David"]
    return TournamentManager(
        player_names=players,
        game_mode="501",
        system="Doppel-K.o.",
        shuffle=False,
    )


@pytest.fixture
def tm_3_players():
    """Fixture für ein Turnier mit 3 Spielern (und einem Freilos)."""
    players = ["Alice", "Bob", "Charlie"]
    return TournamentManager(player_names=players, game_mode="501", system="Doppel-K.o.")


@pytest.fixture
def tm_8_players():
    """Fixture für ein Turnier mit 8 Spielern."""
    players = ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    return TournamentManager(player_names=players, game_mode="501", system="Doppel-K.o.")


@pytest.fixture
def tm_5_players():
    """Fixture für ein Turnier mit 5 Spielern (und Freilosen)."""
    players = ["Alice", "Bob", "Charlie", "David", "Eve"]
    return TournamentManager(
        player_names=players,
        game_mode="501",
        system="Doppel-K.o.",
        shuffle=False,
    )

def test_bye_handling_3_players_double_elim():
    """
    Testet das BYE-Handling bei 3 Spielern (Power of 2 = 4, also 1 BYE).
    Szenario: Alice vs Bob, Charlie hat ein Freilos.
    """
    players = ["Alice", "Bob", "Charlie"]
    tm = TournamentManager(players, "501", "Doppel-K.o.", shuffle=False)
    
    # In WB Runde 1 müssen 2 Matches existieren (1 echtes, 1 BYE)
    wb_r1 = tm.bracket["winners"][0]
    assert len(wb_r1) == 2
    
    # Alice sollte das BYE haben (da shuffle=False und num_byes=1 am Anfang nimmt)
    bye_match = next(m for m in wb_r1 if m["player2"] == "BYE")
    assert bye_match["player1"] == "Alice"
    assert bye_match["winner"] == "Alice"
    
    # Das spielbare Match finden
    active_match = tm.get_next_match()
    assert active_match["player1"] == "Bob"
    assert active_match["player2"] == "Charlie"
    
    # Bob gewinnt gegen Charlie
    tm.record_match_winner(active_match, "Bob")
    
    # Das WB-Finale muss nun Alice vs Bob sein
    wb_final = tm.get_next_match()
    assert {wb_final["player1"], wb_final["player2"]} == {"Alice", "Bob"}
    
    # Charlie muss im LB gelandet sein (gegen ein BYE, da nur 3 Spieler)
    lb_r1 = tm.bracket["losers"][0][0]
    assert lb_r1["player1"] == "Charlie"
    assert lb_r1["player2"] == "BYE"

def test_lb_progression_6_players():
    """
    Testet den komplexeren Feed-in-Mechanismus bei 6 Spielern.
    Hier kommen Verlierer aus verschiedenen WB-Runden in unterschiedliche LB-Runden.
    """
    players = ["P1", "P2", "P3", "P4", "P5", "P6"]
    tm = TournamentManager(players, "501", "Doppel-K.o.", shuffle=False)
    
    # WB R1 (shuffle=False): [P3-P4, P5-P6, P1-BYE, P2-BYE]
    # Die Strategie hängt Byes hinten an.
    wb_r1_matches = tm.bracket["winners"][0]

    # Resolve actual WB R1 matches (P3-P4, P5-P6)
    match_p3_p4 = next(m for m in wb_r1_matches if m["player1"] == "P3" and m["player2"] == "P4")
    tm.record_match_winner(match_p3_p4, "P3") # P4 loses
    match_p5_p6 = next(m for m in wb_r1_matches if m["player1"] == "P5" and m["player2"] == "P6")
    tm.record_match_winner(match_p5_p6, "P5") # P6 loses
    
    # WB R2: [P3 vs P5, P1 vs P2] (Byes rücken vor)
    wb_r2 = tm.bracket["winners"][1]
    match_p3_p5 = next(m for m in wb_r2 if m["player1"] == "P3" and m["player2"] == "P5")
    tm.record_match_winner(match_p3_p5, "P5") # P3 verliert -> LB R2
    match_p1_p2 = next(m for m in wb_r2 if m["player1"] == "P1" and m["player2"] == "P2")
    tm.record_match_winner(match_p1_p2, "P2") # P1 verliert -> LB R2
    
    # Check LB R1: Verlierer aus WB R1 m0 (P4) und m1 (P6)
    lb_r1 = tm.bracket["losers"][0]
    match_p4_p6_lb = next(m for m in lb_r1 if m["player1"] == "P4" and m["player2"] == "P6")
    assert {match_p4_p6_lb["player1"], match_p4_p6_lb["player2"]} == {"P4", "P6"}
    tm.record_match_winner(match_p4_p6_lb, "P4") # P4 gewinnt LB R1
    
    # Check LB R2: Gewinner LB R1 (P4) vs Verlierer WB R2 (P3)
    lb_r2 = tm.bracket["losers"][1]
    match_p4_p3_lb = next(m for m in lb_r2 if "P4" in [m["player1"], m["player2"]] and "P3" in [m["player1"], m["player2"]])
    tm.record_match_winner(match_p4_p3_lb, "P3") # P3 gewinnt

    # LB R2 m1 hat den Verlierer von P1-P2 (P1) gegen den Gewinner des anderen LB R1 Matches (BYE-BYE)
    match_p1_bye_lb = next(m for m in lb_r2 if "P1" in [m["player1"], m["player2"]])
    assert "BYE" in [match_p1_bye_lb.get("player1"), match_p1_bye_lb.get("player2")], "P1 hätte ein BYE im LB R2 erhalten müssen."
    tm.record_match_winner(match_p1_bye_lb, "P1")

    # Now check LB R3: P3 vs P1
    lb_r3 = tm.bracket["losers"][2]
    assert {lb_r3[0].get("player1"), lb_r3[0].get("player2")} == {"P3", "P1"}

def test_grand_final_reset_logic():
    """
    Testet explizit das Szenario, wenn der LB-Sieger das erste Finale gewinnt.
    Das Turnier darf dann noch nicht beendet sein.
    """
    players = ["Winner", "Loser"]
    # Benutze 4 Spieler, da das System für Grand Finals mindestens 2 WB Runden erwartet
    players = ["W1", "W2", "L1", "L2"]
    tm = TournamentManager(players, "501", "Doppel-K.o.", shuffle=False)
    
    # Alles durchspielen bis zum Grand Final
    while not tm.bracket["grand_final"]:
        m = tm.get_next_match()
        if not m: break # Safety break for unexpected empty matches
        # Assume player1 always wins to quickly get to the final
        tm.record_match_winner(m, m.get("player1"))

    gf1 = tm.bracket["grand_final"][0]
    lb_winner = gf1["player2"] # The player coming from the Losers Bracket
    wb_winner = gf1["player1"] # The player coming from the Winners Bracket

    # LB-Spieler gewinnt das erste Finale -> Bracket Reset
    tm.record_match_winner(gf1, lb_winner)
    assert tm.is_finished is False
    assert len(tm.bracket["grand_final"]) == 2 # A second grand final match should be created
    
    # The second final should now be available
    gf2 = tm.get_next_match()
    assert gf2 is not None
    assert gf2["winner"] is None

    # WB-Spieler gewinnt das zweite Finale -> Turnier Ende
    tm.record_match_winner(gf2, wb_winner)
    assert tm.is_finished is True and tm.winner == wb_winner

def test_initialization_with_invalid_player_count_raises_error():
    """Testet, ob bei weniger als 2 Spielern ein Fehler ausgelöst wird."""
    with pytest.raises(ValueError, match="mindestens 2 Spieler"):
        TournamentManager(player_names=["Player 1"], game_mode="501", system="K.o.")


def test_initialization_creates_double_elim_structure(tm_4_players):
    """Testet, ob die initiale Doppel-K.o.-Struktur korrekt erstellt wird."""
    tm = tm_4_players
    assert "winners" in tm.bracket
    assert "losers" in tm.bracket
    assert "grand_final" in tm.bracket
    assert len(tm.bracket["winners"]) == 2  # WB R1, WB Finale
    assert len(tm.bracket["winners"][0]) == 2  # 4 players -> 2 matches in R1
    assert len(tm.bracket["losers"]) == 2  # LB R1, LB Finale
    assert tm.bracket["grand_final"] == []


def test_get_next_match_priority(tm_4_players):
    """Testet, ob get_next_match die Brackets in der korrekten Reihenfolge durchsucht."""
    tm = tm_4_players

    # --- WB Runde 1 ---
    match1 = tm.get_next_match()
    assert {match1["player1"], match1["player2"]} == {"Alice", "Bob"}
    tm.record_match_winner(match1, "Alice")

    match2 = tm.get_next_match()
    assert {match2["player1"], match2["player2"]} == {"Charlie", "David"}
    tm.record_match_winner(match2, "Charlie")

    # --- WB Runde 2 (Finale) ---
    # Das nächste Match MUSS das WB-Finale sein, nicht das LB-Match.
    next_match_after_wb_r1 = tm.get_next_match()
    assert {
        next_match_after_wb_r1["player1"],
        next_match_after_wb_r1["player2"],
    } == {
        "Alice",
        "Charlie",
    }, "Next match should be WB final"
    tm.record_match_winner(next_match_after_wb_r1, "Alice")

    # --- LB Runde 1 ---
    # ERST JETZT sollte das LB-Match kommen.
    lb_match_1 = tm.get_next_match()
    assert lb_match_1 is not None
    # Die Verlierer der ersten Runde (Bob, David) sollten jetzt im Losers Bracket sein
    lb_players = {lb_match_1["player1"], lb_match_1["player2"]}
    assert lb_players == {
        "Bob",
        "David",
    }, "Losers bracket match has wrong players"


def test_record_match_winner_updates_bracket(tm_4_players):
    """Testet, ob record_match_winner den Gewinner im Turnierbaum korrekt einträgt."""
    match_to_play = tm_4_players.get_next_match()
    assert match_to_play is not None

    winner_name = match_to_play["player1"]
    tm_4_players.record_match_winner(match_to_play, winner_name)
    assert match_to_play["winner"] == winner_name


def test_record_match_winner_with_invalid_winner_raises_error():
    """Testet, ob ein Fehler ausgelöst wird, wenn ein ungültiger Gewinnername übergeben wird."""
    tm = TournamentManager(player_names=["Alice", "Bob"], game_mode="501", system="K.o.")
    match_to_play = tm.get_next_match()
    with pytest.raises(ValueError, match="ist kein Teilnehmer dieses Matches"):
        tm.record_match_winner(match_to_play, "Zelda")


def test_winner_advances_and_loser_drops(tm_4_players):
    """Testet, ob der Gewinner vorrückt und der Verlierer ins Losers Bracket fällt."""
    tm = tm_4_players
    # Mache den Test deterministisch
    p = tm.player_names
    tm.bracket["winners"][0] = [
        {"player1": p[0], "player2": p[1], "winner": None},  # Alice vs Bob
        {"player1": p[2], "player2": p[3], "winner": None},
    ]
    match1 = tm.bracket["winners"][0][0]
    winner, loser = match1["player1"], match1["player2"]

    # winner gewinnt
    tm.record_match_winner(match1, winner)

    # Prüfe Winners Bracket: Nächste Runde ist noch nicht erstellt, da Runde 1 nicht fertig ist.
    assert tm.bracket["winners"][1][0]["player1"] == winner

    # Prüfe Losers Bracket
    lb_match = tm.bracket["losers"][0][0]
    assert lb_match["player1"] == loser
    assert lb_match["player2"] is None  # Wartet auf anderen Verlierer


def test_get_tournament_winner_returns_none_if_not_finished(tm_4_players):
    """Testet, dass get_tournament_winner None zurückgibt, solange das Turnier läuft."""
    assert tm_4_players.winner is None, "Der Gewinner sollte anfangs None sein."
    assert tm_4_players.is_finished is False, "Das Turnier sollte anfangs nicht beendet sein."


def test_full_tournament_flow_4_players(tm_4_players):
    """Simuliert ein komplettes 4-Spieler Doppel-K.o.-Turnier."""
    tm = tm_4_players
    # Mache den Test deterministisch, indem die Paarungen manuell gesetzt und sortiert werden
    p = sorted(tm.player_names)
    tm.bracket["winners"][0] = [
        {"player1": p[0], "player2": p[1], "winner": None},  # A vs B
        {"player1": p[2], "player2": p[3], "winner": None},  # C vs D
    ]

    # --- WB Runde 1 ---
    match_wb_r1_m1 = tm.get_next_match()
    tm.record_match_winner(match_wb_r1_m1, p[0])  # A schlägt B

    match_wb_r1_m2 = tm.get_next_match()
    tm.record_match_winner(match_wb_r1_m2, p[2])  # C schlägt D

    # State check 1: WB R2 und LB R1 sollten gebildet sein
    assert tm.bracket["winners"][1][0]["player1"] == p[0]  # A
    assert tm.bracket["winners"][1][0]["player2"] == p[2]  # C
    assert {
        tm.bracket["losers"][0][0]["player1"],
        tm.bracket["losers"][0][0]["player2"],
    } == {p[1], p[3]}

    # --- WB Finale ---
    match_wb_r2_m1 = tm.get_next_match()
    tm.record_match_winner(match_wb_r2_m1, p[0])  # A schlägt C. A im Grand Final, C fällt.

    # --- LB Runde 1 ---
    match_lb_r1_m1 = tm.get_next_match()
    tm.record_match_winner(match_lb_r1_m1, p[1])  # B schlägt D. D ist eliminiert.

    # State check 2: LB Finale sollte gebildet sein (Verlierer WB-Finale vs. Gewinner LB-Runde)
    lb_final = tm.get_next_match()
    # Die Teilnehmer sind der Gewinner aus der vorherigen LB-Runde (p[1])
    # und der Verlierer aus dem WB-Finale (Charlie/p[2]).
    assert {lb_final["player1"], lb_final["player2"]} == {p[1], p[2]}

    # --- LB Finale ---
    tm.record_match_winner(lb_final, p[2])  # C schlägt B. C im Grand Final.

    # State check 3: Grand Final sollte gebildet sein
    grand_final = tm.get_next_match()
    assert {grand_final["player1"], grand_final["player2"]} == {
        p[0],
        p[2],
    }  # A vs C

    # --- Grand Final ---
    tm.record_match_winner(grand_final, p[0])  # A schlägt C
    assert tm.is_finished is True
    assert tm.winner == p[0], "Der Turniersieger wurde nicht korrekt ermittelt."


def test_bracket_reset_flow_4_players(tm_4_players):
    """Simuliert ein 4-Spieler-Turnier, bei dem der LB-Sieger das erste Grand Final gewinnt."""
    tm = tm_4_players
    p = sorted(tm.player_names)
    tm.bracket["winners"][0] = [
        {"player1": p[0], "player2": p[1], "winner": None},  # A vs B
        {"player1": p[2], "player2": p[3], "winner": None},  # C vs D
    ]

    # --- WB Runde 1 ---
    tm.record_match_winner(tm.get_next_match(), p[0])  # A schlägt B
    tm.record_match_winner(tm.get_next_match(), p[2])  # C schlägt D

    # --- WB Finale ---
    tm.record_match_winner(tm.get_next_match(), p[0])  # A schlägt C. A im Grand Final.

    # --- LB Runde 1 ---
    tm.record_match_winner(tm.get_next_match(), p[3])  # D schlägt B.

    # --- LB Finale ---
    tm.record_match_winner(tm.get_next_match(), p[2])  # C schlägt D. C im Grand Final.

    # --- Grand Final 1: LB-Sieger (C) gewinnt ---
    grand_final_1 = tm.get_next_match()
    tm.record_match_winner(grand_final_1, p[2])

    # State check: Bracket Reset -> Turnier läuft weiter, zweites Finale wurde erstellt
    assert tm.is_finished is False
    assert len(tm.bracket["grand_final"]) == 2

    # --- Grand Final 2 (Reset Match): C gewinnt erneut und wird Turniersieger ---
    tm.record_match_winner(tm.get_next_match(), p[2])
    assert tm.is_finished is True
    assert tm.winner == p[2]


def test_full_tournament_flow_8_players(tm_8_players):
    """
    Simuliert ein komplettes 8-Spieler Doppel-K.o.-Turnier, um die refaktorierte
    Bracket-Logik umfassend zu testen.
    """
    tm = tm_8_players
    p = sorted(tm.player_names)  # Deterministic player list

    # --- WB Runde 1 ---
    # Manuell die Matches setzen für einen deterministischen Testablauf
    tm.bracket["winners"][0] = [
        {"player1": p[0], "player2": p[1], "winner": None},  # P1 vs P2
        {"player1": p[2], "player2": p[3], "winner": None},  # P3 vs P4
        {"player1": p[4], "player2": p[5], "winner": None},  # P5 vs P6
        {"player1": p[6], "player2": p[7], "winner": None},  # P7 vs P8
    ]
    # Gewinner: p0, p2, p4, p6. Verlierer: p1, p3, p5, p7
    tm.record_match_winner(tm.bracket["winners"][0][0], p[0])
    tm.record_match_winner(tm.bracket["winners"][0][1], p[2])
    tm.record_match_winner(tm.bracket["winners"][0][2], p[4])
    tm.record_match_winner(tm.bracket["winners"][0][3], p[6])

    # Checkpoint 1: WB R2 und LB R1 sollten korrekt gebildet sein
    assert len(tm.bracket["winners"]) == 3  # R1, R2, Finale
    assert len(tm.bracket["losers"]) == 4  # LB R1, R2, R3, Finale
    assert {
        tm.bracket["winners"][1][0]["player1"],
        tm.bracket["winners"][1][0]["player2"],
    } == {p[0], p[2]}
    assert {
        tm.bracket["winners"][1][1]["player1"],
        tm.bracket["winners"][1][1]["player2"],
    } == {p[4], p[6]}
    assert {
        tm.bracket["losers"][0][0]["player1"],
        tm.bracket["losers"][0][0]["player2"],
    } == {p[1], p[3]}
    assert {
        tm.bracket["losers"][0][1]["player1"],
        tm.bracket["losers"][0][1]["player2"],
    } == {p[5], p[7]}

    # --- WB Runde 2 (Halbfinale) ---
    # Gewinner: p0, p4. Verlierer: p2, p6
    tm.record_match_winner(tm.bracket["winners"][1][0], p[0])
    tm.record_match_winner(tm.bracket["winners"][1][1], p[4])

    # --- LB Runde 1 ---
    # Gewinner: p1, p5. Eliminiert: p3, p7
    tm.record_match_winner(tm.bracket["losers"][0][0], p[1])
    tm.record_match_winner(tm.bracket["losers"][0][1], p[5])

    # Checkpoint 2: WB Finale und LB R2 sollten korrekt gebildet sein
    # Die Anzahl der Runden bleibt gleich, aber die Matches werden gefüllt.
    assert len(tm.bracket["winners"]) == 3
    assert (
        tm.bracket["winners"][2][0]["player1"] == p[0]
        and tm.bracket["winners"][2][0]["player2"] == p[4]
    )
    # LB R2: Gewinner LB R1 (p1, p5) vs Verlierer WB R2 (p2, p6)
    assert {
        tm.bracket["losers"][1][0]["player1"],
        tm.bracket["losers"][1][0]["player2"],
    } == {p[1], p[2]}
    assert {
        tm.bracket["losers"][1][1]["player1"],
        tm.bracket["losers"][1][1]["player2"],
    } == {p[5], p[6]}

    # --- WB Runde 3 (Finale) ---
    # Gewinner: p0. Verlierer: p4 (fällt ins LB-Finale)
    tm.record_match_winner(tm.bracket["winners"][2][0], p[0])

    # --- LB Runde 2 ---
    # Gewinner: p2, p6. Eliminiert: p1, p5
    tm.record_match_winner(tm.bracket["losers"][1][0], p[2])
    tm.record_match_winner(tm.bracket["losers"][1][1], p[6])

    # Checkpoint 3: LB R3 gebildet
    assert len(tm.bracket["losers"]) == 4
    assert {
        tm.bracket["losers"][2][0]["player1"],
        tm.bracket["losers"][2][0]["player2"],
    } == {p[2], p[6]}

    # --- LB Runde 3 ---
    # Gewinner: p2. Eliminiert: p6
    tm.record_match_winner(tm.bracket["losers"][2][0], p[2])

    # Checkpoint 4: LB Finale gebildet (Gewinner LB R3 vs Verlierer WB Finale)
    assert {
        tm.bracket["losers"][3][0]["player1"],
        tm.bracket["losers"][3][0]["player2"],
    } == {p[2], p[4]}

    # --- LB Runde 4 (Finale) ---
    # Gewinner: p4. Eliminiert: p2
    tm.record_match_winner(tm.bracket["losers"][3][0], p[4])

    # --- Grand Final ---
    grand_final = tm.get_next_match()
    assert {grand_final["player1"], grand_final["player2"]} == {p[0], p[4]}
    tm.record_match_winner(grand_final, p[0])
    assert tm.is_finished is True, "Das Turnier sollte nach dem Grand Final beendet sein."
    assert tm.winner == p[0]


def test_serialization_to_and_from_dict(tm_4_players):
    """Testet, ob der Manager-Zustand korrekt serialisiert und deserialisiert werden kann."""
    tm_original = tm_4_players

    match1 = tm_original.get_next_match()
    winner_name = match1["player1"]
    tm_original.record_match_winner(match1, winner_name)

    state_dict = tm_original.to_dict()
    # Simuliere den neuen Ladevorgang: erst erstellen, dann wiederherstellen
    tm_rehydrated = TournamentManager(
        player_names=state_dict["player_names"],
        game_mode=state_dict["game_mode"],
        system=state_dict["system"],
        shuffle=False,
    )
    tm_rehydrated.restore_state(state_dict)

    assert tm_rehydrated.to_dict() == tm_original.to_dict()

def test_double_elimination_walkover_behavior(tm_4_players):
    """
    Testet das Verhalten, wenn ein Spieler das Turnier abbricht (Walkover).
    Szenario: David wird 'gelöscht'/gibt auf. Alle seine Spiele müssen
    für die Gegner gewertet werden, damit das Turnier nicht hängen bleibt.
    """
    tm = tm_4_players
    p = sorted(tm.player_names) # A, B, C, David
    
    # 1. Runde WB: Alice schlägt Bob.
    tm.record_match_winner(tm.get_next_match(), "Alice")
    
    # 2. David ist das Problem. Er sollte gegen Charlie spielen.
    match_charlie_david = tm.get_next_match()
    assert "David" in [match_charlie_david["player1"], match_charlie_david["player2"]]
    
    # Wir simulieren den Walkover: Charlie gewinnt ohne Spiel.
    tm.record_match_winner(match_charlie_david, "Charlie")
    
    # Aktueller Stand: WB Final (A vs C), LB R1 (B vs D)
    # Das System priorisiert das Winners Bracket.
    
    match_wb_final = tm.get_next_match()
    assert {match_wb_final["player1"], match_wb_final["player2"]} == {"Alice", "Charlie"}
    tm.record_match_winner(match_wb_final, "Alice") # Alice im GF, Charlie -> LB Final
    
    # Jetzt LB R1: Bob vs David
    match_lb_r1 = tm.get_next_match()
    assert {match_lb_r1["player1"], match_lb_r1["player2"]} == {"Bob", "David"}
    tm.record_match_winner(match_lb_r1, "Bob") # Bob gewinnt, David raus
    
    # Jetzt LB Final: Charlie vs Bob
    match_lb_final = tm.get_next_match()
    assert {match_lb_final["player1"], match_lb_final["player2"]} == {"Charlie", "Bob"}
    tm.record_match_winner(match_lb_final, "Charlie") # Charlie im GF
    
    # Finale muss Alice vs Charlie sein
    next_match = tm.get_next_match()
    assert {next_match["player1"], next_match["player2"]} == {"Alice", "Charlie"}
    
    # Das Turnier bleibt nicht hängen (Orphaned Matches), solange wir 
    # einen Gewinner für den 'abwesenden' Spieler eintragen können.

def test_forfeit_player_automated_walkover(tm_4_players):
    """Testet die neue forfeit_player Methode für automatische Walkovers."""
    tm = tm_4_players
    # Initialbesetzung: Alice vs Bob, Charlie vs David (determinisiert)
    
    # David gibt sofort auf
    tm.forfeit_player("David")
    
    # In WB R1: Charlie vs David -> Charlie muss automatisch gewonnen haben
    wb_r1 = tm.bracket["winners"][0]
    charlie_match = next(m for m in wb_r1 if "Charlie" in [m["player1"], m["player2"]])
    assert charlie_match["winner"] == "Charlie"
    
    # David fällt ins LB. Wenn wir jetzt Bob verlieren lassen, landet er gegen David.
    # Da David bereits geforfeited hat, sollte auch dieses Match (LB) 
    # sofort entschieden werden, sobald Bob dort eintrifft.
    tm.record_match_winner(tm.get_next_match(), "Alice") # Bob verliert -> LB
    
    lb_r1 = tm.bracket["losers"][0][0]
    assert lb_r1["winner"] == "Bob", "Bob hätte kampflos gegen David gewinnen müssen."
