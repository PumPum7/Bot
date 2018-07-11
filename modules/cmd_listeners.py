from functions import database
import discord
from discord.ext import commands


class Listeners:
    def __init__(self, bot):
        self.bot = bot
        self.db = database.ServerDatabase()

    async def on_member_join(self, member):
        guild = member.guild
        join_log = self.db.get_join_log(guild.id)[0]
        bot_role = self.db.get_bot_role(guild.id)[0]
        if join_log is not None:
            channel = discord.utils.get(guild.channels, id=join_log)
            if channel.permissions_for(guild.me).send_messages:
                join_msg = self.db.get_join_msg(guild.id)[0]
                if join_msg is not None:
                    member_count = str(guild.member_count)
                    message = join_msg.replace("%USER%", member.mention).replace("%SERVER%",
                                                                                 guild.name).replace("%MEMBERCOUNT%",
                                                                                                     member_count)
                    await channel.send(message)
        if bot_role is not None and member.bot:
            role = discord.utils.get(guild.roles, id=bot_role)
            try:
                await member.add_roles(role, reason="Bot role")
            except commands.BotMissingPermissions:
                return
            except Exception as e:
                print("Something didn't go quite right:", e)

    async def on_member_remove(self, member):
        guild = member.guild
        leave_log = self.db.get_join_log(guild.id)[0]
        if leave_log is None:
            return
        channel = discord.utils.get(guild.channels, id=leave_log)
        if not channel.permissions_for(guild.me).send_messages:
            return
        leave_msg = self.db.get_leave_msg(guild.id)[0]
        if leave_msg is None:
            return
        member_count = str(guild.member_count)
        message = leave_msg.replace("%USER%", member.mention).replace("%SERVER%", guild.name).replace("%MEMBERCOUNT%",
                                                                                                      member_count
                                                                                                      )
        return await channel.send(message)


def setup(bot):
    bot.add_cog(Listeners(bot))
