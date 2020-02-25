class Attempt:
    def __init__(self, id, evaluation_id, word, wsd, duration, date_created=None, include=True):
        self.id = id
        self.evaluation_id = evaluation_id
        self.word = word
        self.wsd = wsd
        self.duration = duration
        self.date_created = date_created
        self.include = include

    def to_response(self):
        r = {
            'attemptId': self.id,
            'evaluationId': self.evaluation_id,
            'word': self.word,
            'wsd': self.wsd,
            'duration': self.duration,
            'include': self.include,
            'dateCreated': self.date_created
        }
        return r

    @staticmethod
    def from_row(row):
        evaluation_id, word, id, wsd, duration, include, date_created = row
        include = bool(include)
        return Attempt(id, evaluation_id, word, wsd, duration, date_created)