from functions import database
import discord
from discord.ext import commands
import bot_settings
import asyncio
import traceback
from functions.paginator import SimplePaginator


class ServerSettings:
    def __init__(self, bot):
        self.bot = bot
        self.db = database.ServerDatabase()

    @commands.group(name="settings", aliases=["set", "setting"], invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def settings(self, ctx):
        """Take a look at your current server settings. Use .help settings for more information"""
        guild_id = ctx.guild.id
        prefix = self.db.get_prefix(guild_id)[0]
        join_log = self.db.get_join_log(guild_id)[0]
        join_msg = self.db.get_join_msg(guild_id)[0]
        leave_msg = self.db.get_leave_msg(guild_id)[0]
        bot_role = self.db.get_bot_role(guild_id)[0]
        giveaway_channel = self.db.get_giveaway_channel(guild_id)[0]
        giveaway_donation = self.db.get_donation_status(guild_id)
        giveaway_log = self.db.get_giveaway_log(guild_id)[0]
        standard_embed_txt = f"If you would like to change any of those settings please use the `{ctx.prefix}help " \
                             f"settings` command for more information."
        embed = discord.Embed(
            color=3553598,
            title="Server setting information:",
            description=standard_embed_txt
        )
        embed.add_field(
            name="Join/Leave log settings:",
            value=f"Log channel: {join_log}\n"
                  f"Join message: `{join_msg if join_msg is not None else 'not set'}`\n"
                  f"Leave message: `{leave_msg if leave_msg is not None else 'not set'}`\n"
                  f"**Note: **If a user leaves/joins and no leave/join message is specified nothing will get "
                  f"posted."
        )
        embed1 = discord.Embed(
            color=3553598,
            title="Server setting information:",
            description=standard_embed_txt
        )
        embed1.add_field(
            name="Giveaway settings:",
            value=f"Giveaway channel: {giveaway_channel}\nDonations: {'enabled' if giveaway_donation else 'disabled'}\n"
                  f"Log channel: {giveaway_log}\n"
                  f"**Note:** If you would like that your members are able to donate keys, ... for giveaways every "
                  f"giveaway setting has to be set to a value."
        )
        embed2 = discord.Embed(
            color=3553598,
            title="Server setting information:",
            description=standard_embed_txt
        )
        embed2.add_field(
            name="Other settings:",
            value=f"Prefix: {prefix}\nBot role: {bot_role}"
        )
        embed.set_footer(text="Use the reactions below to switch between the pages.")
        embed1.set_footer(text="Use the reactions below to switch between the pages.")
        embed2.set_footer(text="Use the reactions below to switch between the pages.")
        await SimplePaginator(extras=[embed, embed1, embed2]).paginate(ctx)

    @settings.command(name="prefix")
    @commands.has_permissions(manage_guild=True)
    async def prefix_cmd(self, ctx, *, prefix=None):
        """Set a new server specific prefix or check the current server prefix. This will overwrite old prefixes."""
        guild_id = ctx.guild.id
        cur_prefix = self.db.get_prefix(guild_id)[0]
        if prefix is None:
            embed = discord.Embed(
                color=3553598,
                title="Prefix information:",
                description=f"Current server prefix: {cur_prefix}\nGlobal prefix: {bot_settings.prefix[0]}\n"
                            f"If you want to set a new server prefix please use `{ctx.prefix}{ctx.command} "
                            f"<prefix>`"
            )
            return await ctx.send(embed=embed)
        if cur_prefix is not None:
            msg = await ctx.send(f"Your current prefix is `{cur_prefix}`. Would you like to set `{prefix}` as the new"
                                 f" prefix? If yes please click the 👍 reaction.")
            await msg.add_reaction("👍")
            try:
                def check(reaction, user):
                    return user == ctx.author and reaction.emoji == "👍"
                await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
                await msg.edit(content=f"Okay I will now change the prefix from {cur_prefix} to {prefix}",
                               delete_after=5)
            except asyncio.TimeoutError:
                return await msg.edit(content="The changing of the prefix has been canceled.", delete_after=10)
        result = self.db.set_prefix(guild_id, prefix)
        if result:
            await ctx.send(f"Successfully set the prefix to {prefix}!")
        else:
            await ctx.send("Something didn't go quite right. The error has been reported.")

    @settings.group(name="welcome", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def cmd_welcome(self, ctx):
        """Get details about the current welcoming settings. Use .help settings welcome for more information"""
        guild_id = ctx.guild.id
        join_log_channel = self.db.get_join_log(guild_id)[0]
        join_msg = self.db.get_join_msg(guild_id)[0]
        leave_msg = self.db.get_leave_msg(guild_id)[0]
        join_log_channel = discord.utils.get(ctx.guild.channels, id=join_log_channel).mention \
            if join_log_channel is not None else "not set"
        embed = discord.Embed(
            color=3553598,
            title="Join/Leave log information:",
            description=f"Log channel: {join_log_channel}\n"
                        f"Join message: `{join_msg if join_msg is not None else 'not set'}`\n"
                        f"Leave message: `{leave_msg if leave_msg is not None else 'not set'}`\n"
                        f"**Note: **If a user leaves/joins and no leave/join message is specified nothing will get "
                        f"posted."
        )
        embed.add_field(
            name="How to change/set these settings?",
            value=f"Log channel: `{ctx.prefix}set welcome channel [channel mention]`\n"
                  f"Leave message: `{ctx.prefix}set welcome leavemsg [message]`\n"
                  f"Join message: `{ctx.prefix}set welcome joinmsg [message]`"
        )
        await ctx.send(embed=embed)

    @cmd_welcome.command(name="channel")
    @commands.has_permissions(manage_guild=True)
    async def cmd_join_logs(self, ctx, channel: discord.TextChannel=None):
        """Set a channel for the join and leave logs"""
        if channel is None:
            join_log_channel = self.db.get_join_log(ctx.guild.id)[0]
            join_log_channel = discord.utils.get(ctx.guild.channels, id=join_log_channel).mention \
                if join_log_channel is not None else "not set"
            return await ctx.send(f"Current join/leave log: {join_log_channel}.\nPlease supply a channel if you "
                                  f"would like to change this setting.")
        if not channel.permissions_for(ctx.me).send_messages:
            return await ctx.send("Please make sure that I can send message in this channel.")
        result = self.db.set_join_log(ctx.guild.id, channel.id)
        if result:
            return await ctx.send(f"{channel.mention} was successfully set as log channel.")
        else:
            return await ctx.send(f"Something didn't go quite right. The error has been reported.")

    @cmd_welcome.command(name="joinmsg")
    @commands.has_permissions(manage_guild=True)
    async def cmd_join_msg(self, ctx, *, message=None):
        """Change the current join message. Use -set welcome options to see a list of all possible options."""
        if message is None:
            join_msg = self.db.get_join_msg(ctx.guild.id)[0]
            return await ctx.send(f"Current join message: `{join_msg if join_msg is not None else 'not set'}`.\n"
                                  f"Please supply a new message if you would  like to change this setting.")
        message_example = message.replace('%USER%', ctx.author.mention).replace('%SERVER%', ctx.guild.name)\
            .replace("%MEMBERCOUNT%", str(ctx.guild.member_count))
        msg = await ctx.send(f"Example of this message: {message_example}\nWould you like to set this as join message? "
                             f"If yes please click on the \U0001F44D reaction.")
        await msg.add_reaction("\U0001F44D")
        try:
            def check(reaction, user):
                return user == ctx.author and reaction.emoji == "👍"

            await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
        except asyncio.TimeoutError:
            return await msg.edit(content="The setting of the join message has been successfully cancelled!")
        if self.db.set_join_msg(ctx.guild.id, message):
            embed = discord.Embed(
                color=3553598,
                title="Successfully updated the join message.",
                description=f"New join messages: `{message}`"
            )
            embed.set_footer(text=f"To see a list of all possible options please use {ctx.prefix}set welcome "
                                  f"options.")
            await msg.edit(embed=embed, content="")
        else:
            return await msg.edit(content="Something didn't go quite right. Please try again later")

    @cmd_welcome.command(name="leavemsg")
    @commands.has_permissions(manage_guild=True)
    async def cmd_leave_msg(self, ctx, *, message=None):
        """Change the current leave message. Use -set welcome options to see a list of all possible options."""
        if message is None:
            join_msg = self.db.get_leave_msg(ctx.guild.id)
            return await ctx.send(f"Current leave message: `{join_msg[0] if join_msg is not None else 'not set'}`.\n"
                                  f"Please supply a new message if you would  like to change this setting.")
        message_example = message.replace('%USER%', ctx.author.mention).replace('%SERVER%', ctx.guild.name)\
            .replace("%MEMBERCOUNT%", str(ctx.guild.member_count))
        msg = await ctx.send(f"Example of this message: {message_example}\nWould you like to set this as leave message?"
                             f" If yes please click on the \U0001F44D reaction.")
        await msg.add_reaction("\U0001F44D")
        try:
            def check(reaction, user):
                return user == ctx.author and reaction.emoji == "👍"

            await self.bot.wait_for('reaction_add', timeout=15.0, check=check)
        except asyncio.TimeoutError:
            return await msg.edit(content="The setting of the leave message has been successfully cancelled!")
        if self.db.set_leave_msg(ctx.guild.id, message):
            embed = discord.Embed(
                color=3553598,
                title="Successfully updated the leave message.",
                description=f"New leave messages: `{message}`"
            )
            embed.set_footer(text=f"To see a list of all possible options please use {ctx.prefix}set welcome "
                                  f"options.")
            await msg.edit(embed=embed, content="")
        else:
            return await msg.edit(content="Something didn't go quite right. Please try again later")

    @settings.group(name="botrole", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def botrole_cmd(self, ctx, role: discord.Role=None):
        """Set a role as botrole. Every bot account which joins will automatically get this role."""
        cur_botrole = self.db.get_bot_role(ctx.guild.id)
        if role is None:
            role = discord.utils.get(ctx.guild.roles, id=cur_botrole[0])
            return await ctx.send(f"Current bot role: {role.name}\nIf you would like to change this setting please"
                                  f" supply a role. If you want to remove the bot role please use `{ctx.prefix}set"
                                  f" botrole disable`.")
        if not ctx.me.top_role.position > role.position:
            return await ctx.send("Something didn't go quite right. Please make sure that my role is lower in the role"
                                  " hierarchy than my current highest role.")
        if self.db.set_bot_role(ctx.guild.id, role.id):
            await ctx.send(f"Successfully set {role.name} as new bot role!")
        else:
            await ctx.send("Something didn't go quite right. The error has been reported!")

    @cmd_welcome.command(name="options")
    @commands.has_permissions(manage_messages=True)
    async def cmd_welcome_options(self, ctx):
        """Get a list of all possible options for the leave/join msg"""
        embed = discord.Embed(
            color=3553598,
            title="Options for the leave/join message:",
            description="%USER% -> gets replaced with the user mention\n%MEMBERCOUNT% -> gets replaced with the new"
                        " membercount\n%SERVER% -> gets replaced with the server name"
        )
        embed.set_footer(text="More options will be added soon.")
        await ctx.send(embed=embed)

    @botrole_cmd.command(name="disable", aliases=["off"])
    @commands.has_permissions(manage_server=True)
    async def cmd_botrole_disable(self, ctx):
        """Disable the auto bot role."""
        if self.db.set_bot_role(ctx.guild.id, None):
            return await ctx.send("The bot role has been successfully disabled!")
        return await ctx.send("Something didn't go quite right. Please try again later.")

    @settings.group(name="giveaway", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def giveaway_settings(self, ctx):
        """Get your current giveaway settings"""
        # gets the information
        guild_id = ctx.guild.id
        channel = self.db.get_giveaway_channel(guild_id)
        log_channel = self.db.get_giveaway_log(guild_id)
        if not log_channel: log_channel = None
        else: log_channel = discord.utils.get(ctx.guild.channels, id=log_channel[0])
        if channel is None:
            channel = "not set"
        else: log_channel = log_channel.mention
        if not channel: channel = None
        else: channel = discord.utils.get(ctx.guild.channels, id=channel[0])
        if channel is None:
            channel = "not set"
        else: channel = channel.mention
        donation_status = self.db.get_donation_status(guild_id)
        # creates and sends the embed
        embed = discord.Embed(
            color=3553598,
            title="Giveaway settings:",
            description=f"Giveaway channel: {channel}\nDonations: {'enabled' if donation_status else 'disabled'}\n"
                        f"Log channel: {log_channel}\n"
                        f"If you would like that your members are able to donate keys, ... for giveaways every giveaway"
                        f" setting has to be set to a value."
        )
        embed.add_field(
            name="How to change/set these settings?",
            value=f"Giveaway channel: `{ctx.prefix}settings giveaway channel <text channel>`\n"
                  f"Donation setting: `{ctx.prefix}settings giveaway donation <enable/disable>`\n"
                  f"Giveaway log channel: `{ctx.prefix}settings giveaway logchannel <text channel>`"
        )
        await ctx.send(embed=embed)

    @giveaway_settings.command(name="channel")
    @commands.has_permissions(manage_guild=True)
    async def giveaway_channel_setting(self, ctx, channel: discord.TextChannel=None):
        """Set/get the current giveaway channel"""
        if channel is None:
            channel = self.db.get_giveaway_channel(ctx.guild.id)
            return await ctx.send(f"Current giveaway channel: {channel[0]}\nIf you want to change this setting please"
                                  f" follow this format: `{ctx.prefix}settings channel <text channel>`.")
        channel_perm = channel.permissions_for(ctx.me)
        if not channel_perm.send_messages and channel_perm.embed_links and channel_perm.add_reactions:
            return await ctx.send("Please make sure that I have the following permissions in this channel: "
                                  "`send_messages`, `embed_links` and `add_reactions`")
        if self.db.set_giveaway_channel(ctx.guild.id, channel.id):
            await ctx.send(f"{channel.mention} has successfully been set as giveaway channel")
        else:
            await ctx.send("Something didn't go quite right. Please try again later.")

    @giveaway_settings.command(name="donations", aliases=["donation"])
    @commands.has_permissions(manage_guild=True)
    async def giveaway_donation_setting(self, ctx, status=None):
        """Set/get the donation status for this guild"""
        if status is None:
            dstatus = self.db.get_donation_status(ctx.guild.id)
            return await ctx.send(f"You are currently {'not' if not dstatus else ''} accepting donations for giveaways"
                                  f".\nIf you want to change this setting please follow this format: `{ctx.prefix}"
                                  f"settings donation <status>`. Status can either be `enable` or `disable`. "
                                  f"**Note:** if you have set it to `True` people will be able to donate keys, ....")
        if self.db.set_donation_status(status=status, server_id=ctx.guild.id):
            return await ctx.send("The setting has been successfully changed!")
        else:
            return await ctx.send("Something didn't go quite right. Please try again later.")

    @giveaway_settings.command(name="logchannel", aliases=["glog"])
    @commands.has_permissions(manage_guild=True)
    async def giveaway_log_channel(self, ctx, channel: discord.TextChannel=None):
        """Set/get the current log channel for giveaways."""
        if channel is None:
            channel = self.db.get_giveaway_log(ctx.guild.id)
            if not channel and channel is None:
                text = "Currently no log channel is set."
            else:
                channel = discord.utils.get(ctx.guild.channels, id=channel[0])
                text = f"Current log channel: {channel.mention if channel is not None else 'not set'}"
            return await ctx.send(f"{text}\n"
                                  f"If you want to change this setting please follow this format: "
                                  f"`{ctx.prefix}settings logchannel <text channel>`. All giveaway donations "
                                  f"will be logged in there")
        channel_perm = channel.permissions_for(ctx.me)
        if channel_perm.send_messages and channel_perm.read_message_history and channel_perm.add_reactions and \
                channel_perm.embed_links:
            if self.db.set_giveaway_log(ctx.guild.id, channel.id):
                return await ctx.send(f"The giveaway log channel has been successfully changed to {channel.mention}!")
        return await ctx.send(f"Something didn't go quite right. Please make sure that I have the following"
                              f" permissions in {channel.mention}: `send_messages`, `embed_links` and `add_rea"
                              f"ctions")

    @staticmethod
    async def __error(ctx, error):
        if isinstance(error, IndexError):
            return await ctx.send("An error occurred! Please make sure that you followed the format.", delete_after=10)
        elif isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.message.add_reaction("❌")
            return await ctx.send("You can't use this command here.")
        elif isinstance(error, commands.NotOwner):
            return
        elif isinstance(error, commands.BadArgument):
            return await ctx.send("Please make sure that this user/channel is valid.")
        print(f"An error occurred: Command: {ctx.command}\nError: {traceback.format_exc()}")
        await ctx.send(f"An error occurred: {traceback.format_exc()}")



def setup(bot):
    bot.add_cog(ServerSettings(bot))


# TODO: Write options command
