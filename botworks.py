import asyncio
import pickle
import sys

from model.game import *

__version__ = 'v0.2beta'

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

commands: {callable} = {}
save_actions: [callable] = []


def command(aliases: [str] = None, hidden: bool = False):
    def decorator(function: callable):
        function.hidden = hidden
        commands[function.__name__] = function
        if aliases:
            for alias in aliases:
                commands[alias] = function
        return function

    return decorator


def save_action(function: callable):
    save_actions.append(function)
    return function


class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


class DisquidClient(discord.Client):
    """
    Main body for the Discord Client interface for the project.
    Documentation Quick Reference https://discordpy.readthedocs.io/en/latest/api.html#
    """

    default_prefix = '*'
    data_path = Path('data/')
    auto_save_duration = 300  # in seconds
    admins: []
    debug_guild = 762071050007609344

    def __init__(self, prefix_file_name: str = 'prefixes', admin_file_name: str = 'admins',
                 player_file_name: str = 'players',
                 game_file_name: str = 'games', history_file_name: str = 'history', **options):
        super().__init__(**options)
        self.prefix_file = DisquidClient.data_path.joinpath(prefix_file_name + '.json')
        self.admin_file = DisquidClient.data_path.joinpath(admin_file_name + '.json')
        self.player_file = DisquidClient.data_path.joinpath(player_file_name + '.pickle')
        self.game_file = DisquidClient.data_path.joinpath(game_file_name + '.pickle')
        self.history_file = DisquidClient.data_path.joinpath(history_file_name + '.pickle')

        # Data directory loading
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)

        # Prefix file loading
        if not os.path.exists(self.prefix_file):
            with open(self.prefix_file, 'w') as f:
                f.truncate(0)
                json.dump({}, f)
            self.prefixes: {int, str} = {}
        else:
            with open(self.prefix_file, 'r') as f:
                temp: {} = json.load(f)
                self.prefixes = {int(k): v for k, v in temp.items()}

        # Admin id file loading:
        if not os.path.exists(self.admin_file):
            with open(self.admin_file, 'w') as f:
                f.truncate(0)
                temp = [int(input('Please give the first admin\'s userID '))]
                json.dump(temp, f)
            DisquidClient.admins = temp
        else:
            with open(self.admin_file, 'r') as f:
                temp: [] = json.load(f)
                DisquidClient.admins = [int(i) for i in temp]

        # Player file loading
        if not os.path.exists(self.player_file):
            with open(self.player_file, 'wb') as f:
                f.truncate(0)
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
                f.truncate(0)
                pickle.dump({}, f)
            self.active_games: {int, Game} = {}
        else:
            with open(self.game_file, 'rb') as f:
                self.active_games: {int, Game} = pickle.load(f)

        # Active Game file loading
        if not os.path.exists(self.history_file):
            with open(self.history_file, 'wb') as f:
                f.truncate(0)
                pickle.dump([], f)
                self.game_history: [Game] = []
        else:
            with open(self.history_file, 'rb') as f:
                self.game_history: [Game] = pickle.load(f)

        # Adding auto save
        async def auto_save(duration: int):
            while True:
                await asyncio.sleep(duration)
                await self.save(bypass=True)

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
            self.players[uid] = Player(uid, len(self.players) + 1)
            return self.get_player(uid)

    def search_name(self, name: str) -> int:
        """
        Takes in a player's name and returns a uid
        """
        for key in self.players:
            if self.players[key].name == name:
                return key
        return 0

    @save_action
    def save_prefixes(self):
        """
        Saves current dict of prefixes to a file using JSON.
        """
        with open(self.prefix_file, 'w') as f:
            f.truncate(0)
            json.dump(self.prefixes, f, indent=4)

    @save_action
    def save_admins(self):
        """
        Saves current dict of prefixes to a file using JSON.
        """
        with open(self.admin_file, 'w') as f:
            f.truncate(0)
            json.dump(DisquidClient.admins, f, indent=4)

    @save_action
    def save_players(self):
        """
        Saves current dict of players to a file using pickle.
        """
        with open(self.player_file, 'wb') as f:
            f.truncate(0)
            pickle.dump(self.players, f)

    @save_action
    def save_games(self):
        """
        Saves current dict of players to a file using pickle.
        """
        with open(self.game_file, 'wb') as f:
            f.truncate(0)
            pickle.dump(self.active_games, f)

    @save_action
    def save_history(self):
        """
        Saves current dict of players to a file using pickle.
        """
        with open(self.history_file, 'wb') as f:
            f.truncate(0)
            pickle.dump(self.game_history, f)

    async def on_ready(self):
        """
        Called when bot is setup and ready.
        Put any startup actions here.
        """
        print(f'Disquid {__version__} ready.')
        await self.get_channel(762071050522984470).send(f'Disquid {__version__} ready to test.')  # Test channel

    async def on_guild_join(self, guild: discord.Guild):
        """
        This is called when the bot is invited to and joins a new "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        self.prefixes[guild.id] = self.default_prefix

    async def on_message(self, message: discord.Message):
        """
        Here will go the processing for breaking down messages into component parts.
        Likely used for start and stop game commands.
        :param message: Message Class found at https://discordpy.readthedocs.io/en/latest/api.html#message.
        """

        if not self.is_ready() or not message.content or message.author.id == self.user.id:
            return

        prefix = self.get_prefix(message.guild.id)
        if len(str(message.content)) >= len(prefix) and prefix == str(message.content[0:len(prefix)]):
            cmd = str(message.content).strip(prefix).split()[0]
            try:
                await commands[cmd](self, message=message)
            except KeyError:
                print('User tried nonexistent command')
        else:
            if message.channel.id not in self.active_games or not str(message.content)[0] in ['A', 'C', 'V', 'Q'] \
                    or len(message.content.split()) > 4:
                return
            # User is likely attempting a move under these conditions
            game = self.active_games[message.channel.id]
            cache = game.cache
            if not message.author.id == game.players[cache.current_player - 1].uid:
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
                    vanquish_spots: str = Utility.format_locations(cache.latest.vanquish_spots(cache.current_player),
                                                                   game)
                    await message.channel.send('Vanquish options:\n' + vanquish_spots)
                else:
                    await message.channel.send(
                        f'Not a valid move! Use \'{prefix}help moves\' to get help.')

    @command(['help', 'h'])
    async def help_command(self, message: discord.Message):
        """
        [*, moves] Provides descriptions of commands.
        """
        is_admin = message.author.id in DisquidClient.admins
        processed_message = str(message.content).split()
        del processed_message[0]
        if len(processed_message) == 0:
            active_descs = {}
            embed_var = discord.Embed(title="Help Commands", color=0xc0365e)
            for key in commands:
                if is_admin or not commands[key].hidden:
                    aliases = []
                    for k in commands:
                        aliases.append(k) if commands[key] == commands[k] else aliases
                    if str(aliases) not in active_descs:
                        active_descs[str(aliases)] = commands[key].__doc__
                        embed_var.add_field(name=str(aliases), value=str(commands[key].__doc__), inline=False)
            await message.channel.send(embed=embed_var)
        else:
            if processed_message[0] == 'moves':
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
                await message.channel.send(f'No help found for \'{processed_message[0]}\'.')

    @command(['changeprefix', 'cp'])
    async def change_prefix(self, message: discord.message):
        """
        [prefix] Usable by admins to change the bot's server prefix.
        """
        if message.author.guild_permissions.administrator:
            processed_message = str(message.content).split()
            del processed_message[0]
            if len(processed_message) == 0:
                await message.channel.send('No prefix argument provided.')
                return
            self.prefixes.pop(message.guild.id)
            self.prefixes[message.guild.id] = processed_message[0]
            await message.channel.send(f'Prefix is now \'{processed_message[0]}\'')
        else:
            await message.channel.send('Only administrators may do this.')

    @command(['profile'])
    async def player_profile(self, message: discord.Message):
        """
        [@mention/name] views a given player's profile.
        """
        mentions: [discord.Member] = message.mentions
        processed_message = str(message.content).split()
        del processed_message[0]
        if len(mentions) == 1:
            prof_id = mentions[0]
        elif len(mentions) == 0 and len(processed_message) == 1:
            if processed_message[0] == 'dft':
                await message.channel.send('Cannot view the profile by name of someone of the default name.')
                return
            prof_id = self.search_name(processed_message[0])
        elif len(mentions) == 0 and len(processed_message) == 0:
            prof_id = message.author.id
        else:
            await message.channel.send('Too many players mentioned/named')
            return

        if prof_id not in self.players:
            await message.channel.send('Player does not exist.')

        player = self.players[prof_id]
        embed_var = discord.Embed(title=f'{player.name}\'s profile.', color=0xc0365e)
        primary_emoji = str(player.emoji[0]).strip('[').strip(']')
        secondary_emoji = str(player.emoji[1]).strip('[').strip(']')
        custom_emoji = str(player.custom_emoji).strip('[').strip(']')
        emoji_str = f'Primary Emojis (tile, base):\n{primary_emoji}\n\nSecondary Emojis (tile, base):' \
                    f'\n{secondary_emoji}\n\nCustom Emojis\n{custom_emoji}'
        embed_var.add_field(name='Emojis', value=emoji_str, inline=False)
        embed_var.add_field(name='Rank', value=f'#{player.rank}/{len(self.players)} Worldwide', inline=False)
        await message.channel.send(embed=embed_var)

    @command(['c'])
    async def challenge(self, message: discord.Message):
        """
        [@mention/name] Initiates a challenge against another player.
        """
        p1_id = message.author.id
        mentions: [discord.Member] = message.mentions
        processed_message = str(message.content).split()
        del processed_message[0]
        if len(mentions) == 1:
            p2_id = mentions[0].id
            chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))
        elif len(mentions) == 0 and len(processed_message) == 1:
            if processed_message[0] == 'dft':
                await message.channel.send('Cannot challenge someone with a default name by name.')
                return
            p2_id = self.search_name(processed_message[0])
            if p2_id:
                chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))
            else:
                await message.channel.send('Player does not exist!')
                return
        else:
            await message.channel.send('Too many or too few players mentioned/named, '
                                       'challenge failed.')
            return

        async def del_challenge():
            await asyncio.sleep(300)
            if chal in self.active_challenges:
                await message.channel.send(f'Challenge between {chal.p1.name} and {chal.p2.name} expired.')
                self.active_challenges.remove(chal)

        self.active_challenges.append(Challenge(self.get_player(p1_id), self.get_player(p2_id)))
        asyncio.run_coroutine_threadsafe(del_challenge(), asyncio.get_event_loop())
        await message.channel.send(f'{chal.p1.name} challenges {chal.p2.name} they have 5 minutes to accept.')

    @command(['a'])
    async def accept(self, message: discord.Message):
        """
        [@mention/name] Accepts an existing challenge from another user.
        """
        p2_id = message.author.id
        mentions: [discord.Member] = message.mentions
        processed_message = str(message.content).split()
        del processed_message[0]
        if len(mentions) == 1:
            p1_id = mentions[0].id
            temp_chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))
        elif len(mentions) == 0 and len(processed_message) == 1:
            if processed_message[0] == 'dft':
                await message.channel.send('Cannot challenge someone with a default name by name.')
                return
            p1_id = self.search_name(processed_message[0])
            if p1_id:
                temp_chal = Challenge(self.get_player(p1_id), self.get_player(p2_id))
            else:
                message.channel.send('Player does not exist!')
                return
        else:
            await message.channel.send('Too many or too few players mentioned, '
                                       'accept failed.')
            return
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
                await channel.send(
                    f'Game creation success! Welcome to Conquid!. Type {self.get_prefix(guild.id)}start to begin.')
                self.active_challenges.remove(c)

    @command(['start', 's'])
    async def start_game(self, message: discord.Message):
        """
        Starts a game in an active game channel.
        """
        channel_id = message.channel.id
        target_game = self.active_games[channel_id]
        if target_game:
            if not message.author.id == target_game.players[0].uid:
                await message.channel.send('Challenger needs to start the game!')
                return
            await message.channel.send('Incoming Board!')
            board_string = str(target_game)
            for substring in board_string.split('#msg'):
                await message.channel.send(substring)
            await message.channel.send(
                f'It is <@{target_game.players[target_game.cache.current_player - 1].uid}>\'s turn! Do \'{self.get_prefix(message.guild.id)}'
                f'help moves\' for move help')
            return
        await message.channel.send(
            f'No waiting game found, please use {self.get_prefix(message.guild.id)}challenge to make one.')

    @command(['previewmove', 'preview', 'p'])
    async def preview_move(self, message: discord.Message):
        """
        [any move] Previews a move by sending it to your dms before you make it.
        """
        processed_message = str(message.content).split()
        del processed_message[0]
        game = self.active_games[message.channel.id]
        cache = game.cache
        try:
            move_string = ''
            for sub in processed_message:
                move_string += f' {sub}'
            move = Utility.read_move(game.cache.current_player, move_string)
            for substring in game.get_board_string(move(cache.latest, validate=True)).split('#msg'):
                await message.author.send(substring)
            await message.channel.send('Move Success! Sent to your DMs.')
            # Test for win condition
            if move.move_type == 'Q':
                await message.author.send(
                    'You would win! Though, I don\'t know how given you weren\'t smart enough to picture a win move.')
        except InvalidMove:
            move_prefix = processed_message[0]
            if move_prefix == 'V':
                vanquish_spots: str = Utility.format_locations(cache.latest.vanquish_spots(cache.current_player),
                                                               game)
                await message.channel.send('Vanquish options:\n' + vanquish_spots)
            else:
                await message.channel.send(
                    f'Not a valid move! Use \'{self.get_prefix(message.guild.id)}help moves\' to get help.')

    @command(['refresh', 'reprint', 'update'])
    async def reprint_board(self, message: discord.Message):
        """
        Refreshes the board if used in an active game channel.
        """
        if message.channel.id in self.active_games and message.author.id in self.active_games[
            message.channel.id].players:
            await self.update_board(self.active_games[message.channel.id])
        else:
            await message.channel.send('No board to update here.')

    @command(['set_cell', 'set'])
    async def set_tile(self, message: discord.Message):
        """
        [main, alt] [tile, base] [(color), custom] Set player cell emoji
        """
        processed_message = str(message.content).split()
        del processed_message[0]
        if len(processed_message) < 3:
            await message.channel.send('Missing arguments')
        else:
            if processed_message[0] == 'main':
                tile_favor = 0
            elif processed_message[0] == 'alt':
                tile_favor = 1
            else:
                tile_favor = None

            if processed_message[1] == 'tile':
                tile_type = 0
            elif processed_message[1] == 'base':
                tile_type = 1
            else:
                tile_type = None

            tile_name = processed_message[2]
            emoji_opts = {
                'black': ':black_large_square:',
                'brown': ':brown_square:',
                'red': ':red_square:',
                'orange': ':orange_square:',
                'yellow': ':yellow_square:',
                'green': ':green_square:',
                'blue': ':blue_square:',
                'purple': ':purple_square:',
                'white': ':white_large_square:',
                'custom': str(self.get_player(message.author.id).custom_emoji[tile_type])
            }
            emoji_name = emoji_opts[tile_name]

            # check if duplicate
            emoji_owner = self.get_player(message.author.id)
            for i in range(len(emoji_owner.emoji)):
                for j in range(len(emoji_owner.emoji[i])):
                    if emoji_owner.emoji[i][j] == str(emoji_name):
                        emoji_name = 'duplicate'

            if tile_favor and tile_type and emoji_name:
                emoji_owner.emoji[tile_favor][tile_type] = str(emoji_name)
                await message.channel.send(f'Success! {emoji_name} has been set')
            elif emoji_name == 'duplicate':
                await message.channel.send('Emoji already chosen by player')
            else:
                await message.channel.send('Arguments invalid. Check help command')

    @command(['upload'])
    async def upload_emoji(self, message: discord.Message):
        """
        [*, tile, base] Upload attached image as custom cell emoji
        """
        processed_message = str(message.content).split()
        del processed_message[0]
        attachments = message.attachments
        slot = None
        if len(processed_message) == 0 or processed_message[0] == 'tile':
            slot_empty = self.get_player(message.author.id).custom_emoji[0] == ''
            slot = 'tile'
        elif processed_message[1] == 'base':
            slot_empty = self.get_player(message.author.id).custom_emoji[1] == ''
            slot = 'base'

        if len(attachments) == 0:
            await message.channel.send('No image provided')
        elif not slot:
            await message.channel.send('Invalid arguments.')
        elif not slot_empty:
            await message.channel.send('Slot is not empty. use the delete command.')
        else:
            image = await attachments[0].read()
            player_name = self.get_player(message.author.id).name
            d_guild = self.get_guild(self.debug_guild)

            final_emoji = await d_guild.create_custom_emoji(
                name=(player_name + '_b' if slot == 'base' else player_name),
                image=image)
            # Check if tile or base
            if slot == 'tile':
                self.get_player(message.author.id).custom_emoji[0] = final_emoji
            elif slot == 'base':
                self.get_player(message.author.id).custom_emoji[1] = final_emoji

            await message.channel.send(f'New emoji {final_emoji} uploaded')

    @command(['clear', 'clr'])
    async def delete_emoji(self, message: discord.Message):
        """
        [*, tile, base] Delete custom emoji to free up slot
        """
        processed_message = str(message.content).split()
        del processed_message[0]
        emoji_owner = self.get_player(message.author.id)

        if len(processed_message) == 0:
            tile_type = 'tile'
        else:
            tile_type = processed_message[0]
        if tile_type == 'tile':
            emoji_index = 0
        elif tile_type == 'base':
            emoji_index = 1
        else:
            await message.channel.send(f'Invalid Argument: \'{processed_message[0]}\'')
            return

        if emoji_owner.custom_emoji[emoji_index] == '':
            await message.channel.send('No emoji to delete')
        else:
            c_emoji = emoji_owner.custom_emoji[emoji_index]
            # replace custom emoji if in use
            for i in range(len(emoji_owner.emoji)):
                for j in range(len(emoji_owner.emoji[i])):
                    if emoji_owner.emoji[i][j] == str(c_emoji):
                        emoji_owner.emoji[i][j] = Player.default_emoji[i][j]
            # remove emoji from storage server
            await c_emoji.delete()
            # remove emoji from player's custom list
            emoji_owner.custom_emoji[emoji_index] = ''
            await message.channel.send(f'{emoji_owner.name} custom {tile_type} slot has been deleted')

    @command(['changename', 'name'])
    async def change_name(self, message: discord.Message):
        """
        [3 letter name (ex. 'dft')] Changes the name of the user who sends the message,
        as well as all of the user's custom emoji.
        """
        uid = message.author.id
        processed_message = message.content.split()
        del processed_message[0]
        if len(processed_message) == 0:
            await message.channel.send('No name provided.')
            return
        if len(processed_message) > 1:
            await message.channel.send('Invalid Arguments.')
            return
        if not 3 <= len(processed_message[0]) <= 5:
            await message.channel.send('Name too long or short. Names must be 3-5 characters.')
            return
        for key in self.players:
            if processed_message[0] == self.players[key].name:
                await message.channel.send('Name taken.')
                return
        self.get_player(uid).name = str(processed_message[0])
        for i in range(len(self.get_player(uid).custom_emoji)):
            if '' not in self.get_player(uid).custom_emoji[i]:
                if i == 0:
                    self.get_player(uid).custom_emoji[0].edit(str(processed_message[0] + '_b'))
                if i == 1:
                    self.get_player(uid).custom_emoji[1].edit(str(processed_message[0]))
        await message.channel.send('Name changed successfully!')

    @command(['delgame', 'del'])
    async def delete_game(self, message: discord.Message):
        """
        Will trash the current game in the channel, usable by admins only.
        DOES NOT MOVE GAME TO HISTORY.
        """
        channel_id = message.channel.id
        processed_message = str(message.content).split()
        del processed_message[0]
        if channel_id in self.active_games:
            if message.author.guild_permissions.administrator:
                self.active_games.remove(channel_id)
                await message.channel.send('Game Deleted.')
            else:
                await message.channel.send('Insufficient user permissions.')
        else:
            await message.channel.send('No game to delete in this channel.')

    @command(['reindex'])
    async def reindex_game(self, message: discord.Message):
        """
        [@mention (p1), @mention (p2)] rebuilds the current game channel if something is broken by reading all of the
        valid moves in the channel and building a board from it.
        """
        channel_id = message.channel.id
        if message.mentions and len(message.mentions) == 2:
            self.active_games.pop(channel_id)
            self.active_games[message.channel.id] = Game(channel_id, [message.mentions[0].id, message.mentions[1].id])
            messages = await message.channel.history(limit=None, oldest_first=True).flatten()
            print(messages)
            for msg in messages:
                if self.get_prefix(msg.channel.id) not in str(message.content):
                    await message.channel.send(msg.content())
        else:
            await message.channel.send(
                'Invalid arguments, please mention both players in order for the command to be successful.')

    @command(['save'], True)
    async def save(self, message: discord.Message = None, bypass: bool = False):
        """
        Called by a bot admin to save all files in the bot.
        """
        if bypass or message.author.id in DisquidClient.admins:
            for fun in save_actions:
                fun(self)
            await message.channel.send('Save Successful.')
        else:
            await message.channel.send('Insufficient user permissions.')

    @command(['exit', 'stop'], True)
    async def exit_command(self, message: discord.Message):
        """
        Called by a bot admin to exit the bot.
        """
        if message.author.id in DisquidClient.admins:
            await message.channel.send('Shutting down.')
            await self.logout()
            sys.exit()
        else:
            await message.channel.send('Insufficient User Permissions')

    @command(['op'], True)
    async def promote(self, message: discord.Message):
        """
        [@mention] Called by a bot admin to promote a new bot admin.
        """
        mentions = message.mentions
        if message.author.id not in DisquidClient.admins:
            return
        if len(mentions) == 0:
            await message.channel.send('No argument provided!')
        for mention in mentions:
            DisquidClient.admins.append(mention.id)
            await message.channel.send(f'@<{mention.id}> is now an admin.')

    @command(['deop'], True)
    async def demote(self, message: discord.Message):
        """
        [@mention] Called by a bot admin to promote a new bot admin.
        """
        mentions = message.mentions
        if message.author.id not in DisquidClient.admins:
            return
        if len(mentions) == 0:
            await message.channel.send('No argument provided!')
        for mention in mentions:
            DisquidClient.admins.remove(mention.id)
            await message.channel.send(f'@<{mention.id}> is no longer an admin.')

    async def update_board(self, game):
        channel = self.get_channel(game.channel_id)
        await channel.send('Incoming Board!')
        for substring in str(game).split('#msg'):
            await channel.send(substring)

    async def on_win(self, game):
        channel = self.get_channel(game.channel_id)
        await channel.send(f'<@{game.players[game.cache.current_player - 1].uid}> WINS!')
        self.active_games.remove(game)
        self.game_history.append(game)

        async def channel_del(chl):
            await chl.send('Channel will be deleted in 1hr, and has been moved to game history.')
            await asyncio.sleep(3600)
            await chl.delete(reason='Game Complete')

        asyncio.run_coroutine_threadsafe(channel_del(channel), asyncio.get_event_loop())


if __name__ == '__main__':
    DisquidClient().run(input('Bot API Token: '))
