import asyncio
import os
import pickle
import sys
from os.path import exists

from discord.ext import commands
from discord.ext.commands import CommandNotFound

import settings
from poll_cog import PollCog
from twitch_cog import TwitchCog
from youtube_cog import YoutubeCog

if sys.version_info < (3, 7):
    print("You are using Python version {major}.{minor}.{micro}, you need at least Python 3.7".format(
        major=sys.version_info.major, minor=sys.version_info.minor, micro=sys.version_info.micro))
    exit()

if not exists("config.ini"):
    print("Could not find config.ini")
    exit()

async_loop = asyncio.get_event_loop()
bot = commands.Bot(command_prefix=settings.CALL_CHARACTER)
custom_commands = {}

if os.path.isfile('custom_commands.bin'):
    custom_commands = pickle.load(open("custom_commands.bin", "rb"))


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    bot.add_cog(PollCog(bot))
    bot.add_cog(TwitchCog(bot))
    bot.add_cog(YoutubeCog(bot))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        command = ctx.message.content.split()[0].replace(bot.command_prefix, "")
        if command in custom_commands:
            await ctx.send(custom_commands[command])
        return
    raise error


@bot.command()
@commands.has_any_role("Mods", "Admin")
async def addcommand(ctx, *args):
    """Adds a custom text command"""

    if args[0] in custom_commands:
        await ctx.send("there is already a custom command named `{}`".format(args[0]), delete_after=3)
        return
    if args[0] in bot.all_commands.keys():
        await ctx.send("there is already a native command named `{}`".format(args[0]), delete_after=3)
        return

    value = " ".join(ctx.message.content.split(" ")[2:])
    if value == "":
        await ctx.send("The value of the command cannot be empty".format(args[0]), delete_after=3)
        return

    custom_commands[args[0]] = value
    pickle.dump(custom_commands, open("custom_commands.bin", "wb"))
    await ctx.send("`{}` has been added as a new custom command".format(args[0]))


@bot.command()
@commands.has_any_role("Mods", "Admin")
async def removecommand(ctx, key):
    """Removes a custom text command"""
    if key in custom_commands:
        del custom_commands[key]
        await ctx.send("`{}` has been removed from the custom command list".format(key))
        pickle.dump(custom_commands, open("custom_commands.bin", "wb"))
    else:
        await ctx.send("there is no custom command named `{}`".format(key), delete_after=3)


@bot.command()
async def listcommands(ctx):
    """Lists all custom text commands"""
    output = "```"
    for key in custom_commands:
        output += "{} - {}\n".format(key,
                                     (custom_commands[key][:40] + '...').replace('\n', ' ').replace('\r', '') if len(
                                         custom_commands[key].replace('\n', ' ').replace('\r', '')) > 43 else
                                     custom_commands[key].replace('\n', ' ').replace('\r', ''))

    if output != "```":
        output += "```"
        await ctx.send(output)
    else:
        await ctx.send("There are currently no registered text commands", delete_after=3)


print("starting bot")
bot.run(settings.DISCORD_TOKEN)
