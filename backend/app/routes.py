import json
from datetime import datetime
from functools import wraps
from urllib.parse import urlparse

import requests
from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, url_for)
from flask_login import current_user, login_required, login_user, logout_user
from google import genai
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import case, or_

from . import db
from .forms import (ConfirmForm, CreateUserForm, LoginForm, ProfileForm,
                    RegistrationForm, ResetPasswordForm, UserForm)
from .models.quizz import PendingQuestion, Quiz
from .models.role import Role
from .models.user import User
from .send_notification import send_email

main = Blueprint('main', __name__)

PASSWORD_RESET_SALT = 'password-reset-salt'
PASSWORD_RESET_MAX_AGE = 3600  # seconds
MAX_TOPIC_LENGTH = 100  # matches Quiz.topic
ANSWER_KEYS = ('A', 'B', 'C', 'D')


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def admin_required(view):
    """Allow access only to logged-in users with the Admin role."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return login_required(wrapper)


def is_safe_redirect(target):
    """Only allow redirects to paths on this site (prevents open redirects)."""
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc and target.startswith('/') and not target.startswith('//')


def default_user_role():
    role = Role.query.filter_by(name='User').first()
    if role is None:
        role = Role(name='User')
        db.session.add(role)
        db.session.flush()
    return role


def find_conflicting_user(username, email, exclude_id=None):
    query = User.query.filter(or_(User.username == username, User.email == email))
    if exclude_id is not None:
        query = query.filter(User.id != exclude_id)
    return query.first()


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

@main.route('/')
def index():
    return redirect(url_for('main.home'))


@main.route('/home')
def home():
    return render_template('index.html')


@main.route('/challenges')
@login_required
def challenges():
    return render_template('challenges.html')


# --------------------------------------------------------------------------
# Authentication
# --------------------------------------------------------------------------

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        if find_conflicting_user(form.username.data, form.email.data):
            flash('That username or email is already registered.', 'danger')
            return render_template('register.html', form=form)

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role_id=default_user_role().id,
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)


@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('You have been logged in!', 'success')
            next_page = request.args.get('next')
            if not is_safe_redirect(next_page):
                next_page = url_for('main.home')
            return redirect(next_page)
        flash('Invalid username or password', 'danger')
    return render_template('login.html', title='Log In', form=form)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))


def get_serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip()
        user = User.query.filter_by(email=email).first() if email else None
        if user:
            token = get_serializer().dumps(user.email, salt=PASSWORD_RESET_SALT)
            reset_url = url_for('main.reset_password', token=token, _external=True)
            try:
                send_email(
                    'Password Reset Request',
                    user.email,
                    f'Please click the link to reset your password (valid for 1 hour): {reset_url}',
                )
            except Exception:
                current_app.logger.exception('Failed to send password reset email.')
        # Same message either way, so the form can't be used to find accounts.
        flash('If that email is registered, a password reset link has been sent.', 'info')
        return redirect(url_for('main.login'))
    return render_template('forgot_password.html')


@main.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = get_serializer().loads(token, salt=PASSWORD_RESET_SALT, max_age=PASSWORD_RESET_MAX_AGE)
    except (SignatureExpired, BadSignature):
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('main.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if user is None:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('main.forgot_password'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated!', 'success')
        return redirect(url_for('main.login'))

    return render_template('reset_password.html', form=form, token=token)


# --------------------------------------------------------------------------
# Quiz
# --------------------------------------------------------------------------

DEFAULT_QUESTIONS = {
    "science": {
        "question": "What is the chemical symbol for water?",
        "options": {"A": "H2O", "B": "O2", "C": "CO2", "D": "NaCl"},
        "correct_answer": "A",
    },
    "history": {
        "question": "Which ancient civilization built the pyramids at Giza?",
        "options": {"A": "Romans", "B": "Egyptians", "C": "Vikings", "D": "Mayans"},
        "correct_answer": "B",
    },
    "geography": {
        "question": "What is the largest ocean on Earth?",
        "options": {"A": "Atlantic", "B": "Indian", "C": "Pacific", "D": "Arctic"},
        "correct_answer": "C",
    },
    "general": {
        "question": "How many days are there in a leap year?",
        "options": {"A": "365", "B": "366", "C": "364", "D": "367"},
        "correct_answer": "B",
    },
}


def build_prompt(topic):
    return (
        f"Generate a quiz question about {topic}. "
        "Format the response as JSON with the following keys:\n"
        "- \"question\": The quiz question text.\n"
        "- \"options\": An object with keys \"A\", \"B\", \"C\", and \"D\", representing four answer choices.\n"
        "- \"correct_answer\": The key (A, B, C, or D) corresponding to the correct answer.\n"
        "For example:\n"
        "{\n"
        "    \"question\": \"What is the chemical symbol for water?\",\n"
        "    \"options\": {\n"
        "        \"A\": \"H2O\",\n"
        "        \"B\": \"O2\",\n"
        "        \"C\": \"CO2\",\n"
        "        \"D\": \"NaCl\"\n"
        "    },\n"
        "    \"correct_answer\": \"A\"\n"
        "}\n"
    )


def extract_json(text):
    """Return the first JSON object found in text, or None."""
    decoder = json.JSONDecoder()
    for start, character in enumerate(text):
        if character != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    return None


def validate_question(question):
    required_keys = {"question", "options", "correct_answer"}
    if not isinstance(question, dict) or not required_keys.issubset(question):
        raise ValueError("Generated question is missing required fields")
    if not isinstance(question["options"], dict) or set(question["options"]) != set(ANSWER_KEYS):
        raise ValueError("Generated question must contain four options")
    if question["correct_answer"] not in question["options"]:
        raise ValueError("Generated question has an invalid correct answer")
    return {
        "question": str(question["question"]),
        "options": {key: str(question["options"][key]) for key in ANSWER_KEYS},
        "correct_answer": question["correct_answer"],
    }


def generate_with_gemini(prompt):
    api_key = current_app.config.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=current_app.config["GEMINI_MODEL"],
        contents=prompt,
        config={
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        },
    )
    question = extract_json(response.text.strip())
    if question is None:
        raise ValueError("Gemini returned invalid JSON")
    return validate_question(question)


def generate_with_ollama(prompt):
    response = requests.post(
        f"{current_app.config['OLLAMA_URL'].rstrip('/')}/api/generate",
        json={
            "model": current_app.config["OLLAMA_MODEL"],
            "prompt": prompt,
            "format": "json",
            "stream": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    question = extract_json(response.json().get("response", "").strip())
    if question is None:
        raise ValueError("Ollama returned invalid JSON")
    return validate_question(question)


def get_default_question(topic):
    topic_key = str(topic).strip().lower()
    return dict(DEFAULT_QUESTIONS.get(topic_key, DEFAULT_QUESTIONS["general"]))


def create_question(topic):
    """Try Gemini, then Ollama, then the built-in questions."""
    prompt = build_prompt(topic)
    try:
        return generate_with_gemini(prompt)
    except Exception:
        current_app.logger.exception("Gemini quiz generation failed.")
    try:
        return generate_with_ollama(prompt)
    except (requests.RequestException, ValueError, KeyError, TypeError):
        current_app.logger.exception("Ollama quiz generation failed.")
    return get_default_question(topic)


@main.route('/start_quiz/<category>')
@login_required
def start_quiz(category):
    return render_template('quizz.html', category=category[:MAX_TOPIC_LENGTH])


@main.route('/generate_question', methods=['POST'])
@login_required
def generate_question():
    data = request.get_json(silent=True) or {}
    topic = str(data.get('topic') or '').strip()
    if not topic:
        return jsonify({"error": "No topic provided."}), 400
    topic = topic[:MAX_TOPIC_LENGTH]

    question = create_question(topic)

    # Replace any earlier unanswered question for this user.
    pending = db.session.get(PendingQuestion, current_user.id)
    if pending is None:
        pending = PendingQuestion(user_id=current_user.id)
        db.session.add(pending)
    pending.topic = topic
    pending.payload = json.dumps(question)
    pending.created_at = datetime.utcnow()
    db.session.commit()

    # The correct answer stays on the server.
    return jsonify({"topic": topic, "question": question["question"], "options": question["options"]})


@main.route('/submit_answer', methods=['POST'])
@login_required
def submit_answer():
    data = request.get_json(silent=True) or {}
    answer = str(data.get('answer') or '').strip().upper()
    if answer not in ANSWER_KEYS:
        return jsonify({"error": "Please choose A, B, C or D."}), 400

    pending = db.session.get(PendingQuestion, current_user.id)
    if pending is None:
        return jsonify({"error": "No active question. Generate a new one."}), 404

    question = json.loads(pending.payload)
    correct_answer = question["correct_answer"]
    is_correct = answer == correct_answer
    score = 1 if is_correct else 0

    db.session.add(Quiz(user_id=current_user.id, topic=pending.topic, score=score))
    current_user.quizzes_attempted = (current_user.quizzes_attempted or 0) + 1
    current_user.last_quiz_score = score
    current_user.last_quiz_date = datetime.utcnow()
    db.session.delete(pending)  # each question can be answered only once
    db.session.commit()

    correct_text = question["options"][correct_answer]
    if is_correct:
        feedback = f"Correct! The answer is {correct_answer}: {correct_text}."
    else:
        feedback = f"Incorrect. The correct answer is {correct_answer}: {correct_text}."
    return jsonify({
        "correct": is_correct,
        "correct_answer": correct_answer,
        "feedback": feedback,
    })


# --------------------------------------------------------------------------
# Profile, history and leaderboard
# --------------------------------------------------------------------------

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = current_user
    form = ProfileForm(obj=user)

    if form.validate_on_submit():
        if find_conflicting_user(None, form.email.data, exclude_id=user.id):
            flash('That email is already used by another account.', 'danger')
            return render_template('profile.html', form=form, user=user)
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('main.profile'))

    return render_template('profile.html', form=form, user=user)


@main.route('/quiz_history/<int:user_id>')
@login_required
def quiz_history(user_id):
    if user_id != current_user.id and not current_user.is_admin:
        abort(403)

    success = case((Quiz.score > 0, 1), else_=0)
    failure = case((Quiz.score == 0, 1), else_=0)
    user_quizzes = (
        db.session.query(
            Quiz.topic,
            db.func.count(Quiz.id).label('total'),
            db.func.sum(success).label('success_count'),
            db.func.sum(failure).label('failure_count'),
            (db.func.sum(success) * 100.0 / db.func.count(Quiz.id)).label('success_rate'),
            db.func.max(Quiz.date_attempted).label('last_attempt_date'),
        )
        .filter(Quiz.user_id == user_id)
        .group_by(Quiz.topic)
        .all()
    )
    return render_template('quizz_history.html', user_quizzes=user_quizzes)


@main.route('/leaderboard', methods=['GET'])
def leaderboard():
    return render_template('leaderboard.html')


@main.route('/leaderboards')
def leaderboard_data():
    limit = max(1, min(request.args.get('limit', 10, type=int), 100))
    points = db.func.coalesce(db.func.sum(Quiz.score), 0).label('points')
    rows = (
        db.session.query(User, points)
        .outerjoin(Quiz, Quiz.user_id == User.id)
        .group_by(User.id)
        .order_by(points.desc(), User.username)
        .limit(limit)
        .all()
    )
    return jsonify([
        {
            'username': user.username,
            'fullname': f"{user.first_name} {user.last_name}",
            'points': int(total),
        }
        for user, total in rows
    ])


# --------------------------------------------------------------------------
# Admin: users
# --------------------------------------------------------------------------

@main.route('/admin/users')
@admin_required
def list_users():
    users = User.query.order_by(User.username).all()
    return render_template('list_users.html', users=users, delete_form=ConfirmForm())


@main.route('/admin/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        if find_conflicting_user(form.username.data, form.email.data):
            flash('That username or email is already registered.', 'danger')
            return render_template('create_user.html', form=form)
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role_id=form.role.data,
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('main.list_users'))
    return render_template('create_user.html', form=form)


@main.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)
    if request.method == 'GET':
        form.role.data = user.role_id

    if form.validate_on_submit():
        if find_conflicting_user(form.username.data, form.email.data, exclude_id=user.id):
            flash('That username or email is already used by another account.', 'danger')
            return render_template('edit_user.html', form=form, user=user)
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.role_id = form.role.data
        if form.password.data:
            user.set_password(form.password.data)
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('main.list_users'))
    return render_template('edit_user.html', form=form, user=user)


@main.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    if not ConfirmForm().validate_on_submit():
        abort(400)
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('main.list_users'))
    db.session.delete(user)  # quizzes and pending question cascade
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('main.list_users'))


# --------------------------------------------------------------------------
# Admin: roles
# --------------------------------------------------------------------------

@main.route('/admin/roles')
@admin_required
def list_roles():
    roles = Role.query.order_by(Role.name).all()
    return render_template('list_roles.html', roles=roles, delete_form=ConfirmForm())


@main.route('/roles/create', methods=['GET', 'POST'])
@admin_required
def create_role():
    if request.method == 'POST':
        role_name = (request.form.get('role_name') or '').strip()
        if not role_name:
            flash('Role name is required.', 'danger')
        elif Role.query.filter_by(name=role_name).first():
            flash('That role already exists.', 'danger')
        else:
            db.session.add(Role(name=role_name))
            db.session.commit()
            flash('Role created successfully!', 'success')
            return redirect(url_for('main.list_roles'))
    return render_template('create_role.html')


@main.route('/roles/edit/<int:role_id>', methods=['GET', 'POST'])
@admin_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    if request.method == 'POST':
        role_name = (request.form.get('role_name') or '').strip()
        if not role_name:
            flash('Role name is required.', 'danger')
        elif Role.query.filter(Role.name == role_name, Role.id != role.id).first():
            flash('That role already exists.', 'danger')
        else:
            role.name = role_name
            db.session.commit()
            flash('Role updated successfully!', 'success')
            return redirect(url_for('main.list_roles'))
    return render_template('edit_role.html', role=role)


@main.route('/roles/delete/<int:role_id>', methods=['POST'])
@admin_required
def delete_role(role_id):
    if not ConfirmForm().validate_on_submit():
        abort(400)
    role = Role.query.get_or_404(role_id)
    if role.users:
        flash('This role is still assigned to users. Reassign them first.', 'danger')
        return redirect(url_for('main.list_roles'))
    db.session.delete(role)
    db.session.commit()
    flash('Role deleted successfully!', 'success')
    return redirect(url_for('main.list_roles'))
