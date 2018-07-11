import datetime

from functions.database import Database
from bot_settings import daily_time, daily_amount
from random import choice


class EconomyFunctions:
    def __init__(self):
        self.db = Database()

    async def daily_use(self, user_id):
        current_balance = await self.balance(user_id)
        if current_balance is None:
            current_balance = 0
        if await self.daily_check(user_id):
            self.db.set_value("balance", current_balance + daily_amount, user_id)
            self.db.set_value("daily_time", str(datetime.datetime.utcnow()), user_id)
            return True
        else:
            return False

    async def balance(self, user_id):
        balance = self.db.get_value("balance", user_id)
        if balance is None:
            balance = 0
        return balance[0]

    async def daily_check(self, user_id):
        now_time = datetime.datetime.utcnow()
        old_time = self.db.get_value("daily_time", user_id)
        if old_time is None:
            return True
        if old_time[0] is None:
            return True
        old_time = old_time[0]
        old_time = datetime.datetime.strptime(old_time, "%Y-%m-%d %H:%M:%S.%f")
        if (old_time + datetime.timedelta(hours=daily_time)) <= now_time:
            return True
        else:
            return False

    async def daily_time(self, user_id):
        old_time = self.db.get_value("daily_time", user_id)[0]
        if old_time is None:
            return None
        old_time = datetime.datetime.strptime(old_time, "%Y-%m-%d %H:%M:%S.%f")
        daily_time_ = old_time + datetime.timedelta(hours=daily_time)
        return str(daily_time_).split(".", 1)[0]

    async def give_credits(self, giver_id, reciever_id, amount):
        giver_balance = await self.balance(giver_id)
        reciever_balance = await self.balance(reciever_id)
        if giver_balance < amount:
            return False
        self.db.set_value("balance", giver_balance - amount, giver_id)
        self.db.set_value("balance", reciever_balance + amount, reciever_id)
        return True

    async def set_credits(self, user_id, amount):
        balance = await self.balance(user_id)
        if balance < amount:
            return False
        self.db.set_value("balance", balance - amount, user_id)
        return True

    async def add_credits(self, user_id, amount):
        balance = await self.balance(user_id)
        self.db.set_value("balance", balance + amount, user_id)
        return await self.balance(user_id)

    @staticmethod
    async def wheel_builder():
        emotes_ = {
            1.5: "⬆",
            2.4: "↖",
            1.7: "⬅",
            0.2: "↙",
            0.1: "⬇",
            1.2: "↘",
            0.5: "➡",
            0.3: "↗"
        }
        multiplier, emote = choice(list(emotes_.items()))
        wheel = "**2.4**       **1.5**        **0.3**\n\n" \
                f"**1.7**       {emote}      **0.5**\n\n" \
                "**0.2**      **0.1**        **1.2**"
        return multiplier, wheel


