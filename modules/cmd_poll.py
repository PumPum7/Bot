import discord
import datetime
from discord.ext import commands
import asyncio
import aiohttp

normal_poll = ["\U0001f44d", "\U0001f44e", "\U0001f937"]  # thumbs-down, thumbs-up and shrug emote
numbers = ["1\u20e3", "2\u20e3", "3\u20e3", "4\u20e3", "5\u20e3", "6\u20e3", "7\u20e3", "8\u20e3", "9\u20e3",
           "10\u20e3"]  # numbers from 1 to 10


class PollCommands:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="poll:")
    async def poll_cmd(self, ctx):
        """Start a normal poll"""
        for emote in normal_poll:
            await ctx.message.add_reaction(emote)

    @commands.command(name="poll::")
    async def poll_advanced_cmd(self, ctx, *, question: str=None):
        """Start a more advanced poll version."""
        if question is None:
            try:
                await ctx.message.author.send("You need to include a question.", delete_after=15.0)
                return
            except Exception:
                return
        else:
            try:
                await ctx.message.delete()
            except: pass
            embed = discord.Embed(
                color=discord.Color.default(),
                title=f"{ctx.message.author} started a poll:",
                description=f"{question}",
                timestamp=datetime.datetime.utcnow()
            )
            embed.set_footer(text="Vote using the reactions below.")
            msg = await ctx.send(embed=embed)
            for emote in normal_poll:
                await msg.add_reaction(emote)

    @commands.command(name="opoll:")
    async def option_poll(self, ctx, *, question_and_options: str=None):
        """Start a poll with options. divide the question and the options with `|`"""
        if question_and_options is not None:
            if question_and_options.__contains__("|"):
                q_s = question_and_options.split("|")
                if len(q_s) > 10:
                    return await ctx.send("You can only have up to 9 options.", delete_after=15.0)
                else:
                    text = ""
                    count = 0
                    for option in q_s[1:]:
                        count += 1
                        text = text + "\n" + f"{count}\u20e3" + " " + option
                    embed = discord.Embed(
                        color=0x36393E,
                        title=f"{ctx.message.guild.name} poll:",
                        description=q_s[1] + "\n" + text,
                        timestamp=datetime.datetime.utcnow()
                    )
                    embed.set_footer(text="Vote using the reactions below.")
                    msg = await ctx.send(embed=embed)
                    await ctx.message.delete()
                    for i in range(1, count+1):
                        await asyncio.sleep(0.5)
                        await msg.add_reaction(f"{i}\u20e3")
            else:
                embed = discord.Embed(
                    color=discord.Color.red(),
                    title="Something didn't go quite right.",
                    description="Please make sure you have followed the format."
                )
                await ctx.send(embed=embed)
        else:
            await ctx.send("Please specify a question and options.")

    async def __error(self, ctx, error):
        if isinstance(error, IndexError):
            return await ctx.send("An error occurred! Please make sure that you followed the format.", delete_after=10)
        elif isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.NoPrivateMessage):
            return await ctx.send("You can't use this command here.")

    @staticmethod
    async def __local_check(ctx):
        if ctx.guild is None:
            raise commands.NoPrivateMessage("You can only use this command in a guild.")
        else:
            return


def setup(bot):
    bot.add_cog(PollCommands(bot))


""" # Currently not working
    @commands.command(name="rpoll:")
    async def reaction_poll(self, ctx, *question_answers_and_emotes):
        all_emojis = self.bot.emojis
        guild = ctx.message.guild
        question = question_answers_and_emotes[0]
        a_e = question_answers_and_emotes[1:]
        only_answer = []
        only_emotes = []
        cnt = 0
        for i in a_e:
            if cnt == 1:
                only_answer.append(i)
                cnt = 0
            else:
                emote_id = self.emote_id(i)
                if self.bot.get_emoji(int(emote_id)) is None:
                    emote = await self.server_emote(emote_id, self.emote_name(i), guild.name)
                    emote = discord.utils.get(all_emojis, id=emote.id)
                    only_emotes.append(str(emote))
                else:
                    only_emotes.append(i)
                cnt = 1
        text = ""
        text_ = ""
        cnt = 0
        for i in a_e:
            if cnt == 0:
                text_ = str(i)
                cnt = 1
            else:
                text = text + f"\n{text_} {i} "
                cnt = 0
        test = f"{question}\n{text}"
        embed = discord.Embed(
            color=0x36393E,
            title=f"{ctx.message.guild.name} poll:",
            description=test,
            timestamp=datetime.datetime.utcnow()
        )
        embed.set_footer(text="Vote using the reactions below.")
        msg = await ctx.send(embed=embed)
        for emote in only_emotes:
            emote_id = self.emote_id(emote)
            emoji = self.bot.get_emoji(int(emote_id))
            if emoji is not None:
                await msg.add_reaction(emoji)
            else:
                emoji = await self.server_emote(emote_id, self.emote_name(emote), guild.name)
                await msg.add_reaction(emoji)
                
        async def server_emote(self, emote_id, emote_name, guild_name):
        link = f"https://cdn.discordapp.com/emojis/{emote_id}.png"
        for server in self.bot.guilds:
            if server.name != guild_name:
                if len(server.emojis) < 50:
                    try:
                        async with aiohttp.ClientSession() as cs:
                            async with cs.get(link) as r:
                                res = await r.read()
                                emote = await server.create_custom_emoji(name=emote_name, image=res,
                                                                         reason="Reaction poll")
                                return emote
                    except Exception as e:
                        return e
                else:
                    await asyncio.sleep(1.0)
                    for emoji in server.emojis:
                        try:
                            await emoji.delete(reason="Too many emotes")
                        except Exception:
                            pass
                    try:
                        async with aiohttp.ClientSession() as cs:
                            async with cs.get(link) as r:
                                res = await r.read()
                                file_name = f'{emote_name}.png'
                                with open(file_name, 'wb') as f:
                                    f.write(res)
                                emote = await server.create_custom_emoji(emote_name, image=file_name,
                                                                         reason="Reaction poll")
                                return emote
                    except Exception as e:
                        return e

    @staticmethod
    def emote_id(emote):
        emote_id = emote.split(":")[2]
        emote_id = emote_id.replace(">", "")
        return emote_id

    @staticmethod
    def emote_name(emote):
        emote_name = emote.split(":")[1]
        return emote_name
"""
