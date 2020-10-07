import copy

from model.memory import *
import discord

EmojiSet = Tuple[str, str]
EmojiArray = Tuple[EmojiSet, EmojiSet]


class Player(object):
    """
    Represents a player's profile, which is linked to every game they participate in.
    Contains information such as:
    - player id
    - rank
    - main/secondary emoji for base/territory
    - name acronym
    """

    default_emoji: EmojiArray = [[':red_square:', ':red_circle:'], [':blue_square:', ':blue_circle:']]

    def __init__(self, uid: int, rank: int, emoji: EmojiArray = default_emoji, name: str = 'dft'):
        self.uid = uid
        self.rank = rank
        self.emoji = copy.deepcopy(emoji)
        self.custom_emoji = ['empty', 'empty']
        self.name = name

    def __eq__(self, other):
        if isinstance(other, Player):
            return self.uid == other.uid
        if isinstance(other, int):
            return self.uid == other
        else:
            return NotImplemented


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

    def __init__(self, channel_id: discord.TextChannel.id, players: [Player], r: int = standard_height,
                 c: int = standard_width, bases: [Position] = None):
        self.channel_id = channel_id
        self.players = players
        if not bases:
            if r == Game.standard_height and c == Game.standard_width:
                bases = [((r // 2) - 1, 4), ((r // 2) - 1, (c - 1) - 5)]
            else:
                raise InvalidGameSetup
        self.history = History(r, c, bases, [])
        self.cache = Cache(self.history)
        self.draw_suggested = 0

    def __str__(self):
        board_string = str(self.cache.latest)
        for i, player in enumerate(self.players):
            board_string = board_string.replace(f'p{i + 1}b', player.emoji[i][1])
            board_string = board_string.replace(f'p{i + 1}', player.emoji[i][0])
        return board_string

    def get_board_string(self, board: Board):
        board_string = str(board)
        for i, player in enumerate(self.players):
            board_string = board_string.replace(f'p{i + 1}b', player.emoji[i][1])
            board_string = board_string.replace(f'p{i + 1}', player.emoji[i][0])
        return board_string

    def __eq__(self, other):
        if isinstance(other, Game):
            return self.channel_id == other.channel_id
        if isinstance(other, int):
            return self.channel_id == other
        else:
            return NotImplemented


class Utility:

    @staticmethod
    def format_locations(locs: [Position], game):
        """
        Turns a given set of locations into something recognizable
        by the end user on discord.
        """
        def emoji_at(i, j) -> str:
            # helper function
            board = game.cache.latest
            player = board[i][j].player
            if player == 0:
                # blank cell, use flag, add spoilers
                return '||' + Board.flag_array[i][j][1] + '||'
            else:
                # player cell stand-in code
                return game.players[player - 1].emoji[player - 1][0]

        result = ''
        for i, (r, c) in enumerate(locs, 1):
            result += f'`V {r} {c}` : ' + emoji_at(r, c) + f' , rows {r}-{r+4}, cols {c}-{c+4},\n'
        return result

    @staticmethod
    def read_move(player: int, action_text) -> Move:
        """
        Turns text into a move.
        :param action_text: Text that should be converted.
        :param player: Player doing the move.
        :return: The move based on the given text.
        """
        args = action_text.split()
        prefix = args[0]
        player_num = player
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
            if not len(args) == 2:
                raise InvalidMove
            try:
                if int(args[0]) < 0 or int(args[0]) > 13 or int(args[1]) < 0 or int(args[1]) > 27:
                    raise InvalidMove
            except ValueError:
                raise InvalidMove
            return Move(prefix, player_num, corner=(int(args[0]), int(args[1])))
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


class InvalidGameSetup(Exception):
    pass
