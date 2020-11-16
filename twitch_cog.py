import sys
import urllib.request

import discord
from discord.ext import commands
from twitchAPI import Twitch, TwitchWebHook

import settings
from models import TwitchSettings


class TwitchCog(commands.Cog, name="Twitch"):
    twitch = Twitch(settings.TWITCH_CLIENT_ID, settings.TWITCH_CLIENT_SECRET)

    def __init__(self, bot):
        self.bot = bot
        self.task = None
        self.was_previously_online = False

        self.twitch.authenticate_app([])
        webhook_callback_address = 'https://' + urllib.request.urlopen('https://ident.me').read().decode(
            'utf8') + ':5001'
        print(webhook_callback_address)
        self.hook = TwitchWebHook(webhook_callback_address,
                                  settings.TWITCH_CLIENT_ID, 5000)
        self.hook.authenticate(self.twitch)
        self.hook.start()

    def get_twitch_user_by_name(self, usernames):
        try:
            return self.twitch.get_users(logins=usernames)
        except Exception as e:
            print(e, file=sys.stderr)
            return e

    def callback_stream_changed(self, uuid, data):
        print('Callback Stream changed for UUID ' + str(uuid))
        print(data)

    async def send_message_to_channel(self, string, channel_id: int):
        print("Sending announcement to channel {}".format(channel_id))
        channel = self.bot.get_channel(channel_id)
        await channel.send(string)

    @commands.command()
    @commands.has_any_role("Mods", "Admin")
    async def disabletwitch(self, ctx):
        """Stop sending twitch updates"""
        current_sub = TwitchSettings.get(guild_id=ctx.guild.id)
        if current_sub is not None:
            success = self.hook.unsubscribe(current_sub.hook_uuid)
            if success:
                current_sub.delete_instance()
                await ctx.send("Successfully unsubscribed from twitch updates")
            else:
                await ctx.send("Failed to unsubscribe from twitch")
        else:
            await ctx.send("You don't seem to be subscribed for any twitch updates")

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
                success, uuid = self.hook.subscribe_stream_changed(user_id=user_json["data"][0]["id"],
                                                                   callback_func=self.callback_stream_changed)
                print("hook: {}, uuid: {}".format(success, uuid))
                if success:
                    twitch_settings, _ = TwitchSettings.get_or_create(guild_id=ctx.guild.id)
                    twitch_settings.twitch_channel = str(user_json["data"][0]["id"])
                    twitch_settings.announcement_channel = str(ctx.message.channel.id)
                    twitch_settings.hook_uuid = uuid
                    twitch_settings.save()
                    await ctx.send(
                        "Successfully set the announcement channel to: {}, I will post here when {} comes online.".format(
                            ctx.message.channel.name, twitch_username))
                else:
                    await ctx.send("Failed to create a webhook, notify the bot administrator")
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
