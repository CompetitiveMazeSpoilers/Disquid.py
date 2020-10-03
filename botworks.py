import asyncio
import pickle

import discord

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


class DisquidClient(discord.Client):
    """
    Main body for the Discord Client interface for the project.
    Documentation Quick Reference https://discordpy.readthedocs.io/en/latest/api.html#
    """

    default_prefix = '*'
    data_path = Path('data/')
    auto_save_duration = 300  # in seconds

    def __init__(self, prefix_file_name: str = 'prefixes', player_file_name: str = 'players',
                 game_file_name: str = 'games', **options):
        self.prefix_file = DisquidClient.data_path.joinpath(prefix_file_name + '.json')
        self.player_file = DisquidClient.data_path.joinpath(player_file_name + '.pickle')
        self.game_file = DisquidClient.data_path.joinpath(game_file_name + '.pickle')
        super().__init__(**options)
        # Prefix file and data directory loading.
        if not os.path.exists(self.prefix_file):
            os.mkdir(self.prefix_file.parents[0])
            with open(self.prefix_file, 'w') as f:
                json.dump({}, f)
            self.prefixes: {str} = []
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
            self.set_prefix(gid, self.default_prefix)
            return self.default_prefix

    def set_prefix(self, gid: discord.Guild.id, prefix: str):
        """
        Sets the given guild to have the given prefix.
        :param gid: Guild id which has prefix. Class found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        :param prefix: Prefix string to be set.
        """
        if prefix is None:
            self.prefixes.pop(gid)
        else:
            self.prefixes[gid] = prefix

    def save_prefixes(self):
        """
        Saves current dict of prefixes to a file using JSON.
        """
        with open(self.prefix_file, "w") as f:
            f.truncate(0)
            json.dump(self.prefixes, f, indent=4)

    def get_player(self, uid: discord.User.id):
        """
        Returns the player class for a given user id.
        :return: The player class of the given user id.
        """
        try:
            return self.players[uid]
        except KeyError:  # in case of failure of the on_guild_join event
            self.set_player(uid, Player(uid))
            return self.get_player(uid)

    def set_player(self, uid: discord.User.id, player: Player):
        """
        Sets the given guild to have the given prefix.
        :param uid: The user ID. Class found at https://discordpy.readthedocs.io/en/latest/api.html#user.
        :param player: The player class that user belongs to.
        """
        if player is None:
            self.prefixes.pop(uid)
        else:
            self.prefixes[uid] = player

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
                self.active_challenges.append(Challenge(self.get_player(p1_id), self.get_player(p2_id)))
            else:
                await self.get_channel(message.channel.id).send('Too many players mentioned, challenge failed.')

        async def accept(message):
            """
            Accepts an existing challenge from another user.
            :param message: The message by which the command was sent.
            """
            p2_id = message.author.id
            mentions: [discord.Member] = message.mentions
            if len(mentions) == 1:
                p1_id = mentions[0].id
                cur_chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))
                for chal in self.active_challenges:
                    if cur_chal == chal:
                        self.active_challenges.remove(chal)
                        self.active_games.append()
            else:
                await self.get_channel(message.channel.id).send('Too many players mentioned, challenge failed.')

        async def on_exit(message):
            """
            Called to exit the bot.
            :param message: The message by which the command was sent.
            """
            self.save_prefixes()
            self.save_players()
            await self.get_channel(message.channel.id).send('Shutting down.')
            exit()

        prefix = self.get_prefix(message.guild)
        if self.is_ready() and prefix in message.content:
            command = str(message.content).strip(prefix).split(' ')[0]
            cmds: {str, callable} = {
                'challenge': challenge,
                'accept': accept,
                'exit': on_exit
            }
            await cmds[command](message)

    async def on_guild_join(self, guild: discord.Guild):
        """
        This is called when the bot is invited to and joins a new "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        self.set_prefix(guild, self.default_prefix)


if __name__ == '__main__':
    DisquidClient().run(input('Bot API Token: '))
