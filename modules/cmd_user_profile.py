import discord
from discord.ext import commands

import bot_settings
from functions import prefix_functions


class Profile:
    def __init__(self, bot):
        self.bot = bot
        self.prefix = prefix_functions.PrefixFunc()

    @commands.command(name="setprefix", aliases=["prefix"])
    async def cmd_setprefix(self, ctx, *, prefix: str=None):
        """Change your user prefix to a specified prefix"""
        if prefix is None:
            prefix = bot_settings.prefix[0]
        if self.prefix.set_prefix(prefix, "users", ctx.author.id):
            await ctx.send(f"Your prefix was successfully set to `{prefix}`.")
        else:
            await ctx.send("An error occurred while changing your prefix. Please try again later.")

    @commands.command(name="profile")
    async def profile(self, ctx, user: discord.Member=None):
        """Get some information about your or another persons profile."""
        if user is None:
            user = ctx.author
        prefix = self.prefix.get_user_prefix(user.id)
        if prefix is None:
            prefix = [None]
        prefix = prefix[0]
        embed = discord.Embed(
            color=0x36393E,
            title=f"Bot settings for {user.name}",
            description=f"Prefix: {prefix if prefix is not None else 'not set'}"
        )
        await ctx.send(embed=embed)



def setup(bot):
    bot.add_cog(Profile(bot))
