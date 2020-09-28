import math
from collections import deque
from heapq import heappush, heappop
from typing import List, Tuple
Position = Tuple[int, int]

class Cell:

    def __init__(self, i, j):
        self.row = i
        self.col = j
        self.player = 0
        self.base = False

    # needed for comparability within heap
    def __lt__(self, other):
        if (self.row < other.row):
            return True
        return self.col < other.col

    def set_base(self, player):
        self.player = player
        self.base = True

    def copy(self):
        cpy = Cell(self.row,self.col)
        cpy.player = self.player
        cpy.base = self.base
        return cpy

class Board:
    # a representation of the state and logic of the game
    adjacent_offsets = [(0,1),(0,-1),(1,0),(-1,0)]
    base_offsets = [(i,j) for i in range(-1,2) for j in range(-1,2)]
    vanquish_offsets = [(i,j) for i in range(4) for j in range(4)]
    vanquish_surround = [(-1,0), (-1,1), (-1,2), (-1,3),
                         (4,0), (4,1), (4,2), (4,3),
                         (0,-1), (1,-1), (2,-1), (3,-1),
                         (0,4), (1,4), (2,4), (3,4)]

    def __init__(self, r, c):
        self.rows = r
        self.cols = c
        self.grid = [[Cell(i, j) for j in range(c)] for i in range(r)]
        self.bases = {}

    def make_base(self, player, base: Position):
        self.bases[player] = self[base]
        for dx, dy in Board.base_offsets:
            self[(base[0] + dx, base[1] + dy)].set_base(player)

    def copy(self):
        cpy = Board(self.rows, self.cols)
        cpy.bases = self.bases
        for i in range(self.rows):
            for j in range(self.cols):
                cpy.grid[i][j] = self.grid[i][j].copy()
        return cpy

    def __getitem__(self, pos):
        return self.grid[pos[0]][pos[1]]

    def is_valid_position(self, pos: Position):
        return pos[0] >= 0 and pos[0] < self.rows and pos[1] >= 0 and pos[1] < self.cols

    def adjacent(self, center: Cell, base=False):
        for dx, dy in Board.adjacent_offsets:
            loc = (center.row + dx, center.col + dy)
            if self.is_valid_position(loc):
                cell = self[loc]
                if base or not cell.base:
                    yield cell

    def acquire(self, player, locs: List[Position]):
        cells = [self[loc] for loc in locs]
        for i, a in enumerate(cells):
            if a.player != 0:
                raise InvalidMove()
            for j in range(i):
                if a == cells[j]:
                    raise InvalidMove()
        for a in cells:
            a.player = player


    def conquer(self, player):
        enemy = 3 - player
        # player cells that touch enemy cell
        touching = [[0 for j in range(self.cols)] for i in range(self.rows)]
        # fill queue w player cells
        q = deque(cell for row in self.grid for cell in row if cell.player == player and not cell.base)
        # begin teh konker
        while q:
            # newly conquered cell
            curr = q.popleft()
            for adj in self.adjacent(curr):
                # update neighbour
                if adj.player == enemy:
                    touching[adj.row][adj.col] += 1
                    if touching[adj.row][adj.col] >= 2:
                        #conquer neighbour
                        adj.player = player
                        q.append(adj)

    def vanquish(self, player, corner: Position):
        square_player = self[corner].player
        # check that player surrounds square
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
        square = []
        for dx, dy in Board.vanquish_offsets:
            loc = (corner[0] + dx, corner[1] + dy)
            if (not self.is_valid_position(loc)):
                raise InvalidMove()
            cell = self[loc]
            if (cell.base or cell.player != square_player):
                raise InvalidMove()
            square.append(cell)
        # delete cells
        for cell in square:
            cell.player = 0

    def conquest(self, player):
        enemy = 3-player
        # distance to player base
        dist = [[math.inf for j in range(self.cols)] for i in range(self.rows)]
        # is distance fixed
        visited = [[False for j in range(self.cols)] for i in range(self.rows)]
        # path from player base
        prev = [[None for j in range(self.cols)] for i in range(self.rows)]

        pbase = self.bases[player]
        dist[pbase.row][pbase.col] = 0
        pq = [(0, pbase)]

        while pq:
            # current least-distance cell
            pathlen, curr = heappop(pq)
            visited[curr.row][curr.col] = True
            for adj in self.adjacent(curr, base=True):
                if not visited[adj.row][adj.col] and adj.player == player:
                    #update unvisited neighbours for shorter path
                    if dist[adj.row][adj.col] > pathlen + 1:
                        prev[adj.row][adj.col] = curr
                        dist[adj.row][adj.col] = pathlen + 1
                        heappush(pq, (dist[adj.row][adj.col], adj))
                # trace path if found
                if adj.base and adj.player == enemy:
                    while curr:
                        curr.base = True
                        curr = prev[curr.row][curr.col]
                    return
        # no path found
        raise InvalidMove()

class InvalidMove(Exception):
    pass
