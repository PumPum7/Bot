import discord
import aiohttp
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from bot_settings import weather_unit, openweathermap_key
from datetime import datetime
from functions import color_functions
import textwrap
from PIL import ImageFont, ImageDraw, Image
from io import BytesIO
from random import sample
import aiogoogletrans
from functions.database import Database
import re


URL = "http://api.openweathermap.org/data/2.5/find"


class Utility:
    def __init__(self, bot):
        self.bot = bot
        self.color = color_functions.Colors()
        self.translator = aiogoogletrans.Translator()
        db = Database()
        self.error_handler = db.error_handler

    @staticmethod
    async def request(url, data=None, params=None):
        valid_responses = [200, 201, 202]
        async with aiohttp.ClientSession() as session:
            async with session.get(url, data=data, params=params) as response:
                if response.status in valid_responses:
                    return await response.json()
                return None

    @staticmethod
    async def post(url, data=None, headers=None):
        valid_responses = [200, 201, 202]
        async with aiohttp.ClientSession() as session:
            async with session.post(url=url, data=data, headers=headers) as response:
                if response.status in valid_responses:
                    return await response.json()
                else:
                    return None

    @commands.command(name="weather")
    @commands.cooldown(1, 10.0, type=BucketType.user)
    async def cmd_weather(self, ctx, *, city=None):
        """Get weather information about a city."""
        if city is None:
            return await ctx.send("Please specify a city.")
        # makes the request
        result = await self.request(url=f"{URL}?q={city}&units={weather_unit}&appid={openweathermap_key}")
        # checks if the request status was 200
        if result is not None:
            # specifies all things
            tmp_item = result["list"][0]
            coord = tmp_item["coord"]
            weather_item = tmp_item["weather"][0]
            main_item = tmp_item["main"]
            coord = [coord["lat"], coord["lon"]]
            temp = main_item["temp"]
            temp_range = [main_item["temp_min"], main_item["temp_max"]]
            wind = tmp_item["wind"]["speed"]
            weather_description = [weather_item["main"], weather_item["description"]]
            icon = weather_item["icon"]
            city = tmp_item["name"]
            embed = discord.Embed(
                color=discord.Color.blue(),
                description=f"Weather description for {city}: {weather_description[1]}",
                title=f"Weather information for {city}"
            )
            embed.add_field(
                name="Temperature:",
                value=f"Current temperature: {temp}\nMaximal temperature: {temp_range[1]}\nMinimal temperature:"
                      f" {temp_range[0]}",
                inline=False
            )
            embed.set_author(icon_url=f"http://openweathermap.org/img/w/{icon}.png", name=weather_description[0])
            embed.add_field(
                name=f"Coordinates:",
                value=f"> Latitude: {coord[0]}\n> Longitude: {coord[1]}",
                inline=False
            )
            embed.add_field(name="Wind:", value=wind)
            embed.add_field(
                name="Disclaimer:",
                value="This command was made possible with the OpenWeatherMap.org API."
            )
            embed.set_footer(text=f"All units are {weather_unit}.")
            return await ctx.send(embed=embed)
        return await ctx.send("Something didn't go quite right. Sorry.")

    @commands.command(name="ping")
    async def ping_cmd(self, ctx):
        """Pong!"""
        msg = await ctx.send("Pong!")
        await msg.edit(content=f"Pong... Time taken: {round(self.bot.latency*1000)} ms!")

    @commands.command(name="avatar", aliases=["uavatar"])
    async def avatar_cmd(self, ctx, user: discord.Member=None):
        """Returns the avatar of you or a specified member."""
        async with ctx.typing():
            if user is None:
                user = ctx.author
            avatar_url = user.avatar_url_as(static_format="png").replace("?size=1024", "").replace("&_=.gif", "")
            static_avatar_url = user.avatar_url_as(format="png")
            embed_color = await self.color.compute_average_image_color(static_avatar_url)
            rgb = embed_color.get("colors")
            embed_color = discord.Color.from_rgb(rgb["red"], rgb["green"], rgb["blue"])
            embed = discord.Embed(
                color=embed_color,
                description=f"[Avatar url]({avatar_url})",
                title=f"Here is {user.name}'s avatar:"
            )
            embed.set_image(url=avatar_url)
            await ctx.send(embed=embed)

    @avatar_cmd.error
    async def avatar_user_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Please specify a valid user.")

    @commands.command(name="botinvite")
    async def botinvite_cmd(self, ctx):
        """Use this command if you would like to invite me to your server."""
        bot_invite = discord.utils.oauth_url(ctx.me.id)
        await ctx.send(f"You can invite me using this link: <{bot_invite}>")

    @commands.command(name="serverinfo")
    async def global_serverinfo_cmd(self, ctx, invitelink: str=None):
        """Get information about this server or a specified server (works with invite links)"""
        if invitelink is not None:
            try:
                invite = await self.bot.get_invite(invitelink)
                guild = invite.guild
                await ctx.send(embed=await self.serverinfo_embed(guild, guild_type="invite"))
            except Exception:
                guild = ctx.guild
                await ctx.send(embed=await self.serverinfo_embed(guild))
        else:
            guild = ctx.guild
            await ctx.send(embed=await self.serverinfo_embed(guild))

    async def serverinfo_embed(self, guild: discord.Guild, guild_type="standard"):
        if guild_type is "standard":
            name = guild.name
            membercount = guild.member_count
            guild_icon = guild.icon_url_as(format="png")
            owner = guild.owner
            guild_id = guild.id
            mfa_level = {0: "disabled", 1: "enabled"}.get(guild.mfa_level)
            verification_level = {discord.VerificationLevel.none: "No criteria set.",
                                  discord.VerificationLevel.low: "Members must have a verified email on their Discord "
                                                                 "account.",
                                  discord.VerificationLevel.medium: "Members must have a verified email and be registered "
                                                                    "on Discord for more than five minutes.",
                                  discord.VerificationLevel.high: "Members must have a verified email, be registered on "
                                                                  "Discord for more than five minutes, and be a member of "
                                                                  "the guild itself for more than ten minutes.",
                                  discord.VerificationLevel.extreme: "Members must have a verified phone on their Discord "
                                                                     "account."
                                  }.get(guild.verification_level)
            explicit_content_filter = {discord.ContentFilter.disabled: "This guild does not have the content "
                                                                       "filter enabled.",
                                       discord.ContentFilter.no_role: "This guild has the content filter enabled "
                                                                      "for members without a role.",
                                       discord.ContentFilter.all_members: "This guild has the content filter enabled "
                                                                          "for every member."
                                       }.get(guild.explicit_content_filter)
            special_features = guild.features
            splash = guild.splash_url
            role_count = len(guild.roles)
            voice_channel_count = len(guild.voice_channels)
            text_channel_count = len(guild.text_channels)
            category_count = len(guild.categories)
            creation_date = f"{str(guild.created_at).split('.', 1)[0]} UTC"
            server_region = guild.region
            guild_icon_main_color = await self.color.compute_average_image_color(guild_icon)
            rgb_format = guild_icon_main_color.get("colors")
            hex_format = guild_icon_main_color.get("hex")
            embed = discord.Embed(
                color=discord.Color.from_rgb(rgb_format.get("red"), rgb_format.get("green"), rgb_format.get("blue")),
                description=f"ID: {guild_id}"
            )
            embed.add_field(
                name="General information:",
                value=f"> Creation date: {creation_date}\n> Channel category count: {category_count}\n> Text channel "
                      f"count: {text_channel_count}\n> Voice channel count: {voice_channel_count}\n"
                      f"> Role count: {role_count}\n> Member count: {membercount}\n> Owner ID: {owner.id}\n"
                      f"> Server region: {server_region}\n> Avarage color of the guilds icon: {hex_format}"
            )
            if len(special_features) > 0:
                special_features_ = ""
                for item in special_features:
                    if item == "INVITE_SPLASH":
                        special_features += f"> {item}(<{splash}>), "
                    else:
                        special_features += f"> {item}, "
                embed.add_field(
                    name="Special features:",
                    value=f"{special_features_}"
                )
            embed.set_author(
                name=name,
                icon_url=guild_icon
            )
            embed.set_thumbnail(url=guild_icon)
            embed.add_field(
                name="Security settings:",
                value=f"> Verification level: {verification_level}\n"
                      f"> Explicit Content filter: {explicit_content_filter}\n"
                      f"> Two factor authorisation is {mfa_level}",
            )
        else:
            embed = discord.Embed(
                color=discord.Color.dark_blue(),
                description=f"General information:\n"
                            f"> ID: {guild.id}\n> Creation date: {str(guild.created_at).split('.', 1)[0]} UTC"
            )
            embed.set_author(name=guild.name)
            embed.set_footer(text="This is a minimised but global version of the serverinfo command.")
        return embed

    @cmd_weather.error
    async def cmd_weather_error(self, ctx, error):
        if str(error).__contains__("You are on cooldown. Try again in"):
            await ctx.send(error)
        elif isinstance(error, commands.CommandError):
            print(f"Command: {ctx.command}\nError: {error}")

    @commands.command(name="userinfo", aliases=["ui", "whois", "user"])
    async def cmd_userinfo(self, ctx, *, user_arg: str=None):
        """Get informations about you or another user"""
        if user_arg is not None:
            user_ = re.search(r"<(@!|@)(?P<user_mention>\d+)>|(?P<user_id>\d+)", user_arg)
            if user_ is not None:
                usr = user_.groupdict()["user_id"]
                user_ = int(usr) if usr is not None else int(user_.groupdict()["user_mention"])
                user = ctx.guild.get_member(user_id=user_)
                if user is not None:
                    return await ctx.send(embed=await self.userinfo_embed_creator(user, global_=False))
                else:
                    user = await self.bot.get_user_info(user_id=user_)
                if user is None:
                    return await ctx.send("Please make sure that this is a valid user.")
                return await ctx.send(embed=await self.userinfo_embed_creator(user, global_=True))
            else:
                user = discord.utils.get(ctx.guild.members, name=user_arg)
                if user is not None:
                    await ctx.send(embed=await self.userinfo_embed_creator(user, global_=False))
                else:
                    await ctx.send(f"I couldn't find a user named {user_arg}.")
        else:
            user = ctx.author
            await ctx.send(embed=await self.userinfo_embed_creator(user, global_=False))

    async def userinfo_embed_creator(self, user, global_=False):
        # creates the embed for the userinfo command
        static_avatar = user.avatar_url_as(format="png")
        user_avatar = user.avatar_url_as(static_format="png")
        embed_color = await self.color.compute_average_image_color(static_avatar)
        if embed_color is not None:
            rgb = embed_color.get("colors")
            embed_color = discord.Color.from_rgb(rgb["red"], rgb["green"], rgb["blue"])
        else:
            embed_color = discord.Color.dark_blue()
        user_name = user.name; user_id = user.id; user_discrim = user.discriminator
        user_age = (datetime.utcnow() - user.created_at).days
        user_default_avatar = user.default_avatar
        user_default_avatar_url = user.default_avatar_url
        user_has_nitro = user.is_avatar_animated()
        if user_has_nitro:
            user_has_nitro = "This user has nitro perks."
        else:
            user_has_nitro = "This user either has no nitro perks or doesn't use an animated profile picture."
        user_is_bot = "This is a bot account" if user.bot else "This is a user account."
        embed = discord.Embed(
            color=embed_color,
            title=user_name + "#" + user_discrim,
            description=f"User ID: {user_id}"
        )
        embed.add_field(
            name="Global information:",
            value=f"> {user_has_nitro}\n> This user was created {user_age} days ago.\n> [{user_default_avatar} default "
                  f"avatar]({user_default_avatar_url})\n> {user_is_bot}",
            inline=False
        )
        embed.set_thumbnail(
            url=user_avatar
        )
        if not global_:
            user_roles = user.roles
            user_join_date = (datetime.utcnow() - user.joined_at).days
            user_nick = user.nick
            user_voice = user.voice
            user_status = user.status
            user_activity = user.activity
            user_activity = self.activity_handler(user_activity)
            if user_activity is not None:
                embed.add_field(
                    name="User activity:",
                    value=user_activity,
                    inline=False
                )
            text = f"> {len(user_roles)} roles\n> Joined {user_join_date} days ago\n> Status: {user_status}"
            if user_nick is not None:
                text += f"\n> Nickname: {user_nick}"
            embed.add_field(
                name="More details:",
                value=text,
                inline=False
            )
            if user_voice is not None:
                if user_voice.self_deaf or user_voice.deaf:
                    deaf = True
                else:
                    deaf = False
                if user_voice.self_mute or user_voice.mute:
                    mute = True
                else:
                    mute = False
                user_deaf = {True: "", False: "not "}.get(deaf, "not ")
                user_mute = {True: "", False: "not "}.get(mute, "not ")
                embed.add_field(
                    name="Voice information:",
                    value=f"This user is {user_deaf}deafened, {user_mute}muted and is connected to "
                          f"{user_voice.channel.mention}",
                    inline=False
                )
        return embed

    @staticmethod
    def activity_handler(activity):
        # sets the message for each activity type
        if activity is None:
            return None
        if str(activity) == "Spotify":
            song_title = activity.title; song_artists = activity.artists; song_album = activity.album
            song_album_url = activity.album_cover_url; song_url = f"https://open.spotify.com/track/{activity.track_id}"
            song_duration = activity.duration; start_time = activity.start
            time_dif = datetime.utcnow() - start_time
            time_dif = str(time_dif)[2:].split(".", 1)[0]
            playing_time = str(song_duration)[2:].split(".", 1)[0]
            if len(song_artists) == 1:
                song_artists_text = f"Artist: {song_artists[0]}, "
            else:
                song_artists_text = "Artists: "
                for artist in song_artists:
                    song_artists_text += f"{artist}, "
            text = f"> Song title: [{song_title}]({song_url})\n> Album: [{song_album}]({song_album_url})\n" \
                   f"> {song_artists_text[:-2]}\n> Song duration: {time_dif} / {playing_time}"
            return text
        elif activity.type == discord.ActivityType.playing:
            activity_name = activity.name
            return f"> Playing {activity_name}"
        elif activity.type == discord.ActivityType.streaming:
            stream_name = activity.name; stream_url = activity.url; stream_streamer_name = activity.twitch_name
            stream_game = activity.details
            text = f"> Stream name: [{stream_name}]({stream_url})"
            if stream_streamer_name is not None:
                text += f"\n> Streamer: {stream_streamer_name}"
            if stream_game is not None:
                text += f"\n> Streaming {stream_game}"
            return text

    @commands.command(name="message", aliases=["msg", "getmsg"], hiddden=True)
    async def message_cmd(self, ctx, *, content="nothing"):
        """Create a message as picture, more or less only testing"""
        # creates the texts
        user = ctx.message.author
        color = user.color
        text = ctx.message.clean_content.replace(f"{ctx.prefix}{ctx.command}", "")
        # makes the text right
        text = textwrap.fill(text, width=60) if len(text) >= 60 else text
        y_cord = 30 + (len(text.split("\n")) * 20)
        # makes the timestamp
        timestamp = str(ctx.message.created_at).split(" ", 1)[1]
        timestamp = timestamp.split(".", 1)[0]
        # creates a new image
        img = Image.new("RGB", size=(507, y_cord), color=(53, 57, 62))
        draw = ImageDraw.Draw(img)
        # writes the nickname
        nick_font = ImageFont.truetype("./data/fonts/nick-font.otf", 16)
        draw.text((10, 0), user.display_name, color.to_rgb(), font=nick_font)
        # gets the timestamp coordinates
        text_xy = draw.textsize(user.display_name, nick_font)
        timestamp_xy = (text_xy[0] + 14, text_xy[1] - 14)
        # writes the timestamp
        time_font = ImageFont.truetype("./data/fonts/OpenSans-Regular.ttf", 12)
        draw.text(timestamp_xy, f"Today at {timestamp[:-3]}", (91, 94, 98), font=time_font)
        # loads the fonts for the text
        bold_font = ImageFont.truetype("./data/fonts/bold-font.woff", 16)
        text_font = ImageFont.truetype("./data/fonts/msg-font.woff", 16)
        # testing out things
        """
        text_ = text.split("\n")
        for part in text:
            re.findall("[** **]")
        """
        draw.multiline_text((10, 20), text, font=text_font, spacing=2, align="left")
        bytes_ = BytesIO()
        img.save(bytes_, format="png")
        bytes_.seek(0)
        image = discord.File(filename=f"test.png", fp=bytes_)
        await ctx.send(file=image)

    @commands.cooldown(1, 5, commands.BucketType.channel)
    @commands.command(aliases=["translate_mixup", "googletrans"])
    async def translate(self, ctx, *, text):
        """Translates text to 10 random languages then back to English."""
        msg = await ctx.send("I will now translate it.")
        text = text[:900]
        langs = []
        prevlang = (await self.translator.translate(text)).src
        if "zh" in prevlang:
            prevlang = "en"
        for language in sample(list(aiogoogletrans.LANGUAGES), 10):
            if len(language) > 2:
                continue
            text = (await self.translator.translate(text, dest=language, src=prevlang)).text
            langs.append(language)
            prevlang = language
        result = await self.translator.translate(text, dest="en")
        if len(result.text) > 1900:
            result.text = await ctx.upload(result.text)
        else:
            result.text = "```" + result.text + "```"
        await msg.edit(content="**User**: {}\n**Languages**:\n```{}```\n**End result**\n"
                       "{}".format(ctx.author, "\n".join([aiogoogletrans.LANGUAGES[l] for l in langs]), result.text))

    async def __error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send(f"Please make sure you supplied the right arguments. For more information please use the "
                           f"command {ctx.prefix}help {ctx.command}")
            return
        elif isinstance(error, commands.BotMissingPermissions):
            return
        elif isinstance(error, commands.MissingPermissions):
            return
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(error)
            return
        elif isinstance(error, ValueError):
            await ctx.send(f"Please make sure you supplied the right arguments. For more information please use the "
                           f"command {ctx.prefix}help {ctx.command}")
            return
        elif isinstance(error, commands.CommandError):
            self.error_handler(error)
            await ctx.send("Something didn't go quite right.")



def setup(bot):
    bot.add_cog(Utility(bot))
