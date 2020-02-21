class Poll:
    def __init__(self, message_id=0, name="", endtime="", channel_id=0):
        self.channel_id = channel_id
        self.message_id = message_id
        self.name = name
        self.endtime = endtime
        self.options = [Option() for _ in range(10)]
        self.is_active = True

    def add_option(self, author, author_id, movie):
        for option in self.options:
            if option.name == "":
                option.name = movie
                option.author = author
                option.author_id = author_id
                break


class Option:
    def __init__(self, name="", author="", author_id=0):
        self.author = author
        self.author_id = author_id
        self.name = name
        self.votes = []
