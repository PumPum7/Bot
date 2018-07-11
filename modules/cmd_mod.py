import discord
from discord.ext import commands
import random
import datetime
from asyncio import TimeoutError, sleep

import bot_settings


class ModCommands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def ban_cmd(self, ctx, user: discord.User=None, *, reason=None):
        # makes sure a user object has been supplied
        if user is None:
            random_user = random.choice(ctx.message.guild.members).name
            embed = discord.Embed(
                color=discord.Color.red(),
                title="An error occurred:",
                description="You need to supply a user which should get banned, you can either use id, mention or the"
                            f"users name.\nExample: `{bot_settings.prefix[0]}ban {random_user}`"
            )
            return await ctx.send(embed=embed, delete_after=10)
        #  asks before the ban happens if everything is right
        text = ""
        mod = ctx.message.author
        if reason is not None:
            text = f"Reason: `{reason}`\n"
        text = f"{text}User: {user.display_name}#{user.discriminator} ({user.id})\n" \
               f"Moderator: {mod.display_name}#{mod.discriminator} ({mod.id})"
        embed = discord.Embed(
            color=discord.Color.green(),
            title="Confirmation:",
            description=f"Please make sure all information are right. Once you respond with `confirm`"
                        f" I will ban {user.mention}:\n{text}\nIf anything is wrong please respond with `cancel`.",
            timestamp=datetime.datetime.utcnow()
        )
        msg = await ctx.send(embed=embed)

        def check(message):
            return message.author == message.author and str(message.content) in ["cancel", "confirm"]
        try:
            response = await self.bot.wait_for("message", check=check, timeout=15.0)
        except TimeoutError:
            embed = discord.Embed(
                color=discord.Color.red(),
                title="An error occurred:",
                description="You only have 15 seconds to respond. Please try again, "
                            "if you want to cancel it please respond with `cancel`."
            )
            msg_2 = await ctx.send(embed=embed)
            try:
                response = await self.bot.wait_for("message", check=check, timeout=15.0)
            except TimeoutError:
                await msg_2.edit(embed=discord.Embed(color=discord.Color.red(), title="You took to long again.",
                                 description="I have now canceled the banning process."),
                                 delete_after=10)
                return
        # checks which option the user chose
        if str(response.content).lower() == "cancel":
            embed = discord.Embed(
                color=discord.Color.green(),
                title="I have canceled the process.",
                description="\uFEFF"
            )
            await msg.edit(embed=embed, delete_after=10)
        if str(response.content).lower() == "confirm":
            server = ctx.message.guild
            case_time = datetime.datetime.now().strftime("%Y-%m-%d %I:%M%p")
            reason = f'{user.name} was banned by {mod.name} for "{reason} at {case_time}'
            try:
                await server.ban(user=user, reason=reason, delete_message_days=2)
                embed = discord.Embed(
                    color=discord.Color.green(),
                    title=f"Successfully banned {user.name}",
                    description=text
                )
                await msg.edit(embed=embed)
            except Exception as e:
                print(f"an error occurred:{e}\nGuild: {ctx.message.guild}")
                embed = discord.Embed(
                    color=discord.Color.red(),
                    title="An error occurred:",
                    description="The error was reported."
                )
                await msg.edit(embed=embed)

    @ban_cmd.error
    async def error_ban(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                color=discord.Color.red(),
                title="An error occurred:",
                description="Please provide a user. This can either be an ID, mention or name."
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                color=discord.Color.red(),
                title="An error occurred:",
                description="I am missing the `ban members` permission. Please give me this permission and "
                            "then try again."
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                color=discord.Color.red(),
                title="An error occurred:",
                description="You need the `ban members` permission in order to use this command."
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.NoPrivateMessage):
            return
        elif isinstance(error, commands.CommandError):
            print(error)

    @commands.command(name="fastban", aliases=["fast_ban", "quickban"])
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.guild_only()
    async def fast_ban_cmd(self, ctx, user: discord.User=None, *, reason=None):
        if reason is None:
            reason = f"{user.name} was banned by {ctx.message.author}"
        await ctx.message.guild.ban(user=user, reason=reason, delete_message_days=7)
        embed = discord.Embed(
            color=discord.Color.green(),
            title=f"Successfully banned {user.name}"
        )
        await ctx.send(embed=embed)

    @fast_ban_cmd.error
    async def fast_ban_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                color=discord.Color.red(),
                title="An error occurred:",
                description="Please provide a user. This can either be an ID, mention or name."
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BotMissingPermissions):
            embed = discord.Embed(
                color=discord.Color.red(),
                title="An error occurred:",
                description="I am missing the `ban members` permission. Please give me this permission and "
                            "then try again."
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingPermissions):
            pass
        elif isinstance(error, commands.NoPrivateMessage):
            return
        elif isinstance(error, commands.CommandError):
            print(error)


def setup(bot):
    bot.add_cog(ModCommands(bot))
