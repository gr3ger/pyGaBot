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

    def remove_vote(self, index, user):
        self.options[index].votes.remove(user)


class Option:
    def __init__(self, name="", author="", author_id=0):
        self.author = author
        self.author_id = author_id
        self.name = name
        self.votes = []
