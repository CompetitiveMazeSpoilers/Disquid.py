import json
import math
import os
from collections import deque
from functools import partial
from heapq import heappush, heappop
from pathlib import Path
from typing import Tuple

Flag = ([str], str)
Position = Tuple[int, int]

hardcoded_board = '(<gu)(<pm)(<gf)(<pg)(<mk)(<va)(<dz)(<kz)(<np)(vu)(cu)(om)(pr)(by)(sj)(dm)(gg)(ge)(mq)(>np)(>kz)(' \
                  '>dz)(>va)(>mk)(>pg)(>gf)(>pm)(>gu)\n(<bl)(<as)(<cd)(<tz)(<zm)(<pt)(<gt)(<kg)(<mo)(sx)(gw)(ph)(dj)(' \
                  'st)(is)(fo)(no)(ax)(bv)(>mo)(>kg)(>gt)(>pt)(>zm)(>tz)(>cd)(>as)(>bl)\n(<gd)(<gy)(<cg)(<bn)(<qa)(' \
                  '<md)(<bb)(<kr)(<tn)(mg)(bs)(bj)(cz)(ki)(gi)(se)(fi)(dk)([england,en,eng],england)(>tn)(>kr)(>bb)(' \
                  '>md)(>qa)(>bn)(>cg)(>gy)(>gd)\n(<ba)(<mh)(<bi)([<scotland,<scot],scotland)(<mn)(<nf)(<sn)(<im)(' \
                  '<xk)(bz)(mv)(il)(uz)(nc)(ug)(cr)(mr)(nr)(aw)(>xk)(>im)(>sn)(>nf)(>mn)([>scotland,>scot],' \
                  'scotland)(>bi)(>mh)(>ba)\n(<nu)(<bm)(<to)(<ws)(<cp)(<td)(<be)(<aq)(<cn)(et)(si)(bo)(py)(ao)(ht)(' \
                  'ar)(pf)(ea)(hr)(>cn)(>aq)(>be)(>td)(>cp)(>ws)(>to)(>bm)(>nu)\n(<tf)(<ac)(<hm)(<vg)(<ie)(<pe)(<fr)(' \
                  '<lc)(<fm)(tj)(sy)(la)(bw)(bf)(gl)(gm)(az)(in)(eg)(>fm)(>lc)(>fr)(>pe)(>ie)(>vg)(>hm)(>ac)(>tf)\n(' \
                  '<sh)(<ck)(<fk)(<ky)([plr1],player1)([plr1],player1)(<gn)(<bd)(<vn)(mu)(ru)(sl)(lt)(mc)(ua)(ye)(' \
                  'am)(lu)(at)(>vn)(>bd)(>gn)([plr2],player2)([plr2],player2)(>ky)(>fk)(>ck)(>sh)\n(<pn)(<ms)(<nz)(' \
                  '<au)([plr1],player1)([plr1],player1)(<ci)(<jp)(<so)(lv)(hu)(nl)(ga)(pl)(id)(de)(ee)(bg)(co)(>so)(' \
                  '>jp)(>ci)([plr2],player2)([plr2],player2)(>au)(>nz)(>ms)(>pn)\n(<gs)(<ai)(<ta)(<tc)(<ml)(<ng)(' \
                  '<it)(<pw)(<ma)(ir)(ve)(ly)(th)(sm)(li)(ne)(gh)(hn)(lb)(>ma)(>pw)(>it)(>ng)(>ml)(>tc)(>ta)(>ai)(' \
                  '>gs)\n(<tv)(<fj)(<wf)(<tw)(<mf)(<ro)(<cm)(<hk)(<eu)(sk)(es)(sv)(ls)(sg)([wales,wa],wales)(ni)(iq)(' \
                  'mw)(mm)(>eu)(>hk)(>cm)(>ro)(>mf)(>tw)(>wf)(>fj)(>tv)\n(<bq)(<sc)(<je)(<jm)(<af)(<ca)(<vc)([' \
                  '<unitednations,<un,<united_nations],united_nations)(<tr)(kp)(cw)(kh)(ke)([lgbt,lgbtq+,pride,' \
                  'rainbow],rainbow_flag)(rs)(sr)(ec)(rw)(cv)(>tr)([>unitednations,>un,>united_nations],' \
                  'united_nations)(>vc)(>ca)(>af)(>jm)(>je)(>sc)(>bq)\n(<yt)(<er)(<sb)(<tt)(<bh)(<ad)(<mx)(<al)(<cc)(' \
                  'ps)(kw)(ae)(sd)(gp)(sz)(do)(gr)(cl)(pa)(>cc)(>al)(>mx)(>ad)(>bh)(>tt)(>sb)(>er)(>yt)\n(<vi)(<tl)(' \
                  '<na)(<kn)(<lk)(<tm)(<ic)(<sa)(<mp)(ss)(eh)(gq)(jo)(mz)(ch)(lr)(uy)(my)(tg)(>mp)(>sa)(>ic)(>tm)(' \
                  '>lk)(>kn)(>na)(>tl)(>vi)\n(<me)(<tk)(<bt)(<cx)(<re)(<mt)(<pk)(<cy)(<br)(za)(km)(zw)(cf)(ag)(gb)(' \
                  'us)(io)(um)(dg)(>br)(>cy)(>pk)(>mt)(>re)(>cx)(>bt)(>tk)(>me)'


class Cell(object):
    """
    stores information about player and base status

    player = 0 if empty
    player = 1 or 2 respectively for player 1 or 2

    base = False if its a normal gameplay cell
    base = True if its in the base
    """

    def __init__(self, player: int = 0, base: bool = False):
        self.player = player
        self.base = base

    def set_base(self, player: int):
        """Makes this cell into a base cell."""
        self.player = player
        self.base = True

    def copy(self):
        """Deep copies this cell."""
        return Cell(self.player, self.base)


def generate_flag_array() -> [[Flag]]:
    """
    Turns the hardcoded array into a Flag array and writes the .json file.
    Can be overwritten by a .json file if it already exists.
    """
    if not os.path.exists(Board.default_board_file):
        string_split_arr = hardcoded_board.split('\n')
        string_2d_arr = []
        for string in string_split_arr:
            temp_flag_arr = string.strip('(').strip(')').split(')(')
            string_2d_arr.append(temp_flag_arr)
        final_board_arr = []
        for flag_arr in string_2d_arr:
            temp_arr = []
            for flag in flag_arr:
                if flag[0] != '[':
                    flag_code = flag.strip('<').strip('>')
                    temp_arr.append(([flag], f':flag_{flag_code}:'))
                else:
                    split_string = flag.strip('[').split('],')
                    aliases = split_string[0].split(',')
                    flag_code = split_string[1]
                    temp_arr.append((aliases, f':{flag_code}:'))
            final_board_arr.append(temp_arr)
        with open(Board.default_board_file, 'w') as f:
            json.dump(final_board_arr, f, indent=4)
        return final_board_arr

    with open(Board.default_board_file, 'r') as f:
        return json.load(f)


class Board(list):
    """
    A representation of the state of the game and its transformations
    To obtain a the cell at a particular location, call
        <board>[<position>]
    where:
    position is a pair of ints

    ***Note that the board is indexed from 0
       so the first coordinate may range from 0 to rows - 1
       and the second coordinate may range from 0 to cols - 1
    """
    adjacent_offsets = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    base_offsets = [(i, j) for i in range(2) for j in range(2)]
    vanquish_offsets = [(i, j) for i in range(4) for j in range(4)]
    vanquish_surround = [(-1, 0), (-1, 1), (-1, 2), (-1, 3),
                         (4, 0), (4, 1), (4, 2), (4, 3),
                         (0, -1), (1, -1), (2, -1), (3, -1),
                         (0, 4), (1, 4), (2, 4), (3, 4)]

    default_board_file = Path('data/board.json')
    flag_array: [[Flag]]

    def __init__(self, r: int, c: int, bases: [Position]):
        super().__init__()
        self.rows = r
        self.cols = c
        self.extend([[Cell() for j in range(c)] for i in range(r)])
        self.bases = bases

        self.make_base(1)
        self.make_base(2)

        Board.flag_array = generate_flag_array()

    def make_base(self, player: int):
        """
        Creates a new base.
        :param player: The player that owns the base.
        """
        center = self.bases[player - 1]
        for dx, dy in Board.base_offsets:
            self[center[0] + dx][center[1] + dy].set_base(player)

    def deepcopy(self):
        """
        Creates a completely new class with identical values.
        :return: A new Board with the same values as the given instance.
        """
        cpy = Board(self.rows, self.cols, self.bases)
        for i in range(self.rows):
            for j in range(self.cols):
                cpy[i][j] = self[i][j].copy()
        return cpy

    def is_valid_position(self, pos: Position) -> bool:
        """
        Tests if the given position fits on the board.
        :param pos: Position to test.
        """
        return 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols

    def adjacent(self, center: Position, base=False):
        """
        Returns the adjacent cells.
        :param center: The center of which to test adjacent cells.
        :param base: Whether or not base cell included in the list
        :return: An adjacent cell using yield.
        """
        for dx, dy in Board.adjacent_offsets:
            loc = (center[0] + dx, center[1] + dy)
            if self.is_valid_position(loc):
                if base or not self[loc[0]][loc[1]].base:
                    yield loc

    def acquire(self, player: int, locs: [Position], validate=False):
        """
        The acquire move.
        :param player: The player who is acquiring.
        :param locs: The locations of the acquired cells.
        :param validate: Whether or not to validate if the move can be performed.
        """
        if validate:
            for loc in locs:
                if self[loc[0]][loc[1]].player != 0:
                    raise InvalidMove
        for loc in locs:
            self[loc[0]][loc[1]].player = player

    def conquer(self, player: int):
        """
        "Conquers" any space that is able to be conquered by the player.
        Condition for conquering is that two of one player's cells touch one of another player's.
        :param player: The player who is conquering.
        :return:
        """
        enemy = 3 - player
        # player cells that touch enemy cell
        touching = [[0 for j in range(self.cols)] for i in range(self.rows)]
        # fill queue w player cells
        q = deque()
        for i in range(self.rows):
            for j in range(self.cols):
                loc = (i, j)
                if self[loc[0]][loc[1]].player == player and not self[loc[0]][loc[1]].base:
                    q.append(loc)
        # begin teh konker
        while q:
            # newly conquered cell
            curr = q.popleft()
            for i, j in self.adjacent(curr):
                adj = (i, j)
                # update neighbour
                if self[adj[0]][adj[1]].player == enemy:
                    touching[i][j] += 1
                    if touching[i][j] >= 2:
                        # conquer neighbour
                        self[adj[0]][adj[1]].player = player
                        q.append(adj)

    def vanquish_spots(self, player: int):
        return [(i,j) for i in range(self.rows) for j in range(self.cols) 
                if self.is_valid_vanquish(player, (i,j))]

    def is_valid_vanquish(self, player: int, corner: Position) -> bool:
        """
        Checks whether a given vanquish is a valid move
        :param player: The player who is vanquishing.
        :param corner: Top left corner of the square to be vanquished.
        :return: True if move is valid, or else False
        """
        # check that player surrounds square
        surrounding = 0
        for dx, dy in Board.vanquish_surround:
            loc = (corner[0] + dx, corner[1] + dy)
            if self.is_valid_position(loc):
                cell = self[loc[0]][loc[1]]
                if not cell.base and cell.player == player:
                    surrounding += 1
        if surrounding < 4:
            return False
        # check that square is a single color of nonbase cells
        square_player = self[corner[0]][corner[1]].player
        for dx, dy in Board.vanquish_offsets:
            loc = (corner[0] + dx, corner[1] + dy)
            if not self.is_valid_position(loc) or self[loc[0]][loc[1]].base or \
                    self[loc[0]][loc[1]].player != square_player:
                return False
        # is a valid move
        return True

    def vanquish(self, player: int, corner: Position, validate=False):
        """
        Vanquishes a 4x4 square of the same color given that:
        The player has at least 4 cells outside of and adjacent to the square.
        :param player: The player who is vanquishing.
        :param corner: Top left corner of the square to be vanquished.
        """
        # check that player surrounds square
        if validate:
            surrounding = 0
            for dx, dy in Board.vanquish_surround:
                loc = (corner[0] + dx, corner[1] + dy)
                if self.is_valid_position(loc):
                    cell = self[loc[0]][loc[1]]
                    if not cell.base and cell.player == player:
                        surrounding += 1
            if surrounding < 4:
                raise InvalidMove()
        # check that square is a single color
        square_player = self[corner[0]][corner[1]].player
        square = []
        for dx, dy in Board.vanquish_offsets:
            loc = (corner[0] + dx, corner[1] + dy)
            if validate:
                if not self.is_valid_position(loc) or \
                        self[loc[0]][loc[1]].base or \
                        self[loc[0]][loc[1]].player != square_player:
                    raise InvalidMove()
            square.append(self[loc[0]][loc[1]])
        # delete square
        for sq in square:
            sq.player = 0

    def conquest(self, player: int):
        """
        The game ending move. If this succeeds, then the attempting player wins.
        :param player: The player number that is attempting the move.
        """
        enemy = 3 - player
        # distance to player base
        dist = [[math.inf for j in range(self.cols)] for i in range(self.rows)]
        # is distance fixed
        visited = [[False for j in range(self.cols)] for i in range(self.rows)]
        # path from player base
        prev = [[None for j in range(self.cols)] for i in range(self.rows)]

        i, j = self.bases[player - 1]
        start = (i, j)
        dist[i][j] = 0
        pq = [(0, start)]

        while pq:
            # current least-distance cell
            path_len, curr = heappop(pq)
            visited[curr[0]][curr[1]] = True
            for i, j in self.adjacent(curr, base=True):
                if not visited[i][j] and self[i][j].player == player:
                    # update unvisited neighbours for shorter path
                    if dist[i][j] > path_len + 1:
                        prev[i][j] = curr
                        dist[i][j] = path_len + 1
                        heappush(pq, (dist[i][j], (i, j)))
                # trace path if found
                if self[i][j].base and self[i][j].player == enemy:
                    while curr != start:
                        self[i][j].base = True
                        curr = prev[curr[0]][curr[1]]
                    return
        # no path found
        raise InvalidMove

    def __str__(self):
        """
        Converts the Board into a readable string that is sent
        to the discord client as 3 separate messages.
        """
        emoji_string = ''
        for j, (cell_row, flag_row) in enumerate(zip(self, Board.flag_array)):
            for i, (cell, flag) in enumerate(zip(cell_row, flag_row)):
                player = cell.player
                if player == 0:
                    # blank cell, use flag, add spoilers
                    emoji = '||' + flag[1] + '||'
                else:
                    # player cell stand-in code
                    emoji = 'p' + str(player)
                    if cell.base:
                        # base stand-in code
                        emoji += 'b'
                # add this cell's emoji to string
                emoji_string += emoji
                # if row end, add line break
                if i == 27:
                    emoji_string += '\n'
                    # add message breaks on 5th and 9th rows
                    if j == 4 or j == 8:
                        emoji_string += '#msg'
        return emoji_string


class Move(object):
    """
    A Command representing executable moves on the gameboard
    The format for creating a Move is as below:
    Acquire:
        Move('A', <player>, locs=<list of positions to be acquired>)

    Conquer:
        Move('C', <player>)

    Vanquish:
        Move('V', <player>, corner=<position of upper-left corner of 4x4 square to be deleted>)
    
    Conquest:
        Move('Q', <player>)

    where:
        player is 1 or 2
        position is a pair of ints
    """

    def __init__(self, move_type: str, player, locs=None, corner=None):
        self.move_type = move_type
        self.player = player
        if move_type == 'A':
            self.locs = locs
        if move_type == 'V':
            self.corner = corner

    def __call__(self, board: Board, *, validate=False):
        if self.move_type == 'A':
            func = partial(board.acquire, validate=validate)
        elif self.move_type == 'C':
            func = board.conquer
        elif self.move_type == 'V':
            func = partial(board.vanquish, validate=validate)
        elif self.move_type == 'Q':
            func = board.conquest
        else:
            raise InvalidMove
        func(**{k: v for k, v in self.__dict__.items() if k != 'move_type'})


class InvalidMove(Exception):
    """
    Thrown when a Move is not able to be executed.
    """
    pass
