import asyncio
import pickle
from typing import Callable

from model.game import *

__version__ = 'v0.0.1a1'

"""
AUTHORS:
*William Greenlee
*Pavan Rauch
*Teerth Patel
    
The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""


class Command(object):

    def __init__(self, func: Callable, help_msg: str = 'No help message defined.'):
        self.func = func
        self.help_msg = help_msg

    def __eq__(self, other):
        if isinstance(other, Command):
            return self.func == other.func
        if isinstance(other, Callable):
            return self.func == other
        else:
            return NotImplemented

    def __str__(self):
        return self.help_msg


class DisquidClient(discord.Client):
    """
    Main body for the Discord Client interface for the project.
    Documentation Quick Reference https://discordpy.readthedocs.io/en/latest/api.html#
    """

    default_prefix = '*'
    data_path = Path('data/')
    auto_save_duration = 300  # in seconds
    admins = [
        216302359435804684,
        267792207942123530,
        285827256788451328
    ]

    def __init__(self, prefix_file_name: str = 'prefixes', player_file_name: str = 'players',
                 game_file_name: str = 'games', history_file_name: str = 'history', **options):
        super().__init__(**options)
        self.prefix_file = DisquidClient.data_path.joinpath(prefix_file_name + '.json')
        self.player_file = DisquidClient.data_path.joinpath(player_file_name + '.pickle')
        self.game_file = DisquidClient.data_path.joinpath(game_file_name + '.pickle')
        self.history_file = DisquidClient.data_path.joinpath(history_file_name + '.pickle')

        # Data directory loading
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)

        # Prefix file loading
        if not os.path.exists(self.prefix_file):
            with open(self.prefix_file, 'w') as f:
                json.dump({}, f)
            self.prefixes: {int, str} = {}
        else:
            with open(self.prefix_file, 'r') as f:
                self.prefixes: {int, str} = json.load(f)

        # Player file loading
        if not os.path.exists(self.player_file):
            with open(self.player_file, 'wb') as f:
                pickle.dump({}, f)
            self.players: {int, Player} = {}
        else:
            with open(self.player_file, 'rb') as f:
                self.players: {int, Player} = pickle.load(f)

        # Active Challenge list
        self.active_challenges: [Challenge] = []

        # Active Game file loading
        if not os.path.exists(self.game_file):
            with open(self.game_file, 'wb') as f:
                pickle.dump({}, f)
            self.active_games: {int, Game} = {}
        else:
            with open(self.game_file, 'rb') as f:
                self.active_games: {int, Game} = pickle.load(f)

        # Active Game file loading
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'wb') as f:
                pickle.dump([], f)
                self.game_history: [Game] = {}
        else:
            with open(self.history_file, 'rb') as f:
                self.game_history: [Game] = pickle.load(f)

        # Adding auto save
        async def auto_save(duration: int):
            await asyncio.sleep(duration)
            self.save_players()
            self.save_games()
            self.save_prefixes()
            self.save_history()

        asyncio.run_coroutine_threadsafe(auto_save(DisquidClient.auto_save_duration), asyncio.get_event_loop())

    def get_prefix(self, gid: discord.Guild.id):
        """
        Returns the prefix for a given guild.
        :return: The prefix of the given guild.
        """
        try:
            return self.prefixes[gid]
        except KeyError:  # in case of failure of the on_guild_join event
            self.prefixes[gid] = self.default_prefix
            return self.default_prefix

    def get_player(self, uid: discord.User.id):
        """
        Returns the player class for a given user id.
        :return: The player class of the given user id.
        """
        try:
            return self.players[uid]
        except KeyError:  # in case of failure of the on_guild_join event
            self.players[uid] = Player(uid, len(self.players))
            return self.get_player(uid)

    def save_prefixes(self):
        """
        Saves current dict of prefixes to a file using JSON.
        """
        with open(self.prefix_file, "w") as f:
            f.truncate(0)
            json.dump(self.prefixes, f, indent=4)

    def save_players(self):
        """
        Saves current dict of players to a file using pickle.
        """
        with open(self.player_file, "wb") as f:
            f.truncate(0)
            pickle.dump(self.players, f)

    def save_games(self):
        """
        Saves current dict of players to a file using pickle.
        """
        with open(self.game_file, "wb") as f:
            f.truncate(0)
            pickle.dump(self.active_games, f)

    def save_history(self):
        """
        Saves current dict of players to a file using pickle.
        """
        with open(self.history_file, "wb") as f:
            f.truncate(0)
            pickle.dump(self.game_history, f)

    async def on_ready(self):
        """
        Called when bot is setup and ready.
        Put any startup actions here.
        """
        print(f'Disquid {__version__} ready to play.')
        await self.get_channel(759944461970046976).send(f'Disquid {__version__} ready to test.')  # Test channel

    async def on_message(self, message: discord.Message):
        """
        Here will go the processing for breaking down messages into component parts.
        Likely used for start and stop game commands.
        :param message: Message Class found at https://discordpy.readthedocs.io/en/latest/api.html#message.
        """

        if message.author.id == self.user.id:
            return

        async def challenge(msg: discord.Message):
            """
            Initiates a challenge against another player.
            :param msg: The message by which the command was sent.
            """
            p1_id = msg.author.id
            mentions: [discord.Member] = msg.mentions
            if len(mentions) == 1:
                p2_id = mentions[0].id
                chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))
                self.active_challenges.append(Challenge(self.get_player(p1_id), self.get_player(p2_id)))
                await self.get_channel(msg.channel.id).send(f'{chal.p1.name} challenges {chal.p2.name}')
            else:
                await self.get_channel(msg.channel.id).send('Too many or too few players mentioned, '
                                                            'challenge failed.')

        async def accept(msg: discord.Message):
            """
            Accepts an existing challenge from another user.
            :param msg: The message by which the command was sent.
            """
            p2_id = msg.author.id
            mentions: [discord.Member] = msg.mentions
            if len(mentions) == 1:
                p1_id = mentions[0].id
                temp_chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))
                for c in self.active_challenges:
                    if temp_chal == c:
                        channel = msg.channel
                        guild = channel.guild
                        category = None
                        for ca in guild.categories:
                            if ca.id == channel.category_id:
                                category = ca
                                break
                        try:
                            channel = await guild.create_text_channel(f'{c.p1.name}-v-{c.p2.name}', category=category)
                        except discord.errors.Forbidden:
                            await self.get_channel(msg.channel.id).send(
                                'I don\'t have permissions to create game channels!')
                            return
                        try:
                            new_game = Game(channel.id, [c.p1, c.p2])
                            self.active_games[channel.id] = new_game
                        except InvalidGameSetup:
                            await self.get_channel(msg.channel.id).send('Invalid game setup... aborting.')
                            return
                        await self.get_channel(msg.channel.id).send(
                            f'Challenge accepted! Game started in <#{channel.id}>')
                        await self.get_channel(channel.id).send(
                            f'Game creation success! Welcome to Conquid!. Type {prefix}start to begin.')
                        self.active_challenges.remove(c)

            else:
                await self.get_channel(msg.channel.id).send('Too many or too few players mentioned, '
                                                            'accept failed.')

        async def start(msg):
            channel_id = msg.channel.id
            target_game = self.active_games[channel_id]
            if target_game:
                if not msg.author.id == target_game.players[0].uid:
                    return
                await self.get_channel(channel_id).send('Incoming Board!')
                board_string = str(target_game)
                for substring in board_string.split('#msg'):
                    await self.get_channel(channel_id).send(substring)
                await self.get_channel(channel_id).send(
                    f'It is <@{target_game.players[target_game.cache.current_player - 1].uid}>\'s turn! Do \'{prefix}help moves\' for move '
                    f'help')
                return
            await self.get_channel(channel_id).send(f'No waiting game found, please use {prefix}challenge to make one.')

        async def on_exit(msg):
            """
            Called to exit the bot.
            :param msg: The message by which the command was sent.
            """
            if msg.author.id in DisquidClient.admins:
                self.save_prefixes()
                self.save_players()
                self.save_prefixes()
                await self.get_channel(msg.channel.id).send('Shutting down.')
                exit()
            else:
                await self.get_channel(msg.channel.id).send('Insufficient user permissions.')

        async def upload_emoji(msg):
            """
            Uploads attachment as emoji
            :param msg: The message by which the command was sent.
            """
            image = msg.attachments[0]
            player_name = self.get_player(msg.author.id)
            msg.guild.create_custom_emoji(player_name, image)
            msg.channel.send(f'New emoji :{player_name}: uploaded')

        cmds = {
            'challenge': Command(challenge,
                                 'Challenge another player by running this command and mentioning them in the '
                                 'same message'),
            'accept': Command(accept,
                              'Accept another player\'s challenge by running this command and mentioning them in '
                              'the same message'),
            'start': Command(start, 'Start a game once in a game channel that has been setup successfully.'),
            'exit': Command(on_exit, 'Shut down the bot.'),
            'upload': Command(upload_emoji, 'Upload attached image as custom emoji')
        }

        async def help_command(msg):
            processed_msg = str(msg.content).split(' ')
            if len(processed_msg) == 1:
                help_string = '```diff\nHelp Commands:'
                for key in cmds:
                    help_string += '\n+'
                    help_string += str(key) + ': '
                    help_string += str(cmds[key])
                help_string += '```'
                await self.get_channel(msg.channel.id).send(help_string)
            else:
                if processed_msg[1] == 'moves':
                    await self.get_channel(msg.channel.id).send(
                        'A -- Aquire, this move claims 3 cells given as arguments with flag codes (eg. :flag_us: -> '
                        'us).\n '
                        'V -- Vanquish, this move is used to clear a 4x4 area of an enermy cells as long as 4 of the '
                        'attempting player\'s own cells touch the region.\n '
                        'C -- Conquer, this move claims all enemy cells that touch 2 of the attemting player\'s '
                        'cells.\n '
                        'Q -- Conquest, this move is required to win the game, used when the attempting player '
                        'believes they have a path to the enemy base.')
                else:
                    await self.get_channel(msg.channel.id).send('No help found.')

        cmds['help'] = Command(help_command, 'This command.')

        prefix = self.get_prefix(message.guild.id)
        if self.is_ready() and prefix == message.content[0]:
            command = str(message.content).strip(prefix).split(' ')[0]
            await cmds[command].func(message)
        else:
            if message.channel.id not in self.active_games:
                return
            try:
                game = self.active_games[message.channel.id]
                move = Utility.read_move(game.cache.current_player, message.content)
                cache = game.cache
                await self.get_channel(message.channel.id).send('Move Success!')
                cache.receive(move)
                # Test for win condition
                if cache.move.move_type == 'Q':
                    await self.on_win(game)
                await self.update_board(game)
                cache.current_player = 3 - cache.current_player
                cache.move = None
            except InvalidMove:
                await self.get_channel(message.channel.id).send(
                    f'Not a valid move! Use \'{prefix}help moves\' to get help.')

    async def on_guild_join(self, guild: discord.Guild):
        """
        This is called when the bot is invited to and joins a new "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        self.prefixes[guild.id] = self.default_prefix

    async def update_board(self, game):
        channel = self.get_channel(game.channel_id)
        await channel.send('Incoming Board!')
        for substring in str(game):
            await channel.send(substring)
        await channel.send(f'It is now <@{game.players[game.cache.current_player - 1].uid}>\'s turn.')

    async def on_win(self, game):
        channel = self.get_channel(game.channel_id)
        await channel.send(f'<@{game.players[game.cache.current_player].uid}> WINS!')

        async def channel_del(chl):
            await chl.delete(reason='Game Complete')

        asyncio.run_coroutine_threadsafe(channel_del(channel), asyncio.get_event_loop())


if __name__ == '__main__':
    DisquidClient().run(input('Bot API Token: '))
