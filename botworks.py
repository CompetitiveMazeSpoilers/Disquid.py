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
                 game_file_name: str = 'games', **options):
        super().__init__(**options)
        self.prefix_file = DisquidClient.data_path.joinpath(prefix_file_name + '.json')
        self.player_file = DisquidClient.data_path.joinpath(player_file_name + '.pickle')
        self.game_file = DisquidClient.data_path.joinpath(game_file_name + '.pickle')

        # Data directory loading
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)

        # Prefix file loading
        if not os.path.exists(self.prefix_file):
            with open(self.prefix_file, 'w') as f:
                json.dump({}, f)
            self.prefixes: {str} = {}
        else:
            with open(self.prefix_file, 'r') as f:
                self.prefixes: {str} = json.load(f)

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
                pickle.dump([], f)
            self.active_games: [int, Game] = []
        else:
            with open(self.game_file, 'rb') as f:
                self.active_games: [int, Game] = pickle.load(f)

        # Adding auto save
        async def auto_save(duration: int):
            await asyncio.sleep(duration)
            self.save_players()
            self.save_games()
            self.save_prefixes()

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

        async def challenge(message):
            """
            Initiates a challenge against another player.
            :param message: The message by which the command was sent.
            """
            p1_id = message.author.id
            mentions: [discord.Member] = message.mentions
            if len(mentions) == 1:
                p2_id = mentions[0].id
                chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))
                self.active_challenges.append(Challenge(self.get_player(p1_id), self.get_player(p2_id)))
                await self.get_channel(message.channel.id).send(f'{chal.p1.name} challenges {chal.p2.name}')
            else:
                await self.get_channel(message.channel.id).send('Too many or too few players mentioned, '
                                                                'challenge failed.')

        async def accept(message):
            """
            Accepts an existing challenge from another user.
            :param message: The message by which the command was sent.
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
                        try:
                            channel = await guild.create_text_channel(f'{c.p1.name}-v-{c.p2.name}')
                        except discord.errors.Forbidden:
                            await self.get_channel(message.channel.id).send(
                                'I don\'t have permissions to create game channels!')
                            return
                        try:
                            new_game = Game(channel.id, [c.p1, c.p2])
                            self.active_games.append()
                        except InvalidGameSetup:
                            await self.get_channel(message.channel.id).send('Invalid Game Setup... Aborting.')
                            return
                        await self.get_channel(message.channel.id).send(
                            f'Challenge accepted! Game started in <#{channel.id}>')
                        await self.get_channel(channel.id).send(
                            f'Game creation success! Welcome to Conquid!. Type {prefix}start to begin.')
                        self.active_challenges.remove(c)
                        self.get_channel(new_game.channel_id).send('Game starting, await board sending.')
                        for msg in str(new_game).split('#msg'):
                            self.get_channel(new_game.channel_id).send(msg)
            else:
                await self.get_channel(message.channel.id).send('Too many or too few players mentioned, '
                                                                'accept failed.')

        async def start(message):
            channel_id = message.channel.id
            for game in self.active_games:
                if game.channel_id == channel_id:
                    game.start()
                    return

        async def on_exit(message):
            """
            Called to exit the bot.
            :param message: The message by which the command was sent.
            """
            if message.author.id in DisquidClient.admins:
                self.save_prefixes()
                self.save_players()
                self.save_prefixes()
                await self.get_channel(message.channel.id).send('Shutting down.')
                exit()
            else:
                await self.get_channel(message.channel.id).send('Insufficient user permissions.')

        cmds = {
            'challenge': Command(challenge,
                                 'Challenge another player by running this command and mentioning them in the '
                                 'same message'),
            'accept': Command(accept,
                              'Accept another player\'s challenge by running this command and mentioning them in '
                              'the same message'),
            'start': Command(start, 'Start a game once in a game channel that has been setup successfully.'),
            'exit': Command(on_exit, 'Shut down the bot.')
        }

        async def help_command(message):
            help_string = '```diff\nHelp Commands:'
            for key in cmds:
                help_string += '\n+'
                help_string += str(key) + ': '
                help_string += str(cmds[key])
            help_string += '```'
            await self.get_channel(message.channel.id).send(help_string)

        cmds['help'] = Command(help_command, 'This command.')

        prefix = self.get_prefix(message.guild.id)
        if self.is_ready() and prefix in message.content:
            command = str(message.content).strip(prefix).split(' ')[0]
            await cmds[command].func(message)

    async def on_guild_join(self, guild: discord.Guild):
        """
        This is called when the bot is invited to and joins a new "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        self.prefixes[guild.id] = self.default_prefix


if __name__ == '__main__':
    DisquidClient().run(input('Bot API Token: '))
