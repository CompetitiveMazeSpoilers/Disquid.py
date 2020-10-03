from model.state import Move


class Utility:

    # takes string input from discord and creates a move
    @staticmethod
    def read_move(action_text) -> Move:
        """
        Turns text into a move.
        :param action_text: Text that should be converted.
        :return: The move based on the given text.
        """
        args = action_text.split()
        prefix = args[0]
        if prefix == 'A':
            # unfinished
            pass
        elif prefix == 'V':
            if not len(args) == 3:
                return
            for i in range(len(args) - 1):
                # unfinished
                pass
        elif prefix == 'C' or prefix == 'Q':
            return Move(prefix)
        else:
            return

    @staticmethod
    def translate_flag(flag):
        """
        Takes in a flag and turns it into coordinates.
        :param flag: The flag that should be translated.
        :return: Coordinates of a given flag on the default layout.
        """
        pass


class Player:
    pass
