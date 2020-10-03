import discord

from model.memory import *

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
    prefix_file = Path('data/prefixes.json')

    def __init__(self, **options):
        super().__init__(**options)
        if not os.path.exists(DisquidClient.prefix_file):
            os.mkdir(DisquidClient.prefix_file.parents[0])
            with open(DisquidClient.prefix_file, 'w') as f:
                json.dump({}, f)
            self.prefixes: {str} = []
        else:
            with open(DisquidClient.prefix_file, 'r') as f:
                self.prefixes: {str} = json.load(f)

    def get_prefix(self, guild: discord.Guild):
        """
        Returns the prefix for a given guild.
        :return: The prefix of the given guild.
        """
        try:
            return self.prefixes[guild.id]
        except KeyError:  # in case of failure of the on_guild_join event
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

        async def challenge(message):
            """
            Initiates a challenge against another player.
            :param ctx: The context of the command.
            """
            pass

        async def on_exit(message):
            """
            Called when the bot exits.
            """
            self.save_prefixes()
            await self.get_channel(message.channel.id).send('Shutting down.')
            exit()

        prefix = self.get_prefix(message.guild)
        if self.is_ready() and prefix in message.content:
            command = str(message.content).strip(prefix).split(' ')[0]
            cmds: {str, callable} = {
                'challenge': challenge,
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
