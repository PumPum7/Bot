import discord
from discord.ext import commands
from functions import economy_functions
import asyncio
from bot_settings import daily_time, daily_amount, currency_name
from discord.ext.commands.cooldowns import BucketType
import traceback

DAILY_AMOUNT = daily_amount
DAILY_TIME = daily_time
CURRENCY_NAME = currency_name


class Economy:
    def __init__(self, bot):
        self.bot = bot
        self.db = economy_functions.EconomyFunctions()

    @commands.command(name="daily")
    async def daily_cmd(self, ctx, user: discord.Member=None):
        """Use this command every few hours to get some free credits!"""
        # defines the user if no user was specified
        if user is None:
            user = ctx.author
        # gives the user the money and gets the balance
        result = await self.db.daily_use(user.id)
        balance = await self.db.balance(user.id)
        if result:
            text = f"{user.mention} you recieved {DAILY_AMOUNT} {CURRENCY_NAME}!"
            if user != ctx.author:
                text = f"{ctx.author.mention} has given {DAILY_AMOUNT} {CURRENCY_NAME} to {user.mention}!"
            embed = discord.Embed(
                color=discord.Color.green(),
                description=text
            )
            embed.set_footer(text=f"{user.display_name}'s new balance: {balance} {CURRENCY_NAME}")
            await ctx.send(embed=embed)
        else:
            daily_time = await self.db.daily_time(ctx.message.author.id)
            embed = discord.Embed(
                color=discord.Color.red(),
                title="You can't use this command yet.",
                description=f"Please try again at {daily_time}."
            )
            await ctx.send(embed=embed)

    @commands.command(name="balance", aliases=["$"])
    async def balance_cmd(self, ctx, user: discord.Member=None):
        """Check your or another users balance"""
        # defines the user if user wasn't specified
        if user is None:
            user = ctx.author
        user_name = user.display_name
        balance = await self.db.balance(user.id)
        embed = discord.Embed(
            color=discord.Color.blue(),
            description=f"{user_name}'s balance: {balance} {CURRENCY_NAME}."
        )
        daily_ready = await self.db.daily_check(user.id)
        embed.set_footer(text=f"{user_name}'s daily is ready." if daily_ready else f"{user_name}'s daily "
                                                                                   f"is not ready yet.")
        await ctx.send(embed=embed)

    @commands.command(name="give")
    async def give_cmd(self, ctx, user: discord.Member=None, amount: int=None):
        """Give another user some money. You need to at least give the user 50 credits."""
        if user is None:
            return await ctx.send("You need to supply a user. You can either use the name, ID or mention.")
        if amount is None or amount < 50:
            return await ctx.send(f"You need to supply the amount you want to give to {user.display_name}. "
                                  f"This has to be over 50 {CURRENCY_NAME}.")
        if await self.db.give_credits(ctx.message.author.id, user.id, amount):
            giver_balance = await self.db.balance(ctx.message.author.id)
            reciever_balance = await self.db.balance(user.id)
            embed = discord.Embed(
                color=discord.Color.green(),
                title=f"Successfully transferred {amount} {CURRENCY_NAME}!",
                description=f"{ctx.author.display_name}'s new balance: {giver_balance} {CURRENCY_NAME}\n"
                            f"{user.display_name}'s new balance: {reciever_balance}"
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                color=discord.Color.red(),
                title="An error occurred!",
                description="Please make sure that you have enough money to transfer."
            )
            await ctx.send(embed=embed)

    @commands.command(name="wheel")
    @commands.cooldown(1, 5, BucketType.user)
    async def wheel_cmd(self, ctx, amount=None):
        """Spin the wheel. Either loose 90% of your bet or win 240%!"""
        if not amount:
            return await ctx.send(f"Please follow the format: `{ctx.prefix}{ctx.command} {'bet amount'}`")
        try:
            amount = int(amount)
        except ValueError:
            if amount == "all":
                amount = await self.db.balance(ctx.author.id)
            else:
                return await ctx.send(f"Please follow the format: `{ctx.prefix}{ctx.command} {'bet amount'}`")
        if amount < 20:
            return await ctx.send(f"You have to at least bet 20 {currency_name}.")
        wheels = []
        multiplier = 1
        for i in range(3):
            wheel = await self.db.wheel_builder()
            wheels.append(wheel[1])
            multiplier = wheel[0]
        cnt = 0
        msg = None
        for i in wheels:
            await asyncio.sleep(0.5)
            cnt += 1
            embed = discord.Embed(
                color=discord.Color.blue(),
                title=f"The wheel is spinning!" if cnt <= 2 else f"Result:",
                description=i
            )
            if cnt > 2:
                win = round((amount * multiplier) - amount)
                print(win)
                balance = await self.db.add_credits(ctx.author.id, win)
                embed.set_footer(text=f"New balance: {balance} {CURRENCY_NAME}")
            if msg is None:
                msg = await ctx.send(embed=embed)
            else:
                await msg.edit(embed=embed)

    @wheel_cmd.error
    async def error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            print(ctx.kwargs)

    async def __error(self, ctx, error):
        if isinstance(error, IndexError):
            return await ctx.send("An error occurred! Please make sure that you followed the format.", delete_after=10)
        elif isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.NoPrivateMessage):
            return await ctx.send("You can't use this command here.")
        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(error)
        elif isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(error)
        elif isinstance(error, commands.CommandError):
            self.error_handler(error)
            return await ctx.send(content="Something didn't go quite right. The error has been reported!",
                                  delete_after=15.0)

    @staticmethod
    def error_handler(error):
        print("An error occurred:")
        traceback.print_exception(type(error), error, error.__traceback__)
        return False


def setup(bot):
    bot.add_cog(Economy(bot))
