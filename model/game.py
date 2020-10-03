from model.state import Move

class Utility:

    # takes string input from discord and creates a move
    @staticmethod
    def readMove(self, action_text) -> Move:
        args = action_text.split()
        prefix = args[0]
        if prefix == 'A':
            # unfinished
            pass
        elif prefix == 'V':
            if not len(args) == 3:
                return
            for i in range(len(args)-1):
                # unfinished
                pass
        elif prefix == 'C' or prefix == 'Q':
            return Move(prefix)
        else:
            return

    # takes a flag code and returns coordinates
    @staticmethod
    def translateFlag(self, flag):

class Player:
    pass