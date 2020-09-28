from conquid.state import *
from typing import List, Tuple
from functools import partial
Position = Tuple[int, int]

class GameHistory:
    def __init__(self, rows, cols, *bases):
        self.rows = rows
        self.cols = cols
        self.lbase = bases[0]
        self.rbase = bases[1]
        self.moves = []

    def store(self, move):
        self.moves.append(move.__dict__)

    def to_updater(move):
        dct = move.copy()
        type = dct['type']
        del dct['type']
        if type == 'A':
            return partial(Board.acquire, **dct)
        if type == 'C':
            return partial(Board.conquer, **dct)
        if type == 'V':
            return partial(Board.vanquish, **dct)
        if type == 'Q':
            return partial(Board.conquest, **dct)

    def board_history(self):
        # starting state
        board = Board(self.rows, self.cols)
        board.make_base(1, self.lbase)
        board.make_base(2, self.rbase)
        # update boards with moves to generate list
        boards = [board.copy()]
        for move in self.moves:
            GameHistory.to_updater(move)(board)
            boards.append(board.copy())

        return boards

"""
The following classes as meant as convenient adaptors to input move info
into GameHistory
"""
class AcquireMove:
    def __init__(self, player, cells: List[Position]):
        self.type = 'A'
        self.player = player
        self.locs = cells

class ConquerMove:
    def __init__(self, player):
        self.type = 'C'
        self.player = player

    def update(self, board):
        board.conquer(self.player)

class VanquishMove:
    def __init__(self, player, corner: Position):
        self.type = 'V'
        self.player = player
        self.corner = corner

class ConquestMove:
    def __init__(self, player):
        self.type = 'Q'
        self.player = player