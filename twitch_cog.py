import asyncio
import http
import json
import sys
from http.client import HTTPSConnection

import discord
from discord.ext import commands

import settings


class TwitchCog(commands.Cog, name="Twitch"):
    def __init__(self, bot):
        self.bot = bot
        self.task = None

        if self.task is None and settings.read_option(settings.KEY_TWITCH_INTEGRATION, "False") == "True":
            self.task = asyncio.create_task(self.poll_thread())

    def get_twitch_user_by_name(self, usernames):
        try:
            if isinstance(usernames, list):
                usernames = ['login={0}'.format(i) for i in usernames]
                req = '/helix/users?' + '&'.join(usernames)
            else:
                req = '/helix/users?login=' + usernames

            print(req)

            connection = http.client.HTTPSConnection('api.twitch.tv', timeout=10)
            connection.request('GET', req, None, headers={
                'Authorization': "Bearer " + settings.read_option(settings.KEY_TWITCH_ACCESS_TOKEN, ""),
                'client-id': settings.TWITCH_CLIENT_ID})
            response = connection.getresponse()

            print("Twitch: {}: {} {}".format(req, response.status, response.reason))
            if response.status == 401:
                self.get_access_token()
                return self.get_twitch_user_by_name(usernames)
            re = response.read().decode()
            j = json.loads(re)
            return j
        except Exception as e:
            print(e, file=sys.stderr)
            return e

    def get_access_token(self):
        try:
            print("Twitch: Attempting to get access token")
            connect_string = "/oauth2/token?client_id={client_id}" \
                             "&client_secret={client_secret}" \
                             "&grant_type=client_credentials".format(client_id=settings.TWITCH_CLIENT_ID,
                                                                     client_secret=settings.TWITCH_CLIENT_SECRET)
            auth_connection = http.client.HTTPSConnection('id.twitch.tv', timeout=10)
            auth_connection.request('POST', connect_string, None)
            response = auth_connection.getresponse()
            print("Twitch: {}: {} {}".format(connect_string, response.status, response.reason))
            re = response.read().decode()
            j = json.loads(re)
            print(j)
            settings.write_option(settings.KEY_TWITCH_ACCESS_TOKEN, j["access_token"])
            return j
        except Exception as e:
            print(e, file=sys.stderr)
            return e

    def get_streams(self, usernames):
        try:
            if isinstance(usernames, list):
                usernames = ['user_login={0}'.format(i) for i in usernames]
                req = '/helix/streams?' + '&'.join(usernames)
            else:
                req = '/helix/streams?user_login=' + usernames

            connection = http.client.HTTPSConnection('api.twitch.tv', timeout=10)
            connection.request('GET', req, None, headers={
                'Authorization': "Bearer " + settings.read_option(settings.KEY_TWITCH_ACCESS_TOKEN, ""),
                'client-id': settings.TWITCH_CLIENT_ID
            })
            response = connection.getresponse()
            print("Twitch: {}: {} {}".format(req, response.status, response.reason))

            if response.status == 401:
                self.get_access_token()
                return self.get_streams(usernames)

            re = response.read().decode()
            j = json.loads(re)
            return j
        except Exception as e:
            print(e, file=sys.stderr)
            return e

    async def poll_thread(self):
        was_previously_online = False
        while True:
            notification_sent = False
            try:
                result_json = self.get_streams(settings.read_option(settings.KEY_TWITCH_CHANNEL, ""))
                is_online = False
                for stream in result_json["data"]:
                    if stream["user_name"] == settings.read_option(settings.KEY_TWITCH_CHANNEL, ""):
                        is_online = True
                        if not was_previously_online:
                            notification_sent = True
                            await self.send_message_to_channel(
                                settings.TWITCH_ANNOUNCEMENT_MESSAGE.format(
                                    streamer=stream['user_name'],
                                    stream_link="https://twitch.tv/" + stream['user_name'],
                                    stream_description=stream['title']),
                                int(settings.read_option(settings.KEY_ANNOUNCEMENT_CHANNEL_TWITCH, 0)))
                print("Twitch: isOnline: {}, wasPreviouslyOnline: {}".format(is_online, was_previously_online))
                was_previously_online = is_online
            except Exception as e:
                print(e)
            if notification_sent:
                print("Twitch: Notification sent, going for a long sleep")
                await asyncio.sleep(settings.TWITCH_POLL_COOLDOWN_MINUTES * 60)
            else:
                await asyncio.sleep(settings.TWITCH_POLL_RATE)

    async def send_message_to_channel(self, string, channel_id: int):
        print("Sending announcement to channel {}".format(channel_id))
        channel = self.bot.get_channel(channel_id)
        await channel.send(string)

    @commands.command()
    @commands.has_any_role("Mods", "Admin")
    async def disabletwitch(self, ctx):
        """Stop sending twitch updates"""
        self.task.cancel()
        self.task = None

        settings.write_option(settings.KEY_TWITCH_INTEGRATION, "False")
        await ctx.send("Twitch integration disabled")

    @commands.command()
    @commands.has_any_role("Mods", "Admin")
    async def enabletwitch(self, ctx, twitch_username):
        """Send twitch updates to this channel"""
        print(str(ctx.message.channel.id))
        if isinstance(ctx.message.channel, discord.TextChannel):
            user_json = self.get_twitch_user_by_name(twitch_username)

            if isinstance(user_json, Exception):
                await ctx.send("*Error: {}*".format(str(user_json)))
                return
            print(user_json)

            try:
                print("Found userid: {}".format(user_json["data"][0]["id"]))
                settings.write_option(settings.KEY_TWITCH_CHANNEL, user_json["data"][0]["display_name"])
                settings.write_option(settings.KEY_ANNOUNCEMENT_CHANNEL_TWITCH, str(ctx.message.channel.id))
                settings.write_option(settings.KEY_TWITCH_INTEGRATION, "True")
                await ctx.send(
                    "Successfully set the announcement channel to: {}, I will post here when {} comes online.".format(
                        ctx.message.channel.name, twitch_username))

                if self.task is None:
                    self.task = asyncio.create_task(self.poll_thread())
            except IndexError:
                await ctx.send("Could not find user {}".format(twitch_username))
            except Exception as e:
                await ctx.send(str(e))
        else:
            await ctx.send("Needs to be done in a regular channel")
            return

    @enabletwitch.error
    async def enabletwitch_error(self, ctx, error):
        if isinstance(error, commands.UserInputError):
            await ctx.send('Usage: `{}enabletwitch <twitch_channel_name>` '
                           '\nIt must be used in a regular channel so it knows where to post announcements.'
                           .format(settings.CALL_CHARACTER))
