from flask import Blueprint, abort, json, jsonify, render_template, redirect, request, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user
import requests
from .models.role import Role

from .models.quizz import Quiz
from . import db
from .forms import ProfileForm, RegistrationForm, LoginForm, UserForm
from .models.user import User
import os
import json
import google.generativeai as genai
import json
import re
main = Blueprint('main', __name__)

@main.route('/home')
@login_required
def home():
    return render_template('index.html')

@main.route('/challenges')
@login_required
def challenges():
    return render_template('challenges.html')

# Register Route
@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    form.role.choices = [(role.id, role.name) for role in Role.query.all()]
   
    if form.validate_on_submit():
        print("Form validated successfully.")
        if User.query.filter_by(username=form.username.data).first():
            flash('User already exists', 'danger')
            return redirect(url_for('main.register'))
        print("Creating new user...")
        
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            role_id=form.role.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data
        )
        new_user.set_password(form.password.data)
        
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully', 'success')
        return redirect(url_for('main.login'))
    else:
        print("Form validation failed:", form.errors)


    return render_template('register.html', form=form)
 
@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    next_page = request.args.get('next')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            #access_token = create_access_token(identity={'username': user.username})
            #print (access_token)
            flash('You have been logged in!', 'success')
            login_user(user, remember=form.remember_me.data)             # Redirect to 'next' page if available, otherwise redirect to 'home'
            return redirect(next_page or url_for('main.home'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html', title='Log In', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.login'))  # Redirect to login page or homepage
# Login Route
@main.route('/login2', methods=['GET', 'POST'])
def login2():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            access_token = create_access_token(identity={'username': user.username})
            flash('Logged in successfully', 'success')
            # Set the access token in a response cookie
            print("herererer")
            response = redirect(url_for('main.home'))
            set_access_cookies(response, access_token)
            return response  
            #return redirect(request.args.get('next') or url_for('main.home'))
        flash('Invalid credentials', 'danger')

    return render_template('login.html', title='Log In', form=form)

@main.route('/start_quiz/<category>')
#@login_required
def start_quiz(category):
    # Logic to start the quiz based on category
    return render_template('quizz.html', category=category , user=current_user)



# Set up generation config
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Initialize the Gemini model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="pretend that you are a chat application, ask me questions related to SCIENCE with 4 options, only one is correct."
)

# Store active chat sessions
chat_sessions = {}
@main.route('/generate_question', methods=['POST'])
def generate_question():
    user_id = 1 # Get user_id from the logged-in user
    topic = request.json.get('topic')
    if not topic:
        return jsonify({"error": "No topic provided."}), 400

    prompt = (
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

    chat_session = model.start_chat(
        history=[
            {
                "role": "user",
                "parts": [prompt],
            },
        ]
    )
    
    chat_sessions[user_id] = chat_session
    last_message = chat_session.history[-1]

    response = chat_session.send_message("Generate the quiz question.")
    raw_response_text = response.text
    print("Raw response text from model:", raw_response_text)

    # Clean the raw response text by removing the code block formatting
    cleaned_response_text = raw_response_text.strip().replace('```json', '').replace('```', '').strip()
    response_json = extract_json(cleaned_response_text)
    print("Extracted JSON objects:", response_json)
   
    if cleaned_response_text and cleaned_response_text.startswith("{") and cleaned_response_text.endswith("}"):
        return cleaned_response_text
    else:
        return jsonify({
            "error": "Invalid response structure.",
            "raw_response": cleaned_response_text
        }), 500

def extract_json(text_response):
    # This pattern matches a string that starts with '{' and ends with '}'
    pattern = r'\{[^{}]*\}'
    matches = re.finditer(pattern, text_response)
    json_objects = []

    for match in matches:
        json_str = match.group(0)
        try:
            # Validate if the extracted string is valid JSON
            json_obj = json.loads(json_str)
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            continue  # Skip invalid JSON

    if json_objects:
        return json_objects
    else:
        return None

def extend_search(text, span):
    # Extend the search to try to capture nested structures
    start, end = span
    nest_count = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            nest_count += 1
        elif text[i] == '}':
            nest_count -= 1
            if nest_count == 0:
                return text[start:i+1]
    return text[start:end]

 

@main.route('/submit_answer', methods=['POST'])
def submit_answer():
    user_id = request.json.get('user_id')
    user_answer = request.json.get('answer')

    if user_id not in chat_sessions:
        return jsonify({"error": "No active session found for this user."}), 404

    chat_session = chat_sessions[user_id]

    # Send the user's answer to the model
    response = chat_session.send_message(user_answer)
    raw_response_text = response.text
    cleaned_response_text = raw_response_text.strip().replace('```json', '').replace('```', '').strip()

    # Initialize variables
    feedback = ""
    explanation = ""
    question = ""

    # Check for feedback and explanation patterns
    if "correct answer is" in cleaned_response_text:
        parts = cleaned_response_text.split("correct answer is")
        feedback = parts[0].strip()  # Feedback portion
        explanation = parts[1].strip() if len(parts) > 1 else ""  # Explanation portion

        # Check if there's a follow-up question
        if "Would you like to try another question?" in explanation:
            explanation, question = explanation.split("Would you like to try another question?")
            question = "Would you like to try another question?"
        else:
            question = ""

    elif "That's correct!" in cleaned_response_text:
        feedback = cleaned_response_text.split(".")[0].strip()  # Get the initial feedback
        explanation = cleaned_response_text[len(feedback):].strip()  # Get the explanation
        question = "Would you like to try another question?"

    else:
        feedback = cleaned_response_text
        explanation = ""
        question = ""

    # Create a structured response
    response_data = {
        "explanation": explanation.strip(),
        "feedback": feedback.strip(),
        "question": question.strip()
    }
    return jsonify(response_data)

 
 
def calculate_quiz_score(user_answers):
    # Logic to calculate score based on user answers and correct answers
    # For simplicity, assume correct answers are known in this example:
    correct_answers = {"A": "H2O", "B": "O2"}  # Example
    score = 0
    
    for answer in user_answers:
        if answer in correct_answers:
            score += 1  # Increase score for correct answers

    return score

@main.route('/save_quiz', methods=['POST'])
@login_required  # Ensure the user is logged in
def save_quiz():
    data = request.json
    user_id = data.get('user_id')
    topic = data.get('topic')
    score = data.get('score')

    # Validate input
    if not user_id or not topic or score is None:
        return jsonify({"error": "Invalid input"}), 400

    user = User.query.get(user_id)
    if user:
        user.quizzes_attempted += 1 
        user.last_quiz_score = score 
        db.session.commit()  #

        # Create a new quiz record
        new_quiz = Quiz(user_id=user_id, topic=topic, score=score)
        db.session.add(new_quiz) 
        db.session.commit()  

        return jsonify({"success": True}), 200
    else:
        return jsonify({"error": "User not found"}), 404 
    
@main.route('/profile', methods=['GET', 'POST'])
@login_required  # Ensure the user is logged in
def profile():
    user = current_user  # Get the current user
    form = ProfileForm(obj=user)  # Populate form with current user data

    if form.validate_on_submit():
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('main.profile'))

    return render_template('profile.html', form=form, user=user)
 
@main.route('/leaderboard', methods=['GET'])
def leaderboard():
    return render_template('leaderboard.html')

@main.route('/leaderboards')
def leaderboard2():
    # Query the top users based on their quiz scores
    users = User.query.order_by(User.last_quiz_score.desc()).limit(10).all()
    
    # Prepare the data for the response
    leaderboard_data = [
        {
            'username': user.username,
            'fullname': f"{user.first_name} {user.last_name}",
            'points': user.last_quiz_score
        }
        for user in users
    ]
    
    return jsonify(leaderboard_data)


@main.route('/admin/users')
@login_required
def list_users():
    if current_user.role.name != 'Admin':
        abort(403)
    users = User.query.all()
    return render_template('list_users.html', users=users)

@main.errorhandler(403)
def forbidden(error):
    return render_template('403.html'), 403


@main.errorhandler(404)
def not_found():
    return render_template('404.html'), 404

@main.errorhandler(500)
def internal_error():
    return render_template('500.html'), 500

@main.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            role_id=form.role.data 
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('main.list_users'))
    return render_template('create_user.html', form=form)

# Route for creating a new role
@main.route('/roles/create', methods=['GET', 'POST'])
@login_required
def create_role():
    if request.method == 'POST':
        role_name = request.form['role_name']
        new_role = Role(name=role_name)
        db.session.add(new_role)
        db.session.commit()
        flash('Role created successfully!', 'success')
        return redirect(url_for('main.list_roles'))
    return render_template('create_role.html')

# Route for editing a role
@main.route('/roles/edit/<int:role_id>', methods=['GET', 'POST'])
@login_required
def edit_role(role_id):
    role = Role.query.get_or_404(role_id)
    if request.method == 'POST':
        role.name = request.form['role_name']
        db.session.commit()
        flash('Role updated successfully!', 'success')
        return redirect(url_for('main.list_roles'))
    return render_template('edit_role.html', role=role)

# Route for deleting a role
@main.route('/roles/delete/<int:role_id>', methods=['GET'])
@login_required
def delete_role(role_id):
    role = Role.query.get_or_404(role_id)
    db.session.delete(role)
    db.session.commit()
    flash('Role deleted successfully!', 'success')
    return redirect(url_for('main.list_roles'))

@main.route('/admin/roles')
@login_required
def list_roles():
    roles = Role.query.all()  # Retrieve all roles from the database
    return render_template('list_roles.html', roles=roles)
# Route for editing a user
@main.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserForm(obj=user)  # Pass the user object to the form
    if request.method == 'POST':
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.role_id = form.role.data  # Update user's ro

        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('main.list_users'))
    return render_template('edit_user.html',form=form, user=user)

# Route for deleting a user
@main.route('/users/delete/<int:user_id>', methods=['GET'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('main.list_users'))