from model.memory import *


class Utility:

    @staticmethod
    def read_move(player, action_text) -> Move:
        """
        Turns text into a move.
        :param action_text: Text that should be converted.
        :param player: Player doing the move.
        :return: The move based on the given text.
        """
        args = action_text.split()
        prefix = args[0]
        player_num = player.id_num
        del args[0]

        # acquire
        if prefix == 'A':
            locs = []
            for flag_code in args:
                loc = Utility.translate_flag(flag_code)
                if loc is None:
                    raise InvalidMove
                locs.append(loc)
            return Move(prefix, player_num, locs=locs)
        # vanquish
        elif prefix == 'V':
            if not len(args) == 3:
                raise InvalidMove
            if args[0] < 0 or args[0] > 27 or args[1] < 0 or args[1] > 13:
                raise InvalidMove
            return Move(prefix, player_num, corner=(args[0], args[1]))
        # conquer / conquest
        elif prefix == 'C' or prefix == 'Q':
            return Move(prefix, player_num)
        else:
            raise InvalidMove

    @staticmethod
    def translate_flag(flag):
        """
        Takes in a flag and turns it into coordinates.
        :param flag: The flag that should be translated.
        :return: Coordinates of a given flag on the default layout.
        """
        for r, row in enumerate(Board.flag_array):
            for c, flag_dec in enumerate(row):
                if flag in flag_dec[0]:
                    return r, c
        return


class Challenge(object):
    """
    Object created when one player wishes to start a game with another.
    Resolves to a new game when both players consent.
    """

    def __init__(self, p1: Player, p2: Player, game_args: [str] = ''):
        self.p1 = p1
        self.p2 = p2
        self.game_args = game_args

    def __eq__(self, other):
        if isinstance(other, Challenge):
            return self.p1 == other.p1 and self.p2 == other.p2
        else:
            return NotImplemented


class Game(object):
    """
    A game class that contains all information about the game
    it represents.
    """
    standard_width = 28
    standard_height = 14

    def __init__(self, players: [Player], r: int = standard_height, c: int = standard_width):
        self.players = players
        base1 = ((r // 2) - 1, 5)
        base2 = ((r // 2) - 1, (c - 1) - 5)
        self.history = History(r, c, [base1, base2], [])
        self.cache = Cache(self.history)

    def __str__(self):
        board_string = str(self.cache.latest)
        for i, player in enumerate(self.players):
            board_string.replace(f'p{i}b', player.emoji[0])
            board_string.replace(f'p{i}', player.emoji[1])
        return board_string
