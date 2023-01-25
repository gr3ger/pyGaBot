import asyncio
import logging
import sys

import discord
import googleapiclient.discovery
import googleapiclient.errors
from dateutil.parser import parse
from discord.ext import commands

import settings


class YoutubeCog(commands.Cog, name="Youtube"):
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

    def __init__(self, bot):
        self.bot = bot
        self.task = None
        self.yt = googleapiclient.discovery.build("youtube", "v3", developerKey=settings.GOOGLE_API_KEY)

        if self.task is None and settings.read_option(settings.KEY_YOUTUBE_INTEGRATION, "False") == "True":
            self.task = asyncio.create_task(self.poll_thread())

    @commands.command()
    @commands.has_any_role("Mods", "Admin")
    async def disableyoutube(self, ctx):
        """Stop sending youtube updates"""
        self.task.cancel()
        self.task = None
        settings.write_option(settings.KEY_YOUTUBE_INTEGRATION, "False")
        await ctx.send("Youtube integration disabled")

    @commands.command()
    @commands.has_any_role("Mods", "Admin")
    async def enableyoutube(self, ctx, username):
        """Send youtube updates to this channel"""
        print(str(ctx.message.channel.id))
        if isinstance(ctx.message.channel, discord.TextChannel):
            user_json = self.get_youtube_user_by_name(username)

            if isinstance(user_json, Exception):
                await ctx.send("*Error: {}*".format(str(user_json)))
                return
            print(user_json)

            try:
                print("Found {} with userid {}".format(user_json["items"][0]["snippet"]["title"],
                                                       user_json["items"][0]["id"]))
                settings.write_option(settings.KEY_YOUTUBE_CHANNEL_ID, user_json["items"][0]["id"])
                settings.write_option(settings.KEY_ANNOUNCEMENT_CHANNEL_YOUTUBE, str(ctx.message.channel.id))
                settings.write_option(settings.KEY_YOUTUBE_INTEGRATION, "True")
                await ctx.send(
                    "Successfully set the announcement channel to: {}, I will post here when {} posts a video.".format(
                        ctx.message.channel.name, username))

                if self.task is None:
                    self.task = asyncio.create_task(self.poll_thread())
            except Exception as e:
                await ctx.send(str(e))
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
        while True:
            try:
                response = self.yt.activities().list(part="snippet,contentDetails",
                                                     channelId=settings.read_option(settings.KEY_YOUTUBE_CHANNEL_ID),
                                                     maxResults=5).execute()
                if settings.read_option(settings.KEY_YOUTUBE_LAST_UPDATE, default="NULL") == "NULL":
                    settings.write_option(settings.KEY_YOUTUBE_LAST_UPDATE,
                                          response["items"][0]["snippet"]["publishedAt"])
                else:
                    prev = parse(settings.read_option(settings.KEY_YOUTUBE_LAST_UPDATE))
                    for x in response["items"]:
                        upload = parse(x["snippet"]["publishedAt"])
                        if upload > prev and "upload" in x["contentDetails"]:
                            final_url = "https://www.youtube.com/watch?v={}".format(
                                x["contentDetails"]["upload"]["videoId"])
                            await self.send_message_to_channel(
                                settings.YOUTUBE_ANNOUNCEMENT_MESSAGE.format(title=x["snippet"]["title"],
                                                                             url=final_url),
                                int(settings.read_option(settings.KEY_ANNOUNCEMENT_CHANNEL_YOUTUBE, 0)))
                    settings.write_option(settings.KEY_YOUTUBE_LAST_UPDATE,
                                          response["items"][0]["snippet"]["publishedAt"])
            except Exception as e:
                logging.exception(e)
            await asyncio.sleep(settings.YOUTUBE_POLL_RATE)

    async def send_message_to_channel(self, string, channel_id: int):
        print("sending: {}".format(string))
        print("Sending announcement to channel {}".format(channel_id))
        channel = self.bot.get_channel(channel_id)
        await channel.send(string)
