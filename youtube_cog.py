import asyncio
import sys

import discord
import googleapiclient.discovery
import googleapiclient.errors
from dateutil.parser import parse
from discord.ext import commands

import settings
from models import YoutubeSettings


class YoutubeCog(commands.Cog, name="Youtube"):
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

    def __init__(self, bot):
        self.bot = bot
        self.task = None
        self.yt = googleapiclient.discovery.build("youtube", "v3", developerKey=settings.GOOGLE_API_KEY)
        self.task = asyncio.create_task(self.poll_thread())

    @commands.command()
    @commands.has_any_role("Mods", "Admin")
    async def disableyoutube(self, ctx):
        """Stop sending youtube updates"""
        current_sub = YoutubeSettings.get(guild_id=ctx.guild.id)
        if current_sub is not None:
            current_sub.delete_instance()
            await ctx.send("Youtube integration disabled")
        else:
            await ctx.send("You currently don't have any Youtube integrations")

    @commands.command()
    @commands.has_any_role("Mods", "Admin")
    async def enableyoutube(self, ctx, username):
        """Send youtube updates to this channel"""
        print(str(ctx.message.channel.id))

        yt_settings, _ = YoutubeSettings.get_or_create(guild_id=ctx.guild.id)

        if isinstance(ctx.message.channel, discord.TextChannel):
            user_json = self.get_youtube_user_by_name(username)

            if isinstance(user_json, Exception):
                await ctx.send("*Error: {}*".format(str(user_json)))
                return
            print(user_json)

            try:
                print("Found {} with userid {}".format(user_json["items"][0]["snippet"]["title"],
                                                       user_json["items"][0]["id"]))
                yt_settings.youtube_channel = str(user_json["items"][0]["id"])
                yt_settings.announcement_channel = str(ctx.message.channel.id)
                yt_settings.save()
                await ctx.send(
                    "Successfully set the announcement channel to: {}, I will post here when {} posts a video.".format(
                        ctx.message.channel.name, username))
            except Exception as e:
                await ctx.send("Something went wrong, contact the developer with this error: " + e)
        else:
            await ctx.send("Needs to be done in a regular channel")
            return

    @enableyoutube.error
    async def enableyoutube_error(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send('Usage: `{}enableyoutube <youtube_channel_name>` '
                           '\nIt must be used in a regular channel so it knows where to post announcements.'
                           .format(settings.CALL_CHARACTER))

    def get_youtube_user_by_name(self, username):
        try:
            response = self.yt.channels().list(part="snippet", forUsername=username).execute()
            return response
        except Exception as e:
            print(e, file=sys.stderr)
            return e

    async def poll_thread(self):
        # Current Google API quota is 10k requests per day, for one user it's about 150 in one day
        while True:
            try:
                for yt_item in YoutubeSettings.select():
                    response = self.yt.activities().list(part="snippet,contentDetails",
                                                         channelId=yt_item.youtube_channel,
                                                         maxResults=5).execute()
                    prev = yt_item.last_update
                    for x in response["items"]:
                        upload = parse(x["snippet"]["publishedAt"]).replace(tzinfo=None)
                        if upload > prev:
                            final_url = "https://www.youtube.com/watch?v={}".format(
                                x["contentDetails"]["upload"]["videoId"])
                            await self.send_message_to_channel(
                                yt_item.announcement_template.format(title=x["snippet"]["title"],
                                                                     url=final_url),
                                int(yt_item.announcement_channel))
                    yt_item.last_update = parse(response["items"][0]["snippet"]["publishedAt"]).replace(tzinfo=None)
                    yt_item.save()
            except Exception as e:
                print(e)
            await asyncio.sleep(settings.YOUTUBE_POLL_RATE)

    async def send_message_to_channel(self, string, channel_id: int):
        print("sending: {}".format(string))
        print("Sending announcement to channel {}".format(channel_id))
        channel = self.bot.get_channel(channel_id)
        await channel.send(string)
