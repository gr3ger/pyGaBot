from utils import intersection


class PollList:
    def __init__(self):
        self.polls = []
        self.currentIndex = 1


class Poll:
    def __init__(self, message_id=0, name="", endtime="", channel_id=0, id=0, icon_url="", thumbnail_url="", author=""):
        self.id = id
        self.channel_id = channel_id
        self.message_id = message_id
        self.name = name
        self.endtime = endtime
        self.options = [Option() for _ in range(10)]
        self.is_active = True
        self.icon_url = icon_url
        self.thumbnail_url = thumbnail_url
        self.author = author

    def add_option(self, author, author_id, movie):
        for option in self.options:
            if option.name == "":
                option.name = movie
                option.author = author
                option.author_id = author_id
                break

    def add_vote(self, index, user_id):
        self.options[index].votes.append(user_id)

    def remove_vote(self, index, user_id):
        self.options[index].votes.remove(user_id)

    def has_already_voted(self, user_id):
        for option in self.options:
            if user_id in option.votes:
                return True
        return False

    def get_vote_count(self, option_index, bot_id):
        # Intersect all votes to know which ones we should ignore
        tempList = set()
        for i in range(0, 10):
            if i != option_index:
                tempList.update(self.options[i].votes)
        tempList = intersection(tempList, self.options[option_index].votes)

        # Remove bot ID since it's allowed to make multiple votes
        try:
            tempList.remove(bot_id)
        except ValueError:
            pass

        votes = self.options[option_index].votes
        count = 0
        for user in votes:
            if user not in tempList:
                count += 1

        return count


class Option:
    def __init__(self, name="", author="", author_id=0):
        self.author = author
        self.author_id = author_id
        self.name = name
        self.votes = []
