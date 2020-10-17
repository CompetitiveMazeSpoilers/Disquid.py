import copy
import io

import cairo
import PIL
from PIL import Image
import discord
from discord import Role
from moviepy.editor import *
import shutil

from model.memory import *

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
    rank_names: {int, str} = {
        0: 'Delinquent',
        100: 'Quartermaster',
        200: 'Squire',
        300: 'Marquis',
        400: 'Conquistador'
    }

    def __init__(self, uid: int, elo: int = 0, emoji: EmojiArray = default_emoji, name: str = 'dft', role: Role = None):
        self.uid = uid
        self.elo = elo
        self.emoji = copy.deepcopy(emoji)
        self.custom_emoji = ['empty', 'empty']
        self.name = name
        self.role = role

    def calc_elo(self, ply2, win: bool):
        p1 = (1.0 / (1.0 + pow(10, (ply2.elo - self.elo) / 100)))
        self.elo += round(30 * (1 - p1 if win else 0 - p1))
        if self.elo < 0:
            self.elo = 0

    def elo_string(self):
        s = ''
        d = Player.rank_names
        for num in d:
            if self.elo >= num:
                s = d[0]
        return s

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
                 c: int = standard_width, bases: [Position] = None, roles: [Role] = [None, None]):
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
        self.roles = roles

    def __str__(self):
        board_string = str(self.cache.latest)
        used_emojis = []
        for i, player in enumerate(self.players):
            # use highest priority emoji not used by another player
            base_emoji = player.emoji[0][1]
            tile_emoji = player.emoji[0][0]

            priority_count = 0
            while base_emoji in used_emojis and priority_count < len(player.emoji):
                priority_count += 1
                base_emoji = player.emoji[priority_count][1]
            used_emojis.append(base_emoji)

            priority_count = 0
            while tile_emoji in used_emojis and priority_count < len(player.emoji):
                priority_count += 1
                tile_emoji = player.emoji[priority_count][0]
            used_emojis.append(tile_emoji)

            board_string = board_string.replace(f'p{i + 1}b', base_emoji)
            board_string = board_string.replace(f'p{i + 1}', tile_emoji)
        # add message breaks to prevent passing character limit
        updated_board_string = ''
        for substring in board_string.split('#msg'):
            chars = 0
            for row_substring in substring.split('\n'):
                chars += len(row_substring)
                if chars > 2000:
                    updated_board_string += '#msg'
                    chars = 0
                updated_board_string += row_substring + '\n'
            updated_board_string += '#msg'
        updated_board_string = updated_board_string.replace('#msg\n#msg', '#msg')
        updated_board_string = updated_board_string.replace('#msg#msg', '#msg')
        if updated_board_string[-4:] == '#msg':
            updated_board_string = updated_board_string[:-4]
        return updated_board_string

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

    def to_video(self, temp_dir: Path, video_dir: Path, file_name: str = None):
        if not file_name:
            file_name = f'{self.players[0].name}-v-{self.players[1].name}'
        images = []
        for v, board in enumerate(self.cache.hist.board_history()):
            arr = str(board).replace('#msg', '').split('\n')
            final_arr = []
            for i, line in enumerate(arr):
                cell_arr = line.replace('||', '').split(':')
                for r_cell in cell_arr:
                    if r_cell == '':
                        cell_arr.remove(r_cell)
                for j, cell in enumerate(cell_arr):
                    if 'p1' not in cell and 'p2' not in cell:
                        cell_arr[j] = 'empty'
                for cell in cell_arr:
                    if 'p1' in cell or 'p2' in cell or 'p1b' in cell or 'p2b' in cell:
                        char_arr = cell.replace('p1b', '3').replace('p2b', '4').replace('p1', '1').replace('p2', '2')
                        for k, char in enumerate(char_arr):
                            if k == len(char_arr) - 1:
                                if char == '1':
                                    cell_arr[cell_arr.index(cell)] = 'p1'
                                elif char == '2':
                                    cell_arr[cell_arr.index(cell)] = 'p2'
                                elif char == '3':
                                    cell_arr[cell_arr.index(cell)] = 'p1b'
                                elif char == '4':
                                    cell_arr[cell_arr.index(cell)] = 'p2b'
                            else:
                                if char == '1':
                                    cell_arr.insert(cell_arr.index(cell), 'p1')
                                elif char == '2':
                                    cell_arr.insert(cell_arr.index(cell), 'p2')
                                elif char == '3':
                                    cell_arr.insert(cell_arr.index(cell), 'p1b')
                                elif char == '4':
                                    cell_arr.insert(cell_arr.index(cell), 'p2b')
                if not len(line) == 0:
                    final_arr.append(cell_arr)
            width = 647
            height = 324

            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            ctx = cairo.Context(surface)

            pat = cairo.SolidPattern(54.0 / 255, 57.0 / 255, 72.0 / 255)
            ctx.set_source(pat)
            ctx.rectangle(0, 0, width, height)
            ctx.fill()

            for i, line in enumerate(final_arr):
                for j, cell in enumerate(line):
                    if cell == 'empty':
                        ctx.set_source_rgb(32.0 / 255, 34.0 / 255, 37.0 / 255)
                    elif 'p1b' in cell:
                        ctx.set_source_rgb(128.0 / 255, 30.0 / 255, 32.0 / 255)
                    elif 'p2b' in cell:
                        ctx.set_source_rgb(64.0 / 255, 57.0 / 255, 193.0 / 255)
                    elif 'p1' in cell:
                        ctx.set_source_rgb(221.0 / 255, 46.0 / 255, 68.0 / 255)
                    elif 'p2' in cell:
                        ctx.set_source_rgb(85.0 / 255, 172.0 / 255, 238.0 / 255)
                    else:
                        continue
                    ctx.rectangle((j * 23) + 2, (i * 23) + 2, 22, 22)
                    ctx.fill()
            if not os.path.exists(temp_dir):
                os.mkdir(temp_dir)
            surface.write_to_png(str(temp_dir.joinpath(f'{v}.png').absolute()))
            images.append(str(temp_dir.joinpath(f'{v}.png').absolute()))
        clips = [ImageClip(m, duration=0.1) for m in images]
        concat_clip = concatenate_videoclips(clips)
        concat_clip.write_videofile(str(video_dir.joinpath(file_name)) + '.mp4', fps=10)
        shutil.rmtree(temp_dir)


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
            result += f'`V {r} {c}` : ' + emoji_at(r, c) + f' , rows {r}-{r + 4}, cols {c}-{c + 4},\n'
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
        if prefix == 'A' and len(args) == 3:
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

    @staticmethod
    def color_estimate(asset: []):
        """
        Takes in bytes of image and returns an estimation of the average color.
        :param asset: Bytes of image to be estimated.
        :return: Color estimation.
        """
        stream = io.BytesIO(asset)
        img = PIL.Image.open(stream)

        colors = Image.Image.getcolors(img, maxcolors=256 * 256 * 256)
        clumps = []
        min_dist = 30
        for color_item in colors:
            print(color_item)
            print(str(color_item) + str(len(clumps)))
            for i, (clump_item) in enumerate(clumps):
                if color_item in colors and Utility.color_distance(color_item[1], clump_item[1]) < min_dist:
                    clumps[i] = clump_item[0] + color_item[0], Utility.average_colors(clump_item[0], clump_item[1],
                                                                                      color_item[0], color_item[1])
                    colors.remove(color_item)
            if color_item in colors:
                clumps.append(color_item)

        most_color = clumps[0]
        for (count, color) in clumps:
            if count > most_color[0]:
                most_color = (count, color)
        rgb = most_color[1]
        return rgb[2] + rgb[1] * 256 + rgb[0] * 256 * 256

    @staticmethod
    def color_distance(color1: (int, int, int, int), color2: (int, int, int, int)):
        """
        Takes in two colors and determines the distance between them.
        :param color1: First color to compare (r,g,b,a)
        :param color2: Second color to compare (r,g,b,a)
        :return: Distance between the two colors
        """
        return pow(pow(color1[0] - color2[0], 2) + pow(color1[1] - color2[1], 2) + pow(color1[2] - color2[2], 2), .5)

    @staticmethod
    def average_colors(w1: float, color1: (int, int, int, int), w2: float, color2: (int, int, int, int)):
        """
        Takes in bytes of image and returns an estimation of the average color.
        :param color1: First color to average (r,g,b,a)
        :param color2: Second color to average (r,g,b,a)
        :param w1: weight of first color
        :param w2: weight of second color
        :return: Weighted average of the two colors
        """
        c1w = w1/(w1+w2)
        c2w = w2/(w1+w2)
        red = pow(c1w * pow(color1[0], 2) + c2w * pow(color2[0], 2), .5)
        green = pow(c1w * pow(color1[1], 2) + c2w * pow(color2[1], 2), .5)
        blue = pow(c1w * pow(color1[2], 2) + c2w * pow(color2[2], 2), .5)

        return round(red), round(green), round(blue), 255



class InvalidGameSetup(Exception):
    pass
