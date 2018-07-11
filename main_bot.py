import ast
import random
import discord
from discord.ext import commands
import os
import traceback

import bot_settings
from functions.prefix_functions import PrefixFunc

prefix = PrefixFunc()


def get_prefix(bot, message):
    if message.guild is not None:
        server_id = message.guild.id
    else:
        server_id = 0
    author_id = message.author.id
    prefixes = prefix.get_prefix(author_id, server_id)
    return commands.when_mentioned_or(*prefixes)(bot, message)


bot = commands.Bot(command_prefix=get_prefix, description='', case_insensitive=True)


def error_handler(error):
    print("An error occurred:")
    traceback.print_exception(type(error), error, error.__traceback__)
    return False


if __name__ == '__main__':
    modules = []
    try:
        files = os.listdir("./modules")
        for module in files:
            try:
                if module not in ["__init__.py", "__pycache__"] and module.__contains__("cmd_"):
                    bot.load_extension(f"modules.{module.replace('.py', '')}")
            except Exception as e:
                error_handler(e)
    except FileNotFoundError:
        files = os.listdir()
        standard_files = ['bot_settings.py', 'main_bot.py']
        for module in files:
            if ".py" in module and module not in standard_files and module.__contains__("cmd_"):
                try:
                    bot.load_extension(module.replace(".py", ""))
                except Exception as e:
                    error_handler(e)
    except Exception as e:
        error_handler(e)


@bot.event
async def on_ready():
    print(f'\nLogged in as: {bot.user} - {bot.user.id}\nLatency: {round(bot.latency *1000)} ms\n'
          f'Connected to {len(bot.guilds)} guilds\nVersion: {discord.__version__}\n')
    bot_extensions = bot.extensions
    count_extensions = len(bot_extensions)
    if count_extensions < 2:
        extensions = f"Loaded {count_extensions} module: "
    else:
        extensions = f"Loaded {count_extensions} modules: "
    for extension in bot_extensions.keys():
        extensions = extensions + f", {extension}"
    await bot.change_presence(activity=discord.Game(name=random.choice(bot_settings.default_game)),
                              status=discord.Status.online)
    file_name = "message_id.json"
    if os.path.exists(file_name):
        with open(file_name, "r") as read_file:
            content = ast.literal_eval(read_file.read())
        channel = bot.get_channel(int(content.get("channel_id")))
        if channel is None:
            channel = bot.get_user(id=int(content.get("channel_id")))
        message = await channel.get_message(int(content.get("message_id")))
        os.remove(file_name)
        os.remove("restart.bat")
        await message.edit(content="Successfully restarted!")
        return print("Successfully restarted!")
    return print(f'Successfully logged in and booted...!')


bot.run(bot_settings.TOKEN, bot=True, reconnect=True)


