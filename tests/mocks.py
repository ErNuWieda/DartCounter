from unittest.mock import MagicMock
from core.atc import ATC_TARGET_VALUES

class MockPlayer:

    """
    Eine generische Mock-Klasse für Player, die für die meisten Tests ausreicht.
    Sie kann in spezifischen Tests bei Bedarf angepasst werden.
    """
    _id_counter = 1

    def __init__(self, name, player_id=None, score=0, game_name="TestGame"):
        self.name = name
        self.id = player_id if player_id is not None else MockPlayer._id_counter
        MockPlayer._id_counter += 1
        
        self.score = score
        self.game_name = game_name
        self.throws = []
        self.sb = MagicMock()
        self.sb.update_score = MagicMock()
        self.sb.update_checkout_suggestion = MagicMock()

        # State-Dictionary für spielspezifische Attribute
        self.state = {
            'hits': {},  # Für Cricket, Micky, ATC etc.
            'life_segment': "",
            'can_kill': False,
            'next_target': None,
            'has_opened': True,
        }

        # Statistik-Dictionary
        self.stats = {
            'total_darts_thrown': 0,
            'total_score_thrown': 0,
            'checkout_opportunities': 0,
            'checkouts_successful': 0,
            'highest_finish': 0,
            'total_marks_scored': 0,
        }

        for i in range(1, 21):
             self.state['hits'][str(i)] = 0
        self.state['hits']['Bull'] = 0

        for target in ATC_TARGET_VALUES:
             self.state['hits'][target] = 0

    # --- Properties für den sicheren Zugriff auf das State-Dictionary ---
    @property
    def hits(self):
        return self.state.get('hits', {})

    @hits.setter
    def hits(self, value):
        self.state['hits'] = value

    @property
    def life_segment(self):
        return self.state.get('life_segment')

    @life_segment.setter
    def life_segment(self, value):
        self.state['life_segment'] = value

    @property
    def can_kill(self):
        return self.state.get('can_kill', False)

    @can_kill.setter
    def can_kill(self, value):
        self.state['can_kill'] = value

    @property
    def has_opened(self):
        return self.state.get('has_opened', False)

    @has_opened.setter
    def has_opened(self, value):
        self.state['has_opened'] = value

    def reset_turn(self):
        self.throws = []

    def get_total_darts_in_game(self):
        return 0

    def update_score_value(self, value, subtract=True):
        if subtract:
            self.score -= value
        else:
            self.score += value
        if self.sb:
            self.sb.update_score(self.score)

class MockGame:
    """Eine generische Mock-Klasse für Game, um den Spielzustand zu verwalten."""
    def __init__(self, name="TestGame", **kwargs):
        self.name = name
        self.end = False
        self.round = 1
        self.db = MagicMock()
        self.next_player = MagicMock()
        self.sound_manager = MagicMock()
        self.highscore_manager = MagicMock()
        self.targets = []
        
        # Setzt alle übergebenen Keyword-Argumente als Attribute
        for key, value in kwargs.items():
            setattr(self, key, value)

    def get_score(self, ring, segment):
        if ring == "Bullseye": return 50
        if ring == "Bull": return 25
        if ring == "Double": return segment * 2
        if ring == "Triple": return segment * 3
        if ring == "Single": return segment
        return 0