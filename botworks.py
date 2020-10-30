import asyncio
import glob
import pickle
from discord import Intents

from model.game import *

__version__ = 'v1.0'

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
    colors_guild = 764673692650831893
    official_guild = 764695476880408586
    replay_channel = 764879291057700884
    matchmaking_channel = 764882689446248489
    rank_roles = {
        "Conquistador": 766082501705203713,
        "Marquis": 766082503789379584,
        "Squire": 766082505224224818,
        "Quartermaster": 766082506255892481,
        "Delinquent": 766082890211393546
    }
    title_roles = {
        "Queen": 766082499536879647
    }

    def __init__(self, prefix_file_name: str = 'prefixes', admin_file_name: str = 'admins',
                 player_file_name: str = 'players', game_file_name: str = 'games',
                 history_file_name: str = 'history', video_dir_name: str = 'videos',
                 rank_file_name: str = 'ranks',
                 **options):
        super().__init__(**options)
        self.prefix_file = DisquidClient.data_path.joinpath(prefix_file_name + '.json')
        self.admin_file = DisquidClient.data_path.joinpath(admin_file_name + '.json')
        self.player_file = DisquidClient.data_path.joinpath(player_file_name + '.pickle')
        self.game_file = DisquidClient.data_path.joinpath(game_file_name + '.pickle')
        self.history_file = DisquidClient.data_path.joinpath(history_file_name + '.pickle')
        self.video_dir = DisquidClient.data_path.joinpath(video_dir_name + '/')
        self.ranks_file = DisquidClient.data_path.joinpath(rank_file_name + '.json')

        # Data directory loading
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)

        if not os.path.exists(self.video_dir):
            os.mkdir(self.video_dir)

        # Prefix file loading
        if not os.path.exists(self.prefix_file):
            with open(self.prefix_file, 'w') as f:
                json.dump({}, f)
            self.prefixes: {int, str} = {}
        else:
            with open(self.prefix_file, 'r') as f:
                temp: {} = json.load(f)
                self.prefixes = {int(k): v for k, v in temp.items()}

        # Admin id file loading:
        if not os.path.exists(self.admin_file):
            with open(self.admin_file, 'w') as f:
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
                pickle.dump({}, f)
            self.players: {int, Player} = {}
        else:
            with open(self.player_file, 'rb') as f:
                self.players: {int, Player} = pickle.load(f)

        # Active Challenge list
        self.active_challenges: [Challenge] = []
        self.queued_player = None

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

        self.ranks = self.rank_arr(self.players)

        # Adding auto save
        async def auto_save(duration: int):
            while True:
                await asyncio.sleep(duration)
                await self.save(bypass=True)

        asyncio.run_coroutine_threadsafe(auto_save(DisquidClient.auto_save_duration), asyncio.get_event_loop())

    def rank_arr(self, d: {}):
        """
        :return: an array in order of ELO of the players
        """
        arr = []
        for key in d:
            arr.append(d[key])

        def val(p):
            return p.elo

        arr.sort(key=val, reverse=True)
        return arr

    async def regen_videos(self):
        """
        Clears video dir and regenerates all of the videos.
        """
        for game in self.game_history:
            game.to_video(self.data_path.joinpath('temp/'), self.video_dir)
        replays = []
        for file in os.listdir(self.video_dir):
            if str(file).split('.')[-1] == 'mp4':
                replays.append(file)
        for replay in replays:
            with open(self.video_dir.joinpath(replay), 'rb') as f:
                attachment = discord.File(f)
                await self.get_channel(DisquidClient.replay_channel).send(replay, file=attachment)

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
        except KeyError:
            self.players[uid] = Player(uid)
            self.ranks.append(self.get_player(uid))
            return self.get_player(uid)

    async def make_player_role(self, gid: discord.Guild.id, uid: discord.User.id):
        """
        Creates and assigns default role to player
        """
        if gid == self.official_guild:
            role = await self.get_guild(gid).create_role(name='dft', mentionable=True, color=discord.Color(0xdd2e45))
            member = self.get_guild(gid).get_member(uid)
            await member.add_roles(role)
            self.get_player(uid).role_id = role.id

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
        if self.get_channel(764699769829982218) is not None:
            await self.get_channel(764699769829982218).send(f'Disquid {__version__} is now online and ready.')
        if len(self.game_history) > len(glob.glob(str(self.video_dir.joinpath('*.mp4')))):
            print(len(self.game_history))
            await self.regen_videos()

    async def on_guild_join(self, guild: discord.Guild):
        """
        This is called when the bot is invited to and joins a new "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        self.prefixes[guild.id] = self.default_prefix

    async def on_guild_leave(self, guild: discord.Guild):
        """
        This is called when a bot leaves a "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        del self.prefixes[guild.id]

    async def on_message(self, message: discord.Message, reindexing=False):
        """
        Here will go the processing for breaking down messages into component parts.
        Likely used for start and stop game commands.
        :param message: Message Class found at https://discordpy.readthedocs.io/en/latest/api.html#message.
        :param reindexing: If the client is reindexing using the on_message event.
        """

        if not self.is_ready() or not message.content or message.author.bot:
            return

        prefix = self.get_prefix(message.guild.id)
        if len(str(message.content)) >= len(prefix) and prefix == str(message.content)[0:len(prefix)]:
            cmd = str(message.content).strip(prefix).split()[0].lower()
            try:
                await commands[cmd](self, message=message)
            except KeyError:
                print('User tried nonexistent command')
        else:
            if message.channel.id not in self.active_games:
                return
            game = self.active_games[message.channel.id]
            if str(message.content) == 'draw' or str(message.content) == 'cancel':
                if str(message.content) == 'draw' and message.author.id in game.players:
                    if not game.draw_suggested:
                        if not reindexing:
                            await message.channel.send(
                                'Are you sure? The other player can confirm by typing \'draw\' or '
                                'either of you can cancel by typing \'cancel\'')
                        game.draw_suggested = message.author.id
                        return
                    elif not game.draw_suggested == message.author.id:
                        await self.on_draw(game)
                else:
                    game.draw_suggested = 0
                    if not reindexing:
                        await message.channel.send('Draw canceled.')

            if not str(message.content)[0] in ['A', 'C', 'V', 'Q'] \
                    or len(message.content.split()) > 4:
                return
            # User is likely attempting a move under these conditions
            cache = game.cache
            if not message.author.id == game.players[cache.current_player - 1].uid:
                if not reindexing:
                    await message.channel.send('Not your turn!')
                return
            try:
                move = Utility.read_move(game.cache.current_player, message.content)
                cache.receive(move)
                if not reindexing:
                    await message.channel.send('Move Success!')
                # Test for win condition
                if cache.move.move_type == 'Q':
                    await self.on_win(game)
                    cache.move = None
                    return
                if not reindexing:
                    await self.update_board(game)
                cache.current_player = 3 - cache.current_player
                cache.move = None
                if not reindexing:
                    if game.players[game.cache.current_player - 1].role_id:
                        send = (f'It is '
                                f'{message.guild.get_role(game.players[game.cache.current_player - 1].role_id).mention}/ '
                                f'<@{game.players[game.cache.current_player - 1].uid}>\'s turn! ')
                    else:
                        send = f'It is <@{game.players[game.cache.current_player - 1].uid}>\'s turn! '
                    await message.channel.send(send)
            except InvalidMove:
                move_prefix = message.content.split()[0]
                if move_prefix == 'V' and not reindexing:
                    vanquish_spots: str = Utility.format_locations(cache.latest.vanquish_spots(cache.current_player),
                                                                   game)
                    await message.channel.send('Vanquish options:\n' + vanquish_spots)
                else:
                    if not reindexing:
                        await message.channel.send(
                            f'Not a valid move! Use \'{prefix}help moves\' to get help.')

    @command(['help', 'h'])
    async def help_command(self, message: discord.Message):
        """
        [*, moves, tiles] Provides descriptions of commands.
        """
        is_admin = message.author.id in DisquidClient.admins
        processed_message = str(message.content).split()
        del processed_message[0]
        if len(processed_message) == 0:
            active_descs = {}
            if self.get_player(message.author.id).role_id:
                color = await message.author.get_role(self.get_player(message.author.id).role_id).color
            else:
                color = 0xc0365e
            embed_var = discord.Embed(title="Help Commands", color=color)
            for key in commands:
                if is_admin or not commands[key].hidden:
                    aliases = []
                    for k in commands:
                        aliases.append(k) if commands[key] == commands[k] else aliases
                    if str(aliases) not in active_descs:
                        active_descs[str(aliases)] = commands[key].__doc__
                        embed_var.add_field(name=str(aliases), value=str(commands[key].__doc__).replace('\n', ''),
                                            inline=False)
            await message.channel.send(embed=embed_var)
        else:
            if processed_message[0] == 'moves':
                await message.channel.send(
                    'A -- Acquire, this move claims 3 cells given as arguments with flag codes (eg. :flag_us: -> '
                    'us) flags that do not have a horizontal line require an arrow indicating what side of the board '
                    'they are on (eg. :flag_eu: -> <eu).\n'
                    'V -- Vanquish, this move is used to clear a 4x4 area of an enemy cells as long as 4 of the '
                    'attempting player\'s own cells touch the region.\n'
                    'C -- Conquer, this move claims all enemy cells that touch 2 of the attempting player\'s '
                    'cells.\n'
                    'Q -- Conquest, this move is required to win the game, used when the attempting player'
                    'believes they have a path to the enemy base.\n'
                    'Draw-- Ends the game without a winner if each individual participating agrees.')
            elif processed_message[0] == 'tiles':
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
                }
                # add custom colors
                c_guild = self.get_guild(self.colors_guild)
                color_emojis = c_guild.emojis
                for c_emoji in color_emojis:
                    emoji_opts[c_emoji.name] = str(c_emoji)
                emoji_opts['custom'] = '[based on player custom slots]'

                # loop through all options and add
                help_msg = ''
                for opt in emoji_opts.items():
                    help_msg += f'{opt[1]} : `{opt[0]}`\n'

                await message.channel.send(help_msg)
            else:
                await message.channel.send(f'No help found for \'{processed_message[0]}\'.')

    @command()
    async def ping(self, message: discord.Message):
        """
        PONG! Sends the bot's latency.
        """
        await message.channel.send(f'{self.latency * 1000}ms')

    async def emoji_color_test(self, emoji_name: str):
        """
        Returns color that estimates prominent color of emoji
        """
        c_guild = self.get_guild(self.colors_guild)
        d_guild = self.get_guild(self.debug_guild)
        emoji = None
        emoji_opts = {
            ':black_large_square:': 0x31373d,
            ':brown_square:': 0xc16a4f,
            ':red_square:': 0xdd2e45,
            ':red_circle:': 0xdd2e45,
            ':orange_square:': 0xf4900c,
            ':yellow_square:': 0xfdcc58,
            ':green_square:': 0x78b159,
            ':blue_square:': 0x55acee,
            ':blue_circle:': 0x55acee,
            ':purple_square:': 0xaa8ed6,
            ':white_large_square:': 0xe6e7e8
        }
        for e in c_guild.emojis:
            if str(e) == emoji_name:
                emoji = e
        for e in d_guild.emojis:
            if str(e) == emoji_name:
                emoji = e
        if emoji is not None:
            color = Utility.color_estimate(await emoji.url.read())
        elif emoji_name in emoji_opts.keys():
            color = emoji_opts[emoji_name]
        else:
            color = 0xffffff
        if color == 0:
            color = 65793
        print(color)
        return color

    @command(['changeprefix', 'cp'])
    async def change_prefix(self, message: discord.Message):
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
            await message.guild.me.edit(nick=f'[{processed_message[0]}] ' + str(message.guild.me.name))
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
            prof_id = mentions[0].id
        elif len(mentions) == 0 and len(processed_message) == 1:
            if processed_message[0] == 'dft':
                await message.channel.send('Cannot view the profile by name of someone of the default name.')
                return
            prof_id = self.search_name(processed_message[0])
        elif len(mentions) == 0 and len(processed_message) == 0:
            prof_id = message.author.id
            self.get_player(prof_id)
        else:
            await message.channel.send('Too many players mentioned/named')
            return

        if prof_id not in self.players:
            await message.channel.send('Player does not exist.')

        player = self.players[prof_id]
        embed_var = discord.Embed(title=f'{player.name}\'s profile.', color=0xc0365e)
        custom_emoji_strings = [[]]
        for c_emoji in player.custom_emoji:
            custom_emoji_strings.append(str(c_emoji))
        emoji_str = f'Primary Emojis (tile, base)\n{str(player.emoji[0]).strip("[").strip("]")}' \
                    f'\n\nSecondary Emojis (tile, base)\n{str(player.emoji[1]).strip("[").strip("]")}' \
                    f'\n\nCustom Emojis\n{str(custom_emoji_strings).strip("[").strip("]").strip(",")}'
        embed_var.add_field(name='Emojis', value=emoji_str, inline=False)
        embed_var.add_field(name='Rank', value=f'#{self.ranks.index(player) + 1}/{len(self.players)} Worldwide',
                            inline=False)
        title = None
        for role_name, role_id in zip(self.title_roles.keys(), self.title_roles.values()):
            if self.get_guild(self.official_guild).get_role(role_id) in self.get_guild(self.official_guild).get_member(
                    prof_id).roles:
                title = role_name

        embed_var.add_field(name='Elo', value=f'{player.elo}: '
                                              f'{player.elo_string() if title is None else title}')
        await message.channel.send(embed=embed_var)

    @command(['top'])
    async def leaderboard(self, message: discord.Message):
        """
        Displays the top 10 players worldwide.
        """
        embed_var = discord.Embed(title='Worldwide Leaderboard', color=0xc0365e)
        leaderboard_str = ''
        for i, player in enumerate(self.ranks):
            if i > 9:
                break
            leaderboard_str += f'`[{player.elo}]`: {player.name}\n'
        embed_var.add_field(name='Top 10', value=leaderboard_str, inline=False)
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
        await self.confirm_challenge(message, temp_chal)

    @command(['q'])
    async def queue(self, message: discord.Message):
        """
        Inserts current user into challenge queue.
        """
        if not message.channel.id == DisquidClient.matchmaking_channel:
            return
        id = message.author.id
        if not self.queued_player:
            self.queued_player = self.get_player(id)
            await message.channel.send('Player is now queued for a challenge.')
        else:
            p2 = self.get_player(id)
            if p2 == self.queued_player:
                await message.channel.send('Player is already queued')
                return
            chal = Challenge(self.queued_player, p2)
            self.active_challenges.append(chal)
            self.queued_player = None
            await self.confirm_challenge(message, chal)

    async def confirm_challenge(self, message: discord.Message, chal: Challenge):
        for c in self.active_challenges:
            if chal == c:
                channel = message.channel
                guild = channel.guild
                category = None
                category_id = channel.category_id if not guild.id == self.official_guild else 764879389648617522
                for ca in guild.categories:
                    if ca.id == category_id:
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
            player = target_game.players[target_game.cache.current_player - 1]
            if player.role_id:
                send = (
                    f'It is {message.guild.get_role(player.role_id).mention}/'
                    f'<@{target_game.players[target_game.cache.current_player - 1].uid}>\'s turn! '
                    f'Do \'{self.get_prefix(message.guild.id)}help moves\' for move help')
            else:
                send = (f'It is <@{target_game.players[target_game.cache.current_player - 1].uid}>\'s turn! '
                        f'Do \'{self.get_prefix(message.guild.id)}help moves\' for move help')
            await message.channel.send(send)
            if message.guild.id == self.official_guild:
                used_emoji = []
                for i, (player) in enumerate(target_game.players):
                    emoji_num = 0
                    emoji = player.emoji[emoji_num][0]
                    while emoji in used_emoji:
                        emoji_num += 1
                        emoji = player.emoji[emoji_num][0]
                    used_emoji.append(emoji)
                    role = await self.get_guild(message.guild.id).create_role(name=message.channel.name,
                                                                              color=discord.Color(
                                                                                  await self.emoji_color_test(emoji)))
                    await self.get_guild(message.guild.id).get_member(player.uid).add_roles(role)
                    target_game.role_ids[i] = role.id

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
        if message.channel.id in self.active_games and (message.author.id in self.active_games[
            message.channel.id].players or message.author.guild_permissions.administrator):
            await self.update_board(self.active_games[message.channel.id], True)
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
                tile_favor = 1
            elif processed_message[0] == 'alt':
                tile_favor = 2
            else:
                tile_favor = 0

            if processed_message[1] == 'tile':
                tile_type = 1
            elif processed_message[1] == 'base':
                tile_type = 2
            else:
                tile_type = 0

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
                'custom': str(self.get_player(message.author.id).custom_emoji[tile_type - 1])
            }
            # add custom colors
            c_guild = self.get_guild(self.colors_guild)
            color_emojis = c_guild.emojis
            for c_emoji in color_emojis:
                emoji_opts[c_emoji.name] = str(c_emoji)

            emoji_name = emoji_opts[tile_name]

            # check if duplicate
            emoji_owner = self.get_player(message.author.id)
            for i in range(len(emoji_owner.emoji)):
                for j in range(len(emoji_owner.emoji[i])):
                    if emoji_owner.emoji[i][j] == str(emoji_name):
                        emoji_name = 'duplicate'

            if emoji_name == 'duplicate':
                await message.channel.send('Emoji already chosen by player')
            elif emoji_name == 'empty':
                await message.channel.send('Custom emoji slot has not been filled')
            elif tile_favor and tile_type and emoji_name:
                emoji_owner.emoji[tile_favor - 1][tile_type - 1] = str(emoji_name)
                await message.channel.send(f'Success! {emoji_name} has been set')
            else:
                await message.channel.send('Arguments invalid. Check help command')

            if tile_favor == 1 and tile_type == 2 and message.guild.id == self.official_guild:
                if not emoji_owner.role_id:
                    await self.make_player_role(gid=message.guild.id, uid=message.author.id)
                await message.guild.get_role(self.get_player(message.author.id).role_id).edit(
                    color=discord.Color(await self.emoji_color_test(emoji_owner.emoji[0][1])))

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
            slot_empty = self.get_player(message.author.id).custom_emoji[0] == 'empty'
            slot = 'tile'
        elif processed_message[0] == 'base':
            slot_empty = self.get_player(message.author.id).custom_emoji[1] == 'empty'
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

        if emoji_owner.custom_emoji[emoji_index] == 'empty':
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
            emoji_owner.custom_emoji[emoji_index] = 'empty'
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
        self.get_player(uid).name = str(processed_message[0]).lower()
        for i in range(len(self.get_player(uid).custom_emoji)):
            if 'empty' not in self.get_player(uid).custom_emoji[i]:
                if i == 0:
                    await self.get_player(uid).custom_emoji[0].edit(name=str(processed_message[0]) + '_b')
                if i == 1:
                    await self.get_player(uid).custom_emoji[1].edit(name=str(processed_message[0]))

        if message.guild.id == self.official_guild:
            if not self.get_player(uid).role_id:
                await self.make_player_role(gid=message.guild.id, uid=uid)
            await message.guild.get_role(self.get_player(uid).role_id).edit(
                name=str(processed_message[0]).lower())
            await message.channel.send('Name changed successfully!')

    @command(['delgame', 'del'])
    async def delete_game(self, message: discord.Message):
        """
        Will trash the current game in the channel, usable by admins only.
        DOES NOT MOVE GAME TO HISTORY.
        """
        if message.author.guild_permissions.administrator:
            channel_id = message.channel.id
            game = self.active_games.get(channel_id)
            if game:
                for i, role_id in enumerate(game.role_ids):
                    await message.guild.get_role(role_id).delete()
            processed_message = str(message.content).split()
            del processed_message[0]
            if channel_id in self.active_games:
                self.active_games.pop(channel_id)
                await message.channel.send('Game Deleted.')

                async def channel_del():
                    await message.channel.send('Channel will be deleted in 1hr, and has been moved to game history.')
                    await asyncio.sleep(3600)
                    await message.channel.delete(reason='Game Complete')

                asyncio.run_coroutine_threadsafe(channel_del(), asyncio.get_event_loop())
            else:
                await message.channel.send('No game to delete in this channel.')
        else:
            await message.channel.send('Insufficient user permissions.')

    @command(['reindex'])
    async def reindex_game(self, message: discord.Message):
        """
        [@mention (p1), @mention (p2), bool (replay)] rebuilds the current game channel if something is broken by
        reading all of the valid moves in the channel and building a board from it.
        """
        if message.author.guild_permissions.administrator:
            channel_id = message.channel.id
            prefix = self.get_prefix(message.guild.id)
            processed_message = str(message.content).split()
            del processed_message[0]
            if len(processed_message) == 3:
                if processed_message[2].lower() == 'true':
                    replay = True
                else:
                    replay = False
            else:
                replay = False
            if message.mentions and len(message.mentions) == 2:
                await self.delete_game(message)
                self.active_games[message.channel.id] = Game(channel_id,
                                                             [self.get_player(message.mentions[0].id),
                                                              self.get_player(message.mentions[1].id)])
            elif len(message.mentions) == 1 and not len(str(message.content).split()) < 3:
                await self.delete_game(message)
                self.active_games[message.channel.id] = Game(channel_id,
                                                             [self.get_player(message.mentions[0].id),
                                                              self.get_player(message.mentions[0].id)])
            else:
                await message.channel.send(
                    'Invalid arguments, please mention both players in order for the command to be successful.')
                return
            await message.channel.send('Beginning of reindexed game.')
            async for msg in message.channel.history(limit=None, oldest_first=True):
                if prefix != str(msg.content)[:len(prefix)]:
                    if not msg.author.bot and replay:
                        await msg.channel.send(f'{msg.author.name}: {msg.content}')
                    await self.on_message(msg, not replay)
            await message.channel.send('Reindex complete.')
        else:
            await message.channel.send('Insufficient user permissions.')

    @command(['save'], True)
    async def save(self, message: discord.Message = None, bypass: bool = False):
        """
        Called by a bot admin to save all files in the bot.
        """
        if bypass:
            for fun in save_actions:
                fun(self)
            return
        if message.author.id in DisquidClient.admins:
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
            await self.close()
        else:
            await message.channel.send('Insufficient user permissions')

    @command(['op'], True)
    async def promote(self, message: discord.Message):
        """
        [@mention] Called by a bot admin to promote a new bot admin.
        """
        if message.author.id in DisquidClient.admins:
            mentions = message.mentions
            if len(mentions) == 0:
                await message.channel.send('No argument provided!')
            for mention in mentions:
                if mention.id not in DisquidClient.admins:
                    DisquidClient.admins.append(mention.id)
                    await message.channel.send(f'<@{mention.id}> is now an admin.')
                else:
                    await message.channel.send(f'<@{mention.id}> was already an admin!')
        else:
            await message.channel.send('Insufficient user permissions.')

    @command(['deop'], True)
    async def demote(self, message: discord.Message):
        """
        [@mention] Called by a bot admin to promote a new bot admin.
        """
        mentions = message.mentions
        if message.author.id in DisquidClient.admins:
            if len(mentions) == 0:
                await message.channel.send('No argument provided!')
            for mention in mentions:
                DisquidClient.admins.remove(mention.id)
                await message.channel.send(f'@<{mention.id}> is no longer an admin.')
        else:
            await message.channel.send('Insufficient user permissions.')

    async def update_rank_role(self, guild: discord.Guild, player: Player):
        if guild.id == self.official_guild:
            try:
                for role in guild.get_member(player.uid).roles:
                    if role.id in self.rank_roles.values() and not role.id == self.rank_roles[player.elo_string()]:
                        await guild.get_member(player.uid).remove_roles(role)
                for new_role in guild.roles:
                    if new_role.id == self.rank_roles[player.elo_string()]:
                        await guild.get_member(player.uid).add_roles(new_role)
            except KeyError:
                print('no role: ' + player.elo_string())

    @command(['elo'], True)
    async def set_elo(self, message: discord.Message):
        """
        [new elo, @mention] Called by an admin to set players' elo to a new value.
        """
        mentions = message.mentions
        if message.author.id in DisquidClient.admins:
            if len(mentions) == 0 or not str(message.content).split()[1].isnumeric():
                await message.channel.send('No argument provided!')
            for mention in mentions:
                self.get_player(mention.id).elo = int(str(message.content).split()[1])

                def val(p):
                    return p.elo

                self.ranks.sort(key=val, reverse=True)
                if message.guild.id == self.official_guild:
                    await self.update_rank_role(message.guild, self.get_player(mention.id))
                await message.channel.send(f'<@{mention.id}>\'s elo has been set.')
        else:
            await message.channel.send('Insufficient user permissions.')

    @command(['queen', 'crown'], True)
    async def assign_queen(self, message: discord.Message):
        """
        [@mention] Crowns a new queen, removing the role from anyone who has it first.
        """
        mentions = message.mentions
        if message.author.id in DisquidClient.admins and message.guild.id == self.official_guild:
            if len(mentions) == 0:
                await message.channel.send('No argument provided!')
            for mention in mentions:
                for member in message.guild.members:
                    if message.guild.get_role(self.title_roles['Queen']) in member.roles:
                        await member.remove_roles(message.guild.get_role(self.title_roles['Queen']))
                await message.guild.get_member(mention.id).add_roles(message.guild.get_role(self.title_roles['Queen']))
                await message.channel.send(f'<@{mention.id}> has been crowned Queen!')
        else:
            await message.channel.send('Insufficient user permissions.')

    async def update_board(self, game: Game, turn_incicator=False):
        channel = self.get_channel(game.channel_id)
        await channel.send('Incoming Board!')
        for final_substring in str(game).split('#msg'):
            await channel.send(final_substring)
        if turn_incicator:
            player = game.players[game.cache.current_player - 1]
            if player is not None:
                send = (
                    f'It is {channel.guild.get_role(player.role_id).mention}/'
                    f'<@{player.uid}>\'s turn! ')
            else:
                send = f'It is <@{game.players[game.cache.current_player - 1].uid}>\'s turn! '
            await channel.send(send)

    async def on_win(self, game):
        channel = self.get_channel(game.channel_id)
        winner = game.players[game.cache.current_player - 1]
        loser = game.players[(3 - game.cache.current_player) - 1]
        await channel.send(f'<@{winner.uid}> WINS!')
        for i, role_id in enumerate(game.role_ids):
            role = channel.guild.get_role(role_id)
            await role.delete() if role else role
        self.active_games.pop(channel.id)
        if game.channel_id not in self.game_history:
            self.game_history.append(game)
            await self.update_board(game)
            winner.calc_elo(loser, True)
            loser.calc_elo(winner, False)
            if channel.guild.id == self.official_guild:
                for player in game.players:
                    await self.update_rank_role(channel.guild, player)

            def val(p):
                return p.elo

            self.ranks.sort(key=val, reverse=True)

        async def channel_del():
            await channel.send('Channel will be deleted in 1hr, and has been moved to game history.')
            await asyncio.sleep(3600)
            await channel.delete(reason='Game Complete')

        asyncio.run_coroutine_threadsafe(channel_del(), asyncio.get_event_loop())
        await self.gen_replay(game)

    async def on_draw(self, game):
        channel = self.get_channel(game.channel_id)
        await channel.send('Game ends in a draw. Shake hands now.')
        for i, role_id in enumerate(game.role_ids):
            await channel.guild.get_member(game.players[i].uid).get_role(role_id).delete()
        self.active_games.pop(channel.id)
        if game.channel_id not in self.active_games:
            self.game_history.append(game)

        async def channel_del():
            await channel.send('Channel will be deleted in 1hr, and has been moved to game history.')
            await asyncio.sleep(3600)
            await channel.delete(reason='Game Complete')

        asyncio.run_coroutine_threadsafe(channel_del(), asyncio.get_event_loop())
        await self.gen_replay(game)

    async def gen_replay(self, game: Game):
        game.to_video(self.data_path.joinpath('temp/'), self.video_dir)
        replay = f'{game.players[0].name}-v-{game.players[1].name}.mp4'
        with open(self.video_dir.joinpath(replay), 'rb') as f:
            attachment = discord.File(f)
            await self.get_channel(DisquidClient.replay_channel).send(replay, file=attachment)

    async def close(self):
        await self.save(bypass=True)
        await super(DisquidClient, self).close()


if __name__ == '__main__':
    intents = Intents.default()
    intents.members = True
    DisquidClient(intents=intents).run(input('Bot API Token: '))
