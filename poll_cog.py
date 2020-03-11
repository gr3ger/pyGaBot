import os
import pickle
from datetime import datetime

import discord
from discord.ext import commands

import settings
from poll import Poll, PollList


class PollCog(commands.Cog, name="Polls"):
    poll_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    def __init__(self, bot):
        self.bot = bot
        self.pollList = PollList()

        if os.path.isfile('polls.bin'):
            self.pollList = pickle.load(open("polls.bin", "rb"))

    async def send_message_to_channel(self, string, channel_id: int):
        print("Sending announcement to channel {}".format(channel_id))
        channel = self.bot.get_channel(channel_id)
        await channel.send(string)

    # This will fetch the original message, and read all the reactions which in turn will update even if stuff
    # happened while offline! Should probably only be used when closing the poll because of (I assume) the HTTP calls.
    async def updatePollStatus(self, poll_id):
        poll = None
        for p in self.pollList.polls:
            if p.id == poll_id:
                poll = p
                break

        if poll is None:
            print("Could not find a poll with id {}".format(poll_id))
            return

        message = await self.bot.get_channel(poll.channel_id).fetch_message(
            poll.message_id)
        print(message)
        for reaction in message.reactions:
            try:
                option_index = PollCog.poll_emojis.index(str(reaction))
            except ValueError:
                continue

            final_string = "{}: ".format(reaction)
            poll.options[option_index].votes.clear()
            async for user in reaction.users():
                poll.options[option_index].votes.append(str(user))
                final_string += "{}, ".format(user)
            print(final_string)
        pickle.dump(self.pollList, open("polls.bin", "wb"))

    @commands.command(usage='<hours> <"Poll title"> <first movie option>'
                            '\nExample: {call_character}makepoll 48 "Gabber Movie Poll" Yeeting with Wolves'
                      .format(call_character=settings.CALL_CHARACTER))
    @commands.has_any_role("Mods", "Admin")
    async def makepoll(self, ctx, *args):
        """Creates a poll other users can add options and vote for"""
        endtime = int(datetime.utcnow().strftime("%s")) + (int(args[0]) * 60 * 60)

        poll = Poll(name=args[1], endtime=endtime, id=self.pollList.currentIndex, channel_id=ctx.message.channel.id)
        poll.add_option(ctx.message.author.name, ctx.message.author.id,
                        " ".join(args[2:]))

        response = await self.printPoll(ctx, poll)
        poll.message_id = response.id
        self.pollList.currentIndex += 1
        self.pollList.polls.append(poll)

        await response.add_reaction(self.poll_emojis[0])
        pickle.dump(self.pollList, open("polls.bin", "wb"))

    async def printPoll(self, ctx, poll):
        votes = ""
        embed = discord.Embed(title="*created by {creator_name}* - Poll is active, ends on {endtime}.".format(
            creator_name=ctx.message.author.name,
            endtime=datetime.fromtimestamp(poll.endtime).strftime("%Y-%m-%d %H:%M UTC")),
            color=0xff3333)
        embed.set_author(
            name="{poll_name} - Poll number #{poll_id}".format(poll_name=poll.name,
                                                               poll_id=poll.id),
            icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=ctx.message.guild.icon_url)
        embed.set_footer(text="Vote for any of the options by reacting to this message with :one:, :two:, etc.\n"
                              "Use the command `!addoption {} OptionName` to add a new option to the poll.".format(
            str(poll.id)))
        for x in range(0, 9):
            if poll.options[x].name == "":
                continue
            embed.add_field(name="{num_emoji} - `{movie_title}` - *[{user}]*".format(num_emoji=PollCog.poll_emojis[x],
                                                                                     movie_title=poll.options[x].name,
                                                                                     user=poll.options[x].author),
                            value="Votes: **[{votes}]**".format(votes=votes), inline=False)
        return await ctx.send(embed=embed)

    @makepoll.error
    async def makepoll_error(self, ctx, error):
        print("Failed creating poll: {}".format(error))
        await ctx.send(
            "```Usage: {prefix}makepoll {usage}```".format(prefix=settings.CALL_CHARACTER,
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

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        print(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        print(payload)
