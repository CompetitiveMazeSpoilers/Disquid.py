import json
import os
from pathlib import Path
import model.state

import discord

__version__ = 'v0.0.1a1'

"""
@AUTHORS:
    *William Greenlee
    *Pavan Rauch
    *Teerth Patel
"""


class DisquidClient(discord.Client):
    """
    Main body for the Discord Client interface for the project.
    Documentation Quick Reference https://discordpy.readthedocs.io/en/latest/api.html#
    """

    default_prefix = '.q'
    prefix_file = Path('data/prefixes.json')

    def __init__(self, **options):
        """
        Called when the class is created.
        :param options: Options for super class.
        """
        super().__init__(**options)
        if not os.path.exists(self.prefix_file):
            os.mkdir(self.prefix_file.parents[0])
            with open(self.prefix_file, 'w') as f:
                json.dump({}, f)
            self.prefixes: {str} = {}
        else:
            with open(self.prefix_file, 'r') as f:
                self.prefixes: {str} = json.load(f)

    def get_prefix(self, guild: discord.Guild):
        """
        :return: The prefix of the given guild.
        """
        try:
            return self.prefixes[guild.id]
        except IndexError:  # in case of failure of the on_guild_join event
            self.set_prefix(guild, self.default_prefix)
            return self.default_prefix

    def set_prefix(self, guild: discord.Guild, prefix: str):
        """
        Sets the given guild to have the given prefix.
        :param guild: Guild which has prefix. Class found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        :param prefix: Prefix to be set.
        """
        if prefix is None:
            self.prefixes.pop(guild.id)
        else:
            self.prefixes[guild.id] = prefix

    def save_prefixes(self):
        """
        Saves current dict of prefixes to a file using JSON.
        """
        with open(self.prefix_file, "w") as f:
            f.truncate(0)
            json.dump(self.prefixes, f, indent=4)

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
        prefix = self.get_prefix(message.guild)
        if self.is_ready() and prefix in message.content:
            pass  # do stuff with the message

    async def on_guild_join(self, guild: discord.Guild):
        """
        This is called when the bot is invited to and joins a new "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        self.set_prefix(guild, self.default_prefix)

    def on_exit(self):
        self.save_prefixes()
        exit()


if __name__ == '__main__':
    DisquidClient().run(input('Bot API Token: '))
