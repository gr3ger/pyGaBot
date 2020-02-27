import asyncio
import json
import os
import pickle
import sys
import time
import urllib.request
from datetime import datetime
from os.path import exists

import discord
import jsonpickle
from discord.ext import commands

import settings
from poll import Poll, Option
from twitch_cog import TwitchCog

if sys.version_info < (3, 7):
    print("You are using Python version {major}.{minor}.{micro}, you need at least Python 3.7".format(
        major=sys.version_info.major, minor=sys.version_info.minor, micro=sys.version_info.micro))
    exit()

if not exists("config.ini"):
    print("Could not find config.ini")
    exit()

async_loop = asyncio.get_event_loop()
DISCORD_TOKEN = settings.config['DEFAULT']['DiscordToken']
CALL_CHARACTER = settings.config['DEFAULT']['CallCharacter']
TWITCH_CLIENT_ID = settings.config['DEFAULT']['TwitchClientID']
TWITCH_CLIENT_SECRET = settings.config['DEFAULT']['TwitchClientSecret']
bot = commands.Bot(command_prefix=CALL_CHARACTER)
poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

polls = []

if os.path.isfile('polls.bin'):
    polls = pickle.load(open("polls.bin", "rb"))


def get_external_ip():
    return urllib.request.urlopen('https://ident.me').read().decode('utf8')


def json_converter(o):
    if isinstance(o, datetime):
        return o.__str__()
    elif isinstance(o, Poll):
        return o.__dict__
    elif isinstance(o, Option):
        return o.__dict__
    else:
        return json.JSONEncoder.default(o)


# This will fetch the original message, and read all the reactions which in turn will update even if stuff
# happened while offline! Should probably only be used when closing the poll because of the HTTP calls.
async def updatePollStatus(id):
    message = await bot.get_channel(polls[id].channel_id).fetch_message(polls[id].message_id)
    print(message)
    for reaction in message.reactions:
        option_index = 0
        try:
            option_index = poll_emojis.index(str(reaction))
        except ValueError:
            continue

        final_string = "{}: ".format(reaction)
        polls[id].options[option_index].votes.clear()
        async for user in reaction.users():
            polls[id].options[option_index].votes.append(str(user))
            final_string += "{}, ".format(user)
        print(final_string)


@bot.command(hidden=True)
@commands.has_any_role("Mods", "Admin")
async def test(ctx):
    """Developer test function"""
    # await updatePollStatus(0)
    print(jsonpickle.encode(polls))


@bot.command(usage='<hours> <"Poll title"> <first movie option>'
                   '\nExample: {call_character}makepoll 48 "Gabber Movie Poll" Yeeting with Wolves'
             .format(call_character=CALL_CHARACTER))
@commands.has_any_role("Mods", "Admin")
async def makepoll(ctx, *args):
    """Creates a poll other users can add options and vote for"""
    endtime = time.time() + (int(args[0]) * 60 * 60)
    print(datetime.fromtimestamp(endtime).__str__())

    poll = Poll(name=args[1], endtime=endtime)
    poll.add_option(ctx.message.author.name, ctx.message.author.id,
                    " ".join(args[2:]))
    print(json.dumps(poll, default=json_converter))

    polls.append(poll)

    votes = ""
    embed = discord.Embed(title="*created by {creator_name}* - Poll is active, {hours_left} hours left.".format(
        creator_name=ctx.message.author.name, hours_left=args[0]), color=0xff3333)
    embed.set_author(
        name="{poll_name} - Poll number #{poll_number}".format(poll_name=args[1], poll_number=str(len(polls))),
        icon_url=ctx.message.author.avatar_url)
    embed.set_thumbnail(url=ctx.message.guild.icon_url)
    for x in range(0, 9):
        if poll.options[x].name == "":
            continue
        embed.add_field(name="{num_emoji} - `{movie_title}` - *[{user}]*".format(num_emoji=poll_emojis[x],
                                                                                 movie_title=poll.options[x].name,
                                                                                 user=poll.options[x].author),
                        value="Votes: **[{votes}]**".format(votes=votes), inline=False)
    response = await ctx.send(embed=embed)
    poll.message_id = response.id
    poll.channel_id = ctx.message.channel.id
    pickle.dump(polls, open("polls.bin", "wb"))


@makepoll.error
async def makepoll_error(ctx, error):
    if isinstance(error, commands.UserInputError):
        await ctx.send('Usage: `{call_character}makepoll <hours> <"Poll title"> <first movie option>`'
                       '\nExample: `{call_character}makepoll 48 "Gabber Movie Poll" Yeeting with Wolves`'
                       .format(call_character=CALL_CHARACTER))
    else:
        await ctx.send(str(error))


@bot.command()
async def addoption(ctx):
    await ctx.send("addoption: Not implemented yet")


@bot.command()
@commands.has_any_role("Mods", "Admin")
async def forceaddoption(ctx):
    await ctx.send("forceaddoption: Not implemented yet")


@bot.command()
@commands.has_any_role("Mods", "Admin")
async def removeoption(ctx):
    await ctx.send("removeoption: Not implemented yet")


@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    bot.add_cog(TwitchCog(bot, TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET, CALL_CHARACTER))


@bot.event
async def on_raw_reaction_add(payload):
    print(payload)


@bot.event
async def on_raw_reaction_remove(payload):
    print(payload)


print("starting bot")
bot.run(DISCORD_TOKEN)
