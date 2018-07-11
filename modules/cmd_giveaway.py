from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands
import discord
import datetime
from random import choice, randint
import re
import asyncio
from functions import database
import functools

DATE_STRING = "{days}d{hours}h{minutes}m"
GIVEAWAY_EMOTE = "🎉"


class Giveaway:
    def __init__(self, bot):
        self.bot = bot
        self.db = database.GiveawayDatabase()
        self.sdb = database.ServerDatabase()

    @commands.group(name="giveaway", invoke_without_command=True)
    async def giveaway(self, ctx):
        """A basic guide for the giveaway cog"""
        embed = discord.Embed(
            color=discord.Color.blue(),
            title="Giveaway guide",
            description=f"Basic format: `{ctx.prefix}giveaway start {DATE_STRING + ' - duration'} {'prize'}`"
                        f"\nBoth the prize and the duration are required arguments."
        )
        if ctx.guild is not None:
            channel = choice(ctx.guild.channels)
            cnt = 0
            while type(channel) != discord.TextChannel:
                cnt += 1
                channel = choice(ctx.guild.channels)
                if cnt > 20:
                    channel_mention = "{channel mention}"
            if not cnt > 20:
                channel_mention = channel.mention
        embed.add_field(
            name="More information:",
            value="If you want to host the giveaway in a specified channel add `{channel mention}c` to the command."
                  f" Example: {ctx.prefix}giveaway start 7d10h discord nitro {channel_mention}c. You **have to**"
                  f" use a channel mention and don't forget the `c` after it.\nIf you want to host a giveaway"
                  " with a specified amount of winners add `{number from 1 to 9}w` to the command. "
                  f"Example: {ctx.prefix}giveaway start 2h discord nitro {randint(1, 9)}w.\nBoth of these extra "
                  " features are not needed arguments."
        )
        await ctx.send(embed=embed)

    @giveaway.command(name="start")
    @commands.guild_only()
    @commands.has_any_role("Giveaways", "giveaways", "Giveaway", "giveaway")
    async def cmd_giveaway(self, ctx, time: str=None, *, prize: str=None):
        """Start giveaways, use -giveaway for more information"""
        # check the inputs
        winners = re.search("[\d]w", prize)
        if winners is not None:
            prize = prize.replace(winners.group(0), "")
            winners = int(winners.group(0).replace("w", ""))
            if winners == 0:
                winners = 1
        else:
            winners = 1
        channel = re.search(r"<#(?P<channel_id>\d+)>c", prize)
        if channel is not None:
            prize = prize.replace(channel.group(0), "")
            channel = discord.utils.get(ctx.guild.channels, id=int(channel.groupdict()["channel_id"]))
        else:
            channel = ctx.channel
        perms = channel.permissions_for(ctx.me)
        if not perms.add_reactions and perms.embed_links and perms.send_messages and perms.read_messages:
            return await ctx.send(content="Please make sure that I have the `send_messages`, `embed_links`, `read_"
                                          "messages` and `add_reactions` permission in this channel.",
                                  delete_after=15.0)
        end_time = self.end_time(time)
        if end_time is None:
            return await ctx.send(f"Please follow the format: `{DATE_STRING}`. You can also only use "
                                  "one/two of the three possible time units.", delete_after=15.0)
        if prize is None:
            return await ctx.send(f"Please follow the format: `{ctx.prefix}{ctx.command} {DATE_STRING} {'{prize}'}`",
                                  delete_after=15.0)
        # send the giveaway embed
        # set up the scheduler and send the confirmation message
        await self.start_giveaway(end_time, prize, channel, winners)
        await ctx.send("Giveaway started!", delete_after=10)

    def end_time(self, time):
        # makes the end time of the giveaway
        if time is None: return None
        try:
            days = 0; hours = 0; minutes = 0
            new_tm = self.get_time(time, "d")
            if new_tm is not None:
                time = new_tm[1]
                days = new_tm[0]
            new_tm = self.get_time(time, "h")
            if new_tm is not None:
                time = new_tm[1]
                hours = new_tm[0]
            new_tm = self.get_time(time, "m")
            if new_tm is not None:
                minutes = new_tm[0]
            if days is 0 and hours is 0 and minutes is 0:
                minutes = time
            return datetime.datetime.now() + datetime.timedelta(days=float(days), hours=float(hours),
                                                                minutes=float(minutes))
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None

    @staticmethod
    def get_time(time, unit: str):
        # time maker
        if unit in time:
            new_tm = time.split(unit)
            return new_tm
        else:
            return None

    async def giveaway_embed(self, prize, channel: discord.TextChannel, msg_id: int, winner_num: int, end_date,
                             giveaway_id=None):
        try:
            # creates the embed for the commands
            message = await channel.get_message(msg_id)
            if message is None:
                return await channel.send(content="I couldn't determine a winner.")
            reactions = message.reactions
            winners = []
            await message.remove_reaction(member=message.author, emoji=f"{GIVEAWAY_EMOTE}")
            for reaction in reactions:
                if reaction.emoji == f"{GIVEAWAY_EMOTE}":
                    for i in range(winner_num):
                        winners.append(choice(await reaction.users().flatten()))
            if len(winners) < 1:
                return await message.edit(content="I couldn't determine a winner.")
            text = await self.text_builder(winners)
            embed = discord.Embed(
                color=discord.Color.green(),
                title=f"{GIVEAWAY_EMOTE} Giveaway! {GIVEAWAY_EMOTE}",
                description=f"{text} Congratulations!\n"
            )
            embed.add_field(
                name="Prize:",
                value=prize
            )
            if giveaway_id is not None:
                embed.add_field(name="Information for the winners:", value="The prizes will be send to you soon!")
            embed.timestamp = end_date
            embed.set_footer(text="Ended at")
            await message.edit(embed=embed)
            if giveaway_id is not None:
                failed = []
                prizes = self.db.get_prizes(giveaway_id)
                for winner in winners:
                    prize = choice(prizes)
                    try:
                        await winner.send(f"Congrats! Here is your prize: {prize}")
                        prizes.remove(prize)
                    except Exception: failed.append(winner)
                if len(failed) > 0:
                    failed_str = ''.join(e.name + ", " for e in failed)
                    await channel.send(f"I couldn't send the keys to following users: {failed_str[:-2]}.")
                    self.db.update_keys(giveaway_id, prizes)
        except IndexError:
            return await channel.send(content="I couldn't determine a winner.")

    @staticmethod
    async def text_builder(winners: [list, tuple]):
        if len(winners) < 2:
            return f"{winners[0].mention} has won the giveaway!"
        else:
            text = ""
            if winners.count(winners[0]) == len(winners):
                return f"{winners[0].mention} has won every prize in the giveaway"
            checked = []
            for member in winners:
                if member not in checked:
                    checked.append(member)
                    wins = winners.count(member)
                    text += f"{member.mention} has won {wins} {'prizes' if wins > 1 else 'prize'}.\n"
            return text

    @cmd_giveaway.error
    async def error_handler_giveaway(self, ctx, error):
        # error handler
        if isinstance(error, commands.NoPrivateMessage):
            return
        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send("Please make sure that I can add reactions to my messages and embed links.")
        elif isinstance(error, discord.errors.Forbidden):
            return await ctx.send("Please make sure that I can add reactions to my messages and embed links.")
        elif isinstance(error, commands.CheckFailure):
            role = discord.utils.get(ctx.guild.roles, name="Giveaways")
            if role is not None:
                return
            if ctx.author.permissions_in(ctx.channel).manage_roles or \
                    ctx.author.permissions_in(ctx.channel).manage_server:
                await ctx.send("Please create a role called `Giveaways` and give it to everyone who should be able"
                               " to host giveaways.")
            else:
                return

    @giveaway.command(name="reroll")
    @commands.guild_only()
    @commands.has_any_role("Giveaways", "Giveaway", "giveaways", "giveaways")
    @commands.bot_has_permissions(embed_links=True)
    async def reroll_giveaways(self, ctx, message_id=None):
        """Rerolls the giveaway"""
        channel = ctx.channel
        message = None
        # gets the right message
        if message_id is None:
            async for message in channel.history(limit=50):
                if message.author == ctx.me:
                    if len(message.embeds) > 0:
                        message = message
                        break
        else:
            message = await channel.get_message(message_id)
        if message is None:
            return await ctx.send(content="Please specify a valid message id.", delete_after=10)
        reactions = message.reactions
        winner = None
        # goes trough all reactions to find the right one and then randomly chooses a winner
        for reaction in reactions:
            if reaction.emoji == GIVEAWAY_EMOTE:
                winner = choice(await reaction.users().flatten())
        if winner is None:
            return await ctx.send(content="I couldn't determine a winner.", delete_after=10)
        else:
            return await ctx.send(content=f"{GIVEAWAY_EMOTE} {winner.mention} is the new winner! Congratulations!")

    @reroll_giveaways.error
    async def reroll_error(self, ctx, error):
        # error handler
        if isinstance(error, commands.NoPrivateMessage):
            return
        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send("Please make sure that I have the `embed links` permission.", delete_after=15.0)
        elif isinstance(error, commands.CheckFailure):
            role = discord.utils.get(ctx.guild.roles, name="Giveaways")
            if role is not None:
                return
            if ctx.author.permissions_in(ctx.channel).manage_roles or \
                    ctx.author.permissions_in(ctx.channel).manage_server:
                await ctx.send("Please create a role called `Giveaways` and give it to everyone who should be able"
                               " to host and reroll giveaways.", delete_after=15.0)
            else:
                return

    @giveaway.command(name="donate")
    async def donate(self, ctx):
        """A command used to donate keys, nitro, ... for giveaways."""
        # start the donation process
        giveaway_log_channel = self.sdb.get_giveaway_log(ctx.guild.id)
        if not giveaway_log_channel:
            giveaway_log_channel = list(giveaway_log_channel)
        donation_status = self.sdb.get_donation_status(ctx.guild.id)
        if not giveaway_log_channel[0] or giveaway_log_channel[0] is None or not donation_status:
            return await ctx.send("This server doesn't have the donation module enabled.")
        donator = ctx.author
        msg1 = await ctx.send("I will now try to DM you and will then ask you some questions. If you need help  with"
                              " anything please ask a Staff member.\nYou have 30 seconds per question.")
        try:
            await donator.send("The donation process will now start! If you need help with anything please "
                               "ask a staff member.")
        except:
            return await msg1.edit(content="I couldn't message you. Please make sure that I can send you DMs.",
                                   delete_after=15.0)
        await msg1.edit(content="I DMed you you and will now ask you some questions. If you need help  with"
                        " anything please ask a Staff member.")
        # asks what the user questions about the giveaway
        await donator.send("First question: What would you like to donate? Note: This will be used to show as prize.")
        donation_type = await self.question_and_answer(donator)
        if donation_type is None: return
        await donator.send("Second question: How many winners can win this giveaway? Please only input a number here.")
        winners = await self.question_and_answer(donator)
        if winners is None: return
        try: winners = int(winners)
        except ValueError: return await donator.send("Please only input numbers. I have canceled the donation "
                                                     "process.")
        await donator.send("Third question: What would you like to set as text for the giveaway? Note: Links are not"
                           " allowed.")
        giveaway_text = await self.question_and_answer(donator)
        if giveaway_text is None: return
        await donator.send("Okay. I just need one more thing: The prizes. After the giveaway they will automatically "
                           "get send to the winners. They will not be shared with anyone.\nPlease input them with a `|"
                           "` between each prize.")
        prizes = await self.question_and_answer(donator)
        if prizes is None: return
        prizes = prizes.split("|")
        if len(prizes) != winners:
            return await donator.send(f"You have inputted {winners} winners and {len(prizes)} prizes. That won't work."
                                      f" Please input as many prizes as you inputted winners. Please try again."
                                      f" I have canceled the donation process.")
        # send a preview version of the embed
        preview_embed = self.giveaway_embed_preview(donation_type, winners, giveaway_text, donator)

        await donator.send(embed=preview_embed, content="This is a preview version of the giveaway. Is everything right"
                                                        "? If no please reply with `cancel`")

        def check(m):
            # check for all questions
            return m.author == donator and m.guild is None
        try:
            answer = await self.bot.wait_for("message", check=check, timeout=20.0)
            if answer.content.lower() == "cancel":
                return await donator.send("The donation process has been successfully canceled.")
        except asyncio.TimeoutError: await donator.send("I will now finish the donation process!")
        # save the giveaway into the database
        result = self.db.giveaway_donation(donator.id, winners, giveaway_text, prizes, donation_type)
        if not result[0]:
            await donator.send("Something didn't go quite right. Please try again later.")
        # sends the giveaway into the log channel
        giveaway_id = result[1]
        embed = self.giveaway_donation_embed(winners, giveaway_text, donator, donation_type, giveaway_id)
        log_channel = discord.utils.get(ctx.guild.channels, id=giveaway_log_channel[0])
        log_msg = await log_channel.send(embed=embed)
        await log_msg.add_reaction("✅")

    async def question_and_answer(self, donator):
        def check(m):
            # check for all questions
            return m.author == donator and m.guild is None
        try:
            answer = await self.bot.wait_for("message", check=check, timeout=30.0)
            return answer.content
        except asyncio.TimeoutError:
            await donator.send("You only have 30 seconds per message. Please try again.")
            return None

    @staticmethod
    def giveaway_donation_embed(winners, giveaway_text, donator, donation_type, giveaway_id):
        # creates the embed for the giveaway log channel
        embed = discord.Embed(
            color=discord.Color.green(),
            title=f"{donator.name} would like to donate a giveaway"
        )
        embed.add_field(name="Details:", value=f"> {winners} winners\n> Donation type: {donation_type}\n"
                                               f"> Giveaway text: {giveaway_text}")
        embed.set_footer(text=f"Giveaway ID: {giveaway_id}")
        return embed

    @staticmethod
    def giveaway_embed_preview(prize, winners, text, donator):
        # creates an embed preview for the donator
        giveaway_embed = discord.Embed(
            color=discord.Color.blue(),
            title=f"{GIVEAWAY_EMOTE} GIVEAWAY! {GIVEAWAY_EMOTE}",
            description=f"**Prize:** {prize}\n"
                        f"**Possible winners:** {winners} {'member' if winners == 1 else 'members'}\n"
                        f"Click on the {GIVEAWAY_EMOTE} reaction to enter!\n"
        )
        giveaway_embed.set_footer(text="Ends at • <time>")
        if donator is not None: donator = donator.name
        giveaway_embed.add_field(
            name=f"A message by {donator}:",
            value=text
        )
        return giveaway_embed

    async def on_reaction_add(self, reaction, user):
        # checks if the message was in the right channel and if everything is right
        if user.bot:
            return
        message = reaction.message
        giveaway_log = self.sdb.get_giveaway_log(server_id=message.guild.id)
        if not giveaway_log: return
        if message.channel.id != giveaway_log[0]: return
        getter = functools.partial(discord.utils.get, user.roles)
        if any(getter(name=name) is not None for name in ["Admin", "Community Managers"]):
            if len(message.embeds) < 1:
                return
            embed = message.embeds[0]; footer = embed.footer.text
            if footer is None: return
            giveaway_id = re.search(r"Giveaway ID: (?P<id_>\d+)", footer)
            if giveaway_id is None: return
            giveaway_id = int(giveaway_id.groupdict()["id_"])
            # accepts the giveaway in the database (logging reasons)
            self.db.accept_giveaway(user.id, giveaway_id)
            # gets the giveaway details
            gd = self.db.get_giveaway_information(giveaway_id)
            donator = gd[0]; winners = gd[1]; giveaway_text = gd[2]; prize = gd[3]
            gchannel = self.get_channel(self.sdb.get_giveaway_channel(message.guild))
            if gchannel is not None:
                await self.start_giveaway(self.end_time("1d"), prize, gchannel, winners, giveaway_text, donator,
                                          giveaway_id)
            else:
                return print("Something didn't go quite right.")
        else:
            return

    async def start_giveaway(self, end_time, prize, channel, winners, donator_note=None, donator=None, giveaway_id=None):
        # starts a giveaway
        # creates the embed and sends it
        giveaway_embed = discord.Embed(
            color=discord.Color.blue(),
            title=f"{GIVEAWAY_EMOTE} GIVEAWAY! {GIVEAWAY_EMOTE}",
            description=f"**Prize:** {prize}\n"
                        f"**Possible winners:** {winners} {'member' if winners == 1 else 'members'}\n"
                        f"Click on the {GIVEAWAY_EMOTE} reaction to enter!"
        )
        giveaway_embed.timestamp = end_time
        giveaway_embed.set_footer(text="Ends at")
        if donator_note is not None:
            donator = discord.utils.get(channel.guild.members, id=donator)
            if donator is not None: donator = donator.name
            giveaway_embed.add_field(
                name=f"A message by {donator}:",
                value=donator_note
            )
        msg = await channel.send(embed=giveaway_embed)
        await msg.add_reaction(f"{GIVEAWAY_EMOTE}")
        # sets up the scheduler
        scheduler = AsyncIOScheduler()
        scheduler.configure(timezone=end_time.tzname())
        scheduler.add_job(func=self.giveaway_embed, trigger="date", run_date=end_time, args=(prize, channel,
                                                                                             msg.id, winners, end_time,
                                                                                             giveaway_id)
                          )
        scheduler.start()
        return True

    @commands.command(name="prizes")
    @commands.has_permissions(administrator=True)
    async def get_prizes(self, ctx, giveaway_id: int):
        """Get a list of all prizes from a giveaway with a giveaway id"""
        prizes = self.db.get_prizes(giveaway_id)
        if prizes is None:
            return await ctx.send(content="I couldn't find any prizes for this giveaway.", delete_after=15.0)
        msg = await ctx.send("Check your DMs.")
        try:
            return await ctx.author.send(f"Here is a list with all prizes for this giveaway: {prizes}")
        except Exception:
            return await msg.edit(content="Something didn't go quite right. Please make sure that I can send you DMs",
                                  delete_after=15.0)

    def get_channel(self, channel_id):
        return self.bot.get_channel(channel_id)

    @staticmethod
    async def __error(ctx, error):
        # global error handler for this cog
        if isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.CheckFailure):
            return
        elif isinstance(error, commands.BotMissingPermissions):
            return await ctx.send(f"I am missing a permission for this command. {error}")
        if isinstance(error, commands.CommandError):
            return await ctx.send(f"Something didn't go quite right: {error}. Please report this.")


def setup(bot):
    bot.add_cog(Giveaway(bot))
