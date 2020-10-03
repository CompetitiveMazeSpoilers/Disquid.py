import json
import math
import os
from collections import deque
from heapq import heappush, heappop
from pathlib import Path
from typing import List, Tuple

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
                  'us)(io)(um)(dg)(>br)(>cy)(>pk)(>mt)(>re)(>cx)(>bt)(>tk)(>me) '
default_board_file = Path('data/board.json')
cell_emoji = ((":purple_square:",":purple_circle:"),(":green_square:",":green_circle:"))

Flag = ([str], str)


def generate_flag_array() -> [[Flag]]:
    if not os.path.exists(default_board_file):
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
        with open(default_board_file, 'w') as f:
            json.dump(final_board_arr, f, indent=4)
        return final_board_arr

    with open(default_board_file, 'r') as f:
        return json.load(f)


flag_array = generate_flag_array()

Position = Tuple[int, int]


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
        self.player = player
        self.base = True

    def copy(self):
        return Cell(self.player, self.base)


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

    def __init__(self, r, c, bases: [Position]):
        super().__init__()
        self.rows = r
        self.cols = c
        self.append([Cell() for j in range(c)] for i in range(r))
        self.bases = bases

        self.make_base(1)
        self.make_base(2)

    def make_base(self, player: int):
        center = self.bases[player - 1]
        for dx, dy in Board.base_offsets:
            self[center[0] + dx][center[1] + dy].set_base(player)

    def copy(self):
        cpy = Board(self.rows, self.cols, self.bases)
        for i in range(self.rows):
            for j in range(self.cols):
                cpy[i][j] = self[i][j].copy()
        return cpy

    def is_valid_position(self, pos: Position):
        return 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols

    def adjacent(self, center: Position, base=False):
        for dx, dy in Board.adjacent_offsets:
            loc = (center[0] + dx, center[1] + dy)
            if self.is_valid_position(loc):
                if base or not self[loc[0]][loc[1]].base:
                    yield loc

    def acquire(self, player, locs: List[Position], validate=False):
        if validate:
            for loc in locs:
                if self[loc[0]][loc[1]].player != 0:
                    raise InvalidMove
        for loc in locs:
            self[loc[0]][loc[1]].player = player

    def conquer(self, player, validate=False):
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

    def vanquish(self, player, corner: Position, validate=False):
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
        # check that square is filled with enemy
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

    def conquest(self, player, validate=False):
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
            pathlen, curr = heappop(pq)
            visited[curr[0]][curr[1]] = True
            for i, j in self.adjacent(curr, base=True):
                if not visited[i][j] and self[i][j].player == player:
                    # update unvisited neighbours for shorter path
                    if dist[i][j] > pathlen + 1:
                        prev[i][j] = curr
                        dist[i][j] = pathlen + 1
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
        emoji_string = ""
        for i, cell, flag in enumerate(zip(self, flag_array)):
            player = cell.player
            j = 0
            emoji = ""
            if player == 0:
                # blank cell, use flag, add spoilers
                emoji = "||" + flag[1] + "||"
            else:
                # player cell
                if cell.base:
                    # base
                    emoji = cell_emoji[player-1][0]
                else:
                    # nonbase
                    emoji = cell_emoji[player-1][1]
            # add this cell's emoji to string
            emoji_string += emoji
            # if row end, add line break
            if (i+1) % 28 == 0:
                emoji_string += "\n"
                j += 1
                # add message breaks on 5th and 9th rows
                if j == 5 or j == 9
                    emoji_string += "#msg"
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

    def execute(self, board: Board, *, validate=False):
        if self.move_type == 'A':
            func = board.acquire
            func(**{k: v for k, v in self.__dict__.items() if k != 'type'}, validate=validate)
        elif self.move_type == 'C':
            func = board.conquer
            func(**{k: v for k, v in self.__dict__.items() if k != 'type'}, validate=validate)
        elif self.move_type == 'V':
            func = board.vanquish
            func(**{k: v for k, v in self.__dict__.items() if k != 'type'}, validate=validate)
        elif self.move_type == 'Q':
            func = board.conquest
            func(**{k: v for k, v in self.__dict__.items() if k != 'type'}, validate=validate)
        else:
            raise InvalidMove


class InvalidMove(Exception):
    pass
