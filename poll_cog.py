import os
import pickle
import time
from datetime import datetime

import discord
from discord.ext import commands

import settings
from poll import Poll


class PollCog(commands.Cog, name="Polls"):
    poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    def __init__(self, bot):
        self.bot = bot
        self.polls = []

        if os.path.isfile('polls.bin'):
            self.polls = pickle.load(open("polls.bin", "rb"))

    async def send_message_to_channel(self, string, channel_id: int):
        print("Sending announcement to channel {}".format(channel_id))
        channel = self.bot.get_channel(channel_id)
        await channel.send(string)

    # This will fetch the original message, and read all the reactions which in turn will update even if stuff
    # happened while offline! Should probably only be used when closing the poll because of the HTTP calls.
    async def updatePollStatus(self, id):
        message = await self.bot.get_channel(self.polls[id].channel_id).fetch_message(self.polls[id].message_id)
        print(message)
        for reaction in message.reactions:
            try:
                option_index = PollCog.poll_emojis.index(str(reaction))
            except ValueError:
                continue

            final_string = "{}: ".format(reaction)
            self.polls[id].options[option_index].votes.clear()
            async for user in reaction.users():
                self.polls[id].options[option_index].votes.append(str(user))
                final_string += "{}, ".format(user)
            print(final_string)

    @commands.command(usage='<hours> <"Poll title"> <first movie option>'
                            '\nExample: {call_character}makepoll 48 "Gabber Movie Poll" Yeeting with Wolves'
                      .format(call_character=settings.CALL_CHARACTER))
    @commands.has_any_role("Mods", "Admin")
    async def makepoll(self, ctx, *args):
        """Creates a poll other users can add options and vote for"""
        endtime = time.time() + (int(args[0]) * 60 * 60)
        print(datetime.fromtimestamp(endtime).__str__())

        poll = Poll(name=args[1], endtime=endtime)
        poll.add_option(ctx.message.author.name, ctx.message.author.id,
                        " ".join(args[2:]))
        self.polls.append(poll)

        votes = ""
        embed = discord.Embed(title="*created by {creator_name}* - Poll is active, {hours_left} hours left.".format(
            creator_name=ctx.message.author.name, hours_left=args[0]), color=0xff3333)
        embed.set_author(
            name="{poll_name} - Poll number #{poll_number}".format(poll_name=args[1], poll_number=str(len(self.polls))),
            icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=ctx.message.guild.icon_url)
        for x in range(0, 9):
            if poll.options[x].name == "":
                continue
            embed.add_field(name="{num_emoji} - `{movie_title}` - *[{user}]*".format(num_emoji=PollCog.poll_emojis[x],
                                                                                     movie_title=poll.options[x].name,
                                                                                     user=poll.options[x].author),
                            value="Votes: **[{votes}]**".format(votes=votes), inline=False)
        response = await ctx.send(embed=embed)
        poll.message_id = response.id
        poll.channel_id = ctx.message.channel.id
        pickle.dump(self.polls, open("polls.bin", "wb"))

    @makepoll.error
    async def makepoll_error(self, ctx, error):
        await ctx.send(
            "```Usage: {prefix}{usage}```".format(prefix=settings.CALL_CHARACTER,
                                                  usage=self.bot.get_command("makepoll").usage))

    @commands.command()
    async def addoption(self, ctx):
        await ctx.send("addoption: Not implemented yet")

    @commands.command()
    @commands.has_any_role("Mods", "Admin")
    async def forceaddoption(self, ctx):
        await ctx.send("forceaddoption: Not implemented yet")

    @commands.command()
    @commands.has_any_role("Mods", "Admin")
    async def removeoption(self, ctx):
        await ctx.send("removeoption: Not implemented yet")
