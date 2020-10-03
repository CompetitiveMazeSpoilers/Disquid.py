from model.state import Move, Board


class Utility:

    @staticmethod
    def read_move(player, action_text) -> Move:
        """
        Turns text into a move.
        :param action_text: Text that should be converted.
        :param player: Player doing the move.
        :return: The move based on the given text.
        """
        args = action_text.split()
        prefix = args[0]
        player_num = player.id_num
        del args[0]

        # acquire
        if prefix == 'A':
            locs = []
            for flag_code in args:
                loc = Utility.translate_flag(flag_code)
                if loc is None:
                    return
                locs.append(loc)
            return Move(prefix, player_num, locs=locs)
        # vanquish
        elif prefix == 'V':
            if not len(args) == 3:
                return
            if args[0] < 0 or args[0] > 27 or args[1] < 0 or args[1] > 13:
                return
            return Move(prefix, player_num, corner=(args[0], args[1]))
        # conquer / conquest
        elif prefix == 'C' or prefix == 'Q':
            return Move(prefix, player_num)
        else:
            return

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


class Player:

    def __init__(self, id_num):
        self.id_num = id_num


class Challenge(object):

    def __init__(self):
        pass
