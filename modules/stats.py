import discord
from discord.ext import commands
import os
import json
import asyncio
import datetime

STATS_LIST = None
NO_MESSAGES = "This value will be specified soon."
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Stats:
    def __init__(self, bot, *args, **kwargs):
        self.bot = bot
        self.counter = dict()
        self.stats = get_stats()
        super().__init__(*args, **kwargs)
        self.bg_task = self.bot.loop.create_task(self.my_background_task())
        self.needed = 2

    @asyncio.coroutine
    async def on_message(self, message):
        if message.guild is not None:
            guild_id = message.guild.id
        else:
            return
        # check if the server is registered
        if str(guild_id) in self.stats.get_registered_servers():
            # checks if the counter is 50, if yes it sets it in the json
            server_counter = self.counter.get(guild_id, None)
            if server_counter is not None:
                self.counter[guild_id] += 1
            else:
                self.counter[guild_id] = 1
            if self.counter.get(guild_id) == self.needed:
                self.counter[guild_id] = 0
                self.stats.update(guild_id)
            return

    @commands.command(name="stats_setup")
    @commands.has_permissions(administrator=True)
    async def stats_setup(self, ctx, *, channel: discord.TextChannel):
        """Setup the stats function."""
        bot = ctx.me
        guild_id = ctx.guild.id
        # checks if the bot has the permission to post in the selected channel
        if channel.permissions_for(bot).send_messages and channel.permissions_for(bot).embed_links:
            # checks if the bot is already registered, if yes it asks if the user wants to change the settings
            if guild_id in self.stats.get_registered_servers():
                await ctx.send("This server is already registered, would you like to change the channel? If "
                               "yes please respond with `yes`, otherwise with `cancel`.")

                def check(m):
                    return m.author == ctx.author

                msg = await self.bot.wait_for("message", check=check)
                if msg.content.lower() == "cancel":
                    return await ctx.send("Canceled setup process.")
                if msg.content.lower() != "yes":
                    return await ctx.send("Please only respond with `yes` or `cancel`.")
            # sends the message
            msg = await channel.send(embed=self.stats_embed(ctx.guild))
            # checks if everything went right
            if self.stats.register_server(guild_id, channel.id, msg.id):
                return await ctx.send(f"Successfully set {channel} as stats channel.")
            # error handler
            await ctx.send("Something didn't go quite right.")
            await msg.delete()

    @stats_setup.error
    async def error_stats_setup(self, ctx, error):
        # error handler
        if isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Please specify a valid channel.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Please specify a valid channel. You can either use the name, ID or mention.")
        elif isinstance(error, commands.CommandError):
            print(error)

    @staticmethod
    def stats_embed(guild: discord.Guild, messages_hour=NO_MESSAGES, messages_day=NO_MESSAGES):
        # creates the embed for the stats post
        embed = discord.Embed(
            color=discord.Color.blue(),
            title=f"Stats for {guild.name}",
            description="I will update this message every hour."
        )
        embed.add_field(name="Message count:", value=f"**>** Messages/hour: {messages_hour}\n"
                                                     f"**>** Messages/day: {messages_day}", inline=False)
        embed.add_field(name="Role count:", value=f"**>** {len(guild.roles)} roles", inline=False)
        embed.add_field(name="Member count:", value=f"**>** {guild.member_count} members", inline=False)
        embed.add_field(name="Channel count:", value=f"**>** {len(guild.channels)}", inline=False)
        return embed

    async def my_background_task(self):
        # does something every X minutes/hours
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(3600.0)
            all_servers = self.stats.get_registered_servers()
            for server_id in all_servers:
                server = all_servers[server_id]
                channel_id = server["channel_id"]
                msg_id = server["msg_id"]
                try:
                    channel = self.bot.get_channel(channel_id)
                    msg = await channel.get_message(msg_id)
                    guild = self.bot.get_guild(int(server_id))
                    stats_for_server = self.stats.get_stats(server_id)
                    await msg.edit(embed=self.stats_embed(guild, messages_day=stats_for_server["messages/day"],
                                                          messages_hour=stats_for_server["messages/hour"]))
                    result = self.stats.edit_stats_post(server_id)
                except Exception as e:
                    print(e)
                    print(f"Something is wrong with {guild.name}")
                    return
                if len(result) == 2:
                    if not self.stats.set_stats(server_id, 0, 0):
                        print(f"Something is wrong with {guild.name}")
                    return
                elif len(result) == 1:
                    if not self.stats.set_stats(server_id, hour_value=0):
                        print(f"Something is wrong with {guild.name}")
                    return
                else:
                    return


class DoSomethingWithStats:
    def __init__(self):
        self.file = "stats.json"
        self.list_ = {}
        if os.path.exists(self.file):
            with open(self.file, 'r') as f_:
                self.list_ = json.loads(f_.read())

    def update(self, server_id, value=50):
        try:
            # sets values for the message counter
            server_id = str(server_id)
            if self.list_.get(server_id, None) is not None:
                server = self.list_.get(server_id, None)
                messages_hour = server.get("messages/hour", None)
                messages_day = server.get("messages/day", None)
                if value is not 0:
                    if messages_day is None:
                        server["messages/day"] = value
                    else:
                        server["messages/day"] += value
                    if messages_hour is None:
                        server["messages/hour"] = value
                    else:
                        server["messages/hour"] += value
                    self.save()
            else:
                if value is 0:
                    return False
                server = self.list_[server_id] = {}
                server["messages/hour"] = value
                server["messages/day"] = value
                self.save()
            return True
        except Exception as e:
            print(e)
            return False

    def get_stats(self, server_id):
        server_id = str(server_id)
        return self.list_.get(server_id, None)

    def save(self):
        with open(self.file, "w") as b_:
            json.dump(self.list_, b_, indent=4)
        return

    def register_server(self, server_id, channel_id, msg_id):
        server_id = str(server_id)
        servers = self.list_.get("registered_servers", None)
        try:
            if servers is None:
                self.list_["registered_servers"] = {server_id: {"channel_id": channel_id, "msg_id": msg_id}}
            else:
                self.list_["registered_servers"][server_id] = {"channel_id": channel_id, "msg_id": msg_id}
            self.save()
            return True
        except Exception as e:
            print(e)
            return False

    def get_registered_servers(self):
        return self.list_.get("registered_servers", {})

    def unregister_server(self, server_id):
        server_id = str(server_id)
        # removes a server from the registered list
        servers = self.list_.get("registered_servers", None)
        if servers is None:
            return False
        if servers.get(server_id, None) is None:
            return False
        servers.pop(server_id)
        return True

    def edit_stats_post(self, server_id):
        # returns which values have to be edited
        last_edit = self.list_[server_id].get("last_edit", None)
        if last_edit is None:
            self.list_[server_id]["last_edit"] = datetime.datetime.utcnow().strftime(TIME_FORMAT)
            return ["hour", "day"]
        now = datetime.datetime.utcnow()
        then = datetime.datetime.strptime(last_edit, TIME_FORMAT)
        difference = (now - then).total_seconds()/3600
        if difference >= 1:
            self.list_[server_id]["last_edit"] = datetime.datetime.utcnow().strftime(TIME_FORMAT)
            return ["hour"]
        if difference >= 24:
            self.list_[server_id]["last_edit"] = datetime.datetime.utcnow().strftime(TIME_FORMAT)
            return ["hour", "day"]
        else:
            print("something is ded")
            return []

    def set_stats(self, server_id, hour_value=None, day_value=None):
        try:
            # sets values for the message counter
            server_id = str(server_id)
            if self.list_.get(server_id, None) is not None:
                server = self.list_.get(server_id, None)
                messages_hour = server.get("messages/hour", None)
                messages_day = server.get("messages/day", None)
                if messages_day is None:
                    return False
                if messages_day is not None and day_value is not None:
                    server["messages/day"] = day_value
                if messages_hour is None:
                    return False
                if messages_hour is not None and hour_value is not None:
                    server["messages/hour"] = hour_value
                self.save()
            else:
                return False
            return True
        except Exception as e:
            print(e)
            return False


def get_stats():
    global STATS_LIST
    if STATS_LIST is None:
        STATS_LIST = DoSomethingWithStats()
    return STATS_LIST


def setup(bot):
    bot.add_cog(Stats(bot))
