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
        """
        Stores the given move.
        """
        self.moves.append(move.__dict__)

    def move_history(self):
        """
        Creates a move history and returns it.
        :return: an array of moves with arr[0]
        being the first move.
        """
        return [Move(**mv) for mv in self.moves]

    def board_history(self):
        """
        Creates a board history and returns it.
        :return an array of boards with arr[0]
        being the inital board.
        """
        # starting state
        board = Board(self.rows, self.cols, self.bases)
        # update boards with moves to generate list
        boards: [Board] = [board]
        for mv in self.moves:
            board = Move(**mv)(board)
            boards.append(board)
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
        self.save = history.board_history()
        self.latest = self.save[-1]
        self.move = None

    def preview(self, move: Move):
        return move(self.latest, validate=True)

    def receive(self, move: Move):
        """
        Turns a move into an updated cache.
        """
        if self.move:
            return
        self.latest = move(self.latest, validate=True)
        self.move = move
        if not self.move:
            return
        self.save.append(self.latest)
        self.hist.store(self.move)
