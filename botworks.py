import asyncio
import pickle
from typing import Callable

from model.game import *

__version__ = 'v0.1beta'

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

    def __init__(self, func: Callable, help_message: str = 'No help message defined.'):
        self.func = func
        self.help_message = help_message

    def __eq__(self, other):
        if isinstance(other, Command):
            return self.func == other.func
        if isinstance(other, Callable):
            return self.func == other
        else:
            return NotImplemented

    def __str__(self):
        return self.help_message


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
    debug_guild = 762071050007609344

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
                self.game_history: [Game] = []
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
        await self.get_channel(762071050522984470).send(f'Disquid {__version__} ready to test.')  # Test channel

    async def on_message(self, message: discord.Message):
        """
        Here will go the processing for breaking down messages into component parts.
        Likely used for start and stop game commands.
        :param message: Message Class found at https://discordpy.readthedocs.io/en/latest/api.html#message.
        """

        if message.author.id == self.user.id:
            return

        async def challenge():
            """
            Initiates a challenge against another player.
            """
            p1_id = message.author.id
            mentions: [discord.Member] = message.mentions
            if len(mentions) == 1:
                p2_id = mentions[0].id
                chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))

                async def del_challenge():
                    await asyncio.sleep(30)
                    if chal in self.active_challenges:
                        await message.channel.send(f'Challenge between {chal.p1.name} and {chal.p2.name} expired.')
                        self.active_challenges.remove(chal)

                self.active_challenges.append(Challenge(self.get_player(p1_id), self.get_player(p2_id)))
                asyncio.run_coroutine_threadsafe(del_challenge(), asyncio.get_event_loop())
                await message.channel.send(f'{chal.p1.name} challenges {chal.p2.name}')
            else:
                await message.channel.send('Too many or too few players mentioned, '
                                                            'challenge failed.')

        async def accept():
            """
            Accepts an existing challenge from another user.
            """
            p2_id = message.author.id
            mentions: [discord.Member] = message.mentions
            if len(mentions) == 1:
                p1_id = mentions[0].id
                temp_chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))
                for c in self.active_challenges:
                    if temp_chal == c:
                        channel = message.channel
                        guild = channel.guild
                        category = None
                        for ca in guild.categories:
                            if ca.id == channel.category_id:
                                category = ca
                                break
                        try:
                            channel = await guild.create_text_channel(f'{c.p1.name}-v-{c.p2.name}', category=category)
                        except discord.errors.Forbidden:
                            await message.channel.send(
                                'I don\'t have permissions to create game channels!')
                            return
                        try:
                            new_game = Game(channel.id, [c.p1, c.p2])
                            self.active_games[channel.id] = new_game
                        except InvalidGameSetup:
                            await message.channel.send('Invalid game setup... aborting.')
                            return
                        await message.channel.send(
                            f'Challenge accepted! Game started in <#{channel.id}>')
                        await self.get_channel(channel.id).send(
                            f'Game creation success! Welcome to Conquid!. Type {prefix}start to begin.')
                        self.active_challenges.remove(c)

            else:
                await message.channel.send('Too many or too few players mentioned, '
                                                            'accept failed.')

        async def start():
            """
            Starts a game in an active game channel.
            """
            channel_id = message.channel.id
            target_game = self.active_games[channel_id]
            if target_game:
                if not message.author.id == target_game.players[0].uid:
                    await message.channel.send('Challenger needs to start the game!')
                    return
                await self.get_channel(channel_id).send('Incoming Board!')
                board_string = str(target_game)
                for substring in board_string.split('#msg'):
                    await self.get_channel(channel_id).send(substring)
                await self.get_channel(channel_id).send(
                    f'It is <@{target_game.players[target_game.cache.current_player - 1].uid}>\'s turn! Do \'{prefix}'
                    f'help moves\' for move help')
                return
            await self.get_channel(channel_id).send(f'No waiting game found, please use {prefix}challenge to make one.')

        async def on_exit():
            """
            Called to exit the bot.
            """
            if message.author.id in DisquidClient.admins:
                self.save_prefixes()
                self.save_players()
                self.save_prefixes()
                self.save_history()
                await message.channel.send('Shutting down.')
                exit()
            else:
                await message.channel.send('Insufficient user permissions.')

        async def upload_emoji():
            """
            Uploads attachment as emoji
            """
            attachments = message.attachments
            if len(attachments) == 0:
                await message.channel.send('No image provided')
            else:
                image = await attachments[0].read()
                player_name = self.get_player(message.author.id).name
                d_guild = self.get_guild(self.debug_guild)
                final_emoji = await d_guild.create_custom_emoji(name=player_name, image=image)
                await message.channel.send(f'New emoji :{final_emoji}: uploaded')

        async def reprint_board():
            if message.channel.id in self.active_games:
                await self.update_board(self.active_games[message.channel.id])
            else:
                await message.channel.send('No board to update here.')

        cmds = {
            'challenge': Command(challenge,
                                 'Challenge another player by running this command and mentioning them in the '
                                 'same message'),
            'accept': Command(accept,
                              'Accept another player\'s challenge by running this command and mentioning them in '
                              'the same message'),
            'start': Command(start, 'Start a game once in a game channel that has been setup successfully.'),
            'upload': Command(upload_emoji, 'Upload attached image as custom emoji'),
            'refresh': Command(reprint_board, 'Reprints the current game\'s board'),
            'exit': Command(on_exit, 'Shut down the bot.')
        }

        async def help_command():
            """
            Provides descriptions of commands.
            """
            processed_message = str(message.content).split(' ')
            if len(processed_message) == 1:
                help_string = '```diff\nHelp Commands:'
                for key in cmds:
                    help_string += '\n+'
                    help_string += str(key) + ': '
                    help_string += str(cmds[key])
                help_string += '```'
                await message.channel.send(help_string)
            else:
                if processed_message[1] == 'moves':
                    await message.channel.send(
                        'A -- Acquire, this move claims 3 cells given as arguments with flag codes (eg. :flag_us: -> '
                        'us).\n'
                        'V -- Vanquish, this move is used to clear a 4x4 area of an enemy cells as long as 4 of the '
                        'attempting player\'s own cells touch the region.\n'
                        'C -- Conquer, this move claims all enemy cells that touch 2 of the attempting player\'s '
                        'cells.\n'
                        'Q -- Conquest, this move is required to win the game, used when the attempting player'
                        'believes they have a path to the enemy base.')
                else:
                    await message.channel.send('No help found.')

        cmds['help'] = Command(help_command, 'This command.')

        prefix = self.get_prefix(message.guild.id)
        if self.is_ready() and prefix == message.content[0]:
            command = str(message.content).strip(prefix).split(' ')[0]
            try:
                await cmds[command].func()
            except KeyError:
                print('User tried nonexistent command')
        else:
            if message.channel.id not in self.active_games or not str(message.content)[0] in ['A', 'C', 'V', 'Q']:
                return
            game = self.active_games[message.channel.id]
            cache = game.cache
            if not message.author.id == game.players[cache.current_player-1].uid:
                await message.channel.send('Not your turn!')
                return
            try:
                move = Utility.read_move(game.cache.current_player, message.content)
                cache.receive(move)
                await message.channel.send('Move Success!')
                # Test for win condition
                if cache.move.move_type == 'Q':
                    await self.on_win(game)
                await self.update_board(game)
                cache.current_player = 3 - cache.current_player
                cache.move = None
                await message.channel.send(f'It is now <@{game.players[game.cache.current_player - 1].uid}>\'s turn.')
            except InvalidMove:
                move_prefix = message.content.split()[0]
                if move_prefix == 'V':
                    vanq_spots: str = Utility.format_locations(cache.latest.vanquish_spots(cache.current_player), game)
                    await message.channel.send('Vanquish options:\n' + vanq_spots)
                else:
                    await message.channel.send(
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
        for substring in str(game).split('#msg'):
            await channel.send(substring)

    async def on_win(self, game):
        channel = self.get_channel(game.channel_id)
        await channel.send(f'<@{game.players[game.cache.current_player - 1].uid}> WINS!')
        self.active_games.pop(game)
        self.game_history.append(game)

        async def channel_del(chl):
            await chl.send('Channel will be deleted in 1hr, then moved to history.')
            await asyncio.sleep(3600)
            await chl.delete(reason='Game Complete')

        asyncio.run_coroutine_threadsafe(channel_del(channel), asyncio.get_event_loop())


if __name__ == '__main__':
    DisquidClient().run(input('Bot API Token: '))
