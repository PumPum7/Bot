from discord.ext import commands
from functions.help_paginator import HelpPaginator


class Meta:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def cmd_help(self, ctx, *, command_: str = None):
        """Shows help about a command or the bot"""
        try:
            if command_ is None:
                p = await HelpPaginator.from_bot(ctx)
            else:
                entity = self.bot.get_cog(command_) or self.bot.get_command(command_)

                if entity is None:
                    clean = command_.replace('@', '@\u200b')
                    return await ctx.send(f'Command or category "{clean}" not found.')
                elif isinstance(entity, commands.Command):
                    p = await HelpPaginator.from_command(ctx, entity)
                else:
                    p = await HelpPaginator.from_cog(ctx, entity)

            await p.paginate()
        except Exception as e:
            print(e)
            await ctx.send("Something didn't go quite right. Please try again later.")


def setup(bot):
    meta = Meta(bot)
    bot.remove_command("help")
    bot.add_command(meta.cmd_help)
