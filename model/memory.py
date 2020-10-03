from model.state import *


class History(object):
    """
    Represents the entire history of moves and board states in a game
    To obtain a list of Boards in a game, call
        <history>.board__history()
    To obtain a list of Moves in game, call
        <history>.move__history()

    ***Remember, if a board is the (i)th state in the board history,
    then the last move done is the (i-1)th action in the move history
    """

    def __init__(self, rows: int, cols: int, bases: [Position], moves: [Move]):
        self.rows = rows
        self.cols = cols
        self.bases = bases
        self.moves = moves

    def store(self, move):
        self.moves.append(move.__dict__)

    def is_finished(self):
        return self.moves and self.moves[-1]['move_type'] == 'Q'

    def move_history(self):
        return [Move(**mv) for mv in self.moves]

    def board_history(self):
        # starting state
        board = Board(self.rows, self.cols, self.bases)
        # update boards with moves to generate list
        boards: [Board] = [board.deepcopy()]
        for mv in self.moves:
            Move(**mv)(board)
            boards.append(board.deepcopy())
        return boards


class Cache(object):
    """
    Stores the current Board state and current player.
    For a move to be executed, entered into history, and the turn to change, the following calls must be made:

    1.  <cache>.receive(<move>) must be provided with a move to execute.
        It is possible for the move to be invalid, in which case it will be rejected and
        an InvalidMove exception will be raised from the method.

    The BoardView class must have a method with signature
        BoardView.set_view(self, <board>, <player>, win=False)
    thru which it receives the board, current player whose turn it is and whether they won yet.
    """

    def __init__(self, history: History):
        self.hist = history
        self.current_player = 1
        self.nstate = 0
        self.save = history.board_history()
        self.nstate = len(self.save) - 1
        self.latest = self.save[-1].deepcopy()
        self.move = None

    def at_last_state(self, finish_allowed=True):
        return self.nstate == len(self.save) - 1 and \
               (finish_allowed or not self.hist.is_finished())

    # def play_back(self):
    #    if self.nstate > 0:
    #       self.nstate -= 1
    #        self.current_player = 3 - self.current_player
    #    self.boardview.set_view(self.save[self.nstate], self.current_player)

    # def play_forward(self):
    #    if self.nstate < len(self.save) - 1:
    #        self.nstate += 1
    #        self.current_player = 3 - self.current_player
    #    if self.at_last_state() and self.hist.is_finished():
    #        self.boardview.set_view(self.save[self.nstate], 3 - self.current_player, win=True)
    #    else:
    #        self.boardview.set_view(self.save[self.nstate], self.current_player)

    def receive(self, move: Move):
        if self.move:
            return
        move(self.latest, validate=True)
        self.move = move
        self.confirm()

    # def discard_change(self):
    #    self.latest = self.save[-1].copy()
    #    self.boardview.set_view(self.latest)
    #    self.move = None

    def confirm(self):
        if not self.move:
            return
        self.save.append(self.latest.deepcopy())
        self.hist.store(self.move)
        self.nstate += 1
        self.current_player = 3 - self.current_player
        if self.move.move_type == 'Q':
            self.controller.game_won()
            self.boardview.set_view(self.latest, 3 - self.current_player, win=True)
        else:
            self.boardview.view_player(self.latest, self.current_player)
        self.move = None
