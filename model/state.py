import math
from collections import deque
from heapq import heappush, heappop
from typing import Dict, List, Tuple
Position = Tuple[int,int]
class Cell:
    """stores information about player and base status"""
    def __init__(self):
        self.player = 0
        self.base = False

    def set_base(self, player):
        self.player = player
        self.base = True

    def copy(self):
        cpy = Cell()
        cpy.player = self.player
        cpy.base = self.base
        return cpy

class Board:
    """a representation of the state of the game and its transformations"""
    adjacent_offsets = [(0,1),(0,-1),(1,0),(-1,0)]
    base_offsets = [(i,j) for i in range(-1,2) for j in range(-1,2)]
    vanquish_offsets = [(i,j) for i in range(4) for j in range(4)]
    vanquish_surround = [(-1,0), (-1,1), (-1,2), (-1,3),
                         (4,0), (4,1), (4,2), (4,3),
                         (0,-1), (1,-1), (2,-1), (3,-1),
                         (0,4), (1,4), (2,4), (3,4)]

    def __init__(self, r, c, bases: Dict[int,Position]):
        self.rows = r
        self.cols = c
        self.grid = [[Cell() for j in range(c)] for i in range(r)]
        self.bases = bases

        self.make_base(1)
        self.make_base(2)

    def make_base(self, player):
        center = self.bases[player]
        for dx, dy in Board.base_offsets:
            self[(center[0] + dx, center[1] + dy)].set_base(player)
        self[center].base = False

    def copy(self):
        cpy = Board(self.rows, self.cols, self.bases)
        for i in range(self.rows):
            for j in range(self.cols):
                cpy.grid[i][j] = self.grid[i][j].copy()
        return cpy

    def __getitem__(self, pos: Position) -> Cell:
        return self.grid[pos[0]][pos[1]]

    def is_valid_position(self, pos: Position):
        return pos[0] >= 0 and pos[0] < self.rows and pos[1] >= 0 and pos[1] < self.cols

    def adjacent(self, center: Position, base=False):
        for dx, dy in Board.adjacent_offsets:
            loc = (center[0] + dx, center[1] + dy)
            if self.is_valid_position(loc):
                if base or not self[loc].base:
                    yield loc

    def acquire(self, player, locs: List[Position], validate=False):
        if validate:
            for loc in locs:
                if self[loc].player != 0:
                    raise InvalidMove
        for loc in locs:
            self[loc].player = player

    def conquer(self, player, validate=False):
        enemy = 3 - player
        # player cells that touch enemy cell
        touching = [[0 for j in range(self.cols)] for i in range(self.rows)]
        # fill queue w player cells
        q = deque()
        for i in range(self.rows):
            for j in range(self.cols):
                loc = (i,j)
                if self[loc].player == player and not self[loc].base:
                    q.append(loc)
        # begin teh konker
        while q:
            # newly conquered cell
            curr = q.popleft()
            for i, j in self.adjacent(curr):
                adj = (i,j)
                # update neighbour
                if self[adj].player == enemy:
                    touching[i][j] += 1
                    if touching[i][j] >= 2:
                        #conquer neighbour
                        self[adj].player = player
                        q.append(adj)

    def vanquish(self, player, corner: Position, validate=False):
        #check that player surrounds square
        if validate:
            surrounding = 0
            for dx, dy in Board.vanquish_surround:
                loc = (corner[0] + dx, corner[1] + dy)
                if self.is_valid_position(loc):
                    cell = self[loc]
                    if not cell.base and cell.player == player:
                        surrounding += 1
            if surrounding < 4:
                raise InvalidMove()
        # check that square is filled with enemy
        square_player = self[corner].player
        square = []
        for dx, dy in Board.vanquish_offsets:
            loc = (corner[0] + dx, corner[1] + dy)
            if validate:
                if not self.is_valid_position(loc) or \
                    self[loc].base or \
                    self[loc].player != square_player:
                    raise InvalidMove()
            square.append(self[loc])
        # delete square
        for sq in square:
            sq.player = 0

    def conquest(self, player, validate=False):
        enemy = 3-player
        # distance to player base
        dist = [[math.inf for j in range(self.cols)] for i in range(self.rows)]
        # is distance fixed
        visited = [[False for j in range(self.cols)] for i in range(self.rows)]
        # path from player base
        prev = [[None for j in range(self.cols)] for i in range(self.rows)]

        i, j = self.bases[player]
        start = (i,j)
        dist[i][j] = 0
        pq = [(0, start)]

        while pq:
            # current least-distance cell
            pathlen, curr = heappop(pq)
            visited[curr[0]][curr[1]] = True
            for i, j in self.adjacent(curr, base=True):
                adj = (i, j)
                if not visited[i][j] and self[adj].player == player:
                    #update unvisited neighbours for shorter path
                    if dist[i][j] > pathlen + 1:
                        prev[i][j] = curr
                        dist[i][j] = pathlen + 1
                        heappush(pq, (dist[i][j], adj))
                # trace path if found
                if self[adj].base and self[adj].player == enemy:
                    while curr != start:
                        self[curr].base = True
                        curr = prev[curr[0]][curr[1]]
                    return
        # no path found
        raise InvalidMove()

class Move:
    """A Command representing executable moves on the gameboard"""
    def __init__(self, type, player, **kwargs):
        self.type = type
        self.player = player
        if type == 'A':
            self.locs = kwargs['locs']
        if type == 'V':
            self.corner = kwargs['corner']

    def execute(self, board: Board, *, validate):
        if self.type == 'A':
            func = board.acquire
        if self.type == 'C':
            func = board.conquer
        if self.type == 'V':
            func = board.vanquish
        if self.type == 'Q':
            func = board.conquest
        func(**{k:v for k,v in self.__dict__.items() if k != 'type'}, validate=validate)

class InvalidMove(Exception):
    pass
