from . import db


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date_attempted = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    user = db.relationship(
        'User',
        backref=db.backref('quizzes', lazy=True, cascade='all, delete-orphan'),
    )


class PendingQuestion(db.Model):
    """The question a user is currently answering.

    Kept on the server so the correct answer is never sent to the browser.
    One row per user; generating a new question replaces it.
    """

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.Text, nullable=False)  # JSON: question, options, correct_answer
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

    user = db.relationship(
        'User',
        backref=db.backref('pending_question', uselist=False, cascade='all, delete-orphan'),
    )
