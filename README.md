# Quizzle

Quizzle is a dynamic and interactive quiz platform where users can challenge themselves with quizzes across various topics, track their performance, and compete with others. With a user-friendly interface and robust backend, Quizzle offers a seamless experience for users looking to learn, compete, and have fun.

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Database Structure](#database-structure)
- [Future Improvements](#future-improvements)

## Features

1. **User Authentication and Authorization**
   - Secure login and registration with password hashing.
   - Role-based access control (Admin, User).
   - Persistent session handling with Flask-Login.

2. **Quiz Management**
   - Users can start quizzes based on categories (e.g., Science, History).
   - Dynamic quiz question generation using the Gemini AI API.
   - Track and display quiz history for each user, including attempts, successes, and failures.

3. **Leaderboard**
   - Global leaderboard displaying top users based on quiz scores.
   - Users can view their ranking and compare their performance with others.

4. **User Profile**
   - Detailed user profile page showing personal details and quiz history.
   - Valuable insights based on quiz performance (success rate, most attempted topics, etc.).

5. **Admin Features**
   - Manage users: Create, edit, and delete user accounts.
   - Manage roles: Create, edit, and delete user roles.
   - View user activity logs and quiz history.

6. **Error Handling**
   - Custom 404 and 403 error pages for a better user experience.
   - Global error handling for invalid URLs.

## Technologies Used

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, Bootstrap, JavaScript
- **Database**: SQLite (or PostgreSQL for production)
- **APIs**: Gemini AI for dynamic quiz question generation
- **Authentication**: Flask-Login
- **Templating Engine**: Jinja2
  
## contributors 

Emmanuel Asante Email:manuelasantempire@gmail.com
Marwa Sabon : marwasabon@gmail.com

## Project Structure

backend/ ├── app/ │ ├── init.py │ ├── models.py │ ├── routes/ │ │ ├── main.py │ │ └── auth.py │ ├── templates/ │ │ ├── base.html │ │ ├── login.html │ │ ├── register.html │ │ ├── profile.html │ │ ├── leaderboard.html │ │ ├── create_user.html │ │ └── edit_role.html │ └── static/ │ ├── css/ │ ├── js/ │ └── images/ ├── migrations/ ├── tests/ ├── config.py └── run.py
## Setup

### Prerequisites

- Python 3.10 or newer
- MySQL Server
- Access to the MySQL database configured in `backend/app/config.py`
- A Gemini API key is optional. If Gemini is unavailable, the application uses local default quiz questions.

### Windows PowerShell installation

From the repository root:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell activation is blocked, use the virtual environment directly instead:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Configure the database

Create the `quizzle` database in MySQL and update the database URI in
`backend/app/config.py` if necessary. The MySQL server must be running and
reachable before starting the application.

From the repository root, change to the `backend` directory and create the
tables from the SQLAlchemy models:

```powershell
cd backend
..\.venv\Scripts\python.exe -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"
```

Seed the default roles required by registration and administrator access:

```powershell
..\.venv\Scripts\flask.exe --app "app:create_app" seed-roles
```

The command creates `Admin` and `User` only when they do not already exist.

### Run the application

From the `backend` directory:

```powershell
..\.venv\Scripts\flask.exe --app "app:create_app" run
```

For debug mode:

```powershell
..\.venv\Scripts\flask.exe --app "app:create_app" --debug run
```

Open the application at <http://127.0.0.1:5000>.

### Register and log in

1. Open <http://127.0.0.1:5000/register>.
2. Enter a username, email address, first name, last name, and password.
3. Select a role. The default roles are `Admin` and `User`.
4. Submit the registration form.
5. Open <http://127.0.0.1:5000/login> and sign in with the new credentials.
6. Open a quiz category and generate a question.

The registration form requires an email address and validates the password
confirmation. The account is stored in the MySQL `user` table.

### Usage

- **Quizzes:** Select a topic and answer multiple-choice questions.
- **Fallback quizzes:** If the Gemini API is unavailable, built-in questions are used automatically.
- **Profile:** View your quiz history and performance insights.
- **Admin features:** Accounts assigned the `Admin` role can manage users and roles.

### API Endpoints

    User Management
        GET /admin/users - List all users (Admin only)
        POST /admin/users/create - Create a new user (Admin only)
        POST /admin/users/edit/<user_id> - Edit a user (Admin only)
        POST /admin/users/delete/<user_id> - Delete a user (Admin only)

    Quiz Management
        GET /start_quiz/<category> - Start a quiz based on the selected category
        POST /submit_quiz - Submit quiz answers and get results

    Leaderboard
        GET /leaderboard - View the global leaderboard

### Database Structure
Users Table

    id: Primary key
    username: Unique username
    email: User email
    first_name: User's first name
    last_name: User's last name
    role_id: Foreign key to Roles table
    password_hash: Hashed password

Roles Table

    id: Primary key
    name: Role name (e.g., Admin, User)

Quizzes Table

    id: Primary key
    user_id: Foreign key to Users table
    topic: Quiz topic (e.g., Science, History)
    score: Quiz score
    date_taken: Timestamp of when the quiz was taken

Future Improvements

    Enhanced Question Generation: Improve the dynamic question generation using advanced filters with the Gemini AI API.
    Real-Time Leaderboard: Add WebSocket support for real-time leaderboard updates.
    Additional Quiz Types: Implement different quiz formats (e.g., true/false, fill-in-the-blank).
    User Analytics: Provide more detailed analytics on user performance and trends.

Contribution

We welcome contributions from the community! To contribute:

    Fork the repository.
    Create a new branch: git checkout -b feature/your-feature.
    Commit your changes: git commit -m 'Add your feature'.
    Push to the branch: git push origin feature/your-feature.
    Open a pull request.

License

This project is licensed under the MIT License. See the LICENSE file for more information.
Contact

For questions or suggestions, feel free to reach out:

    Email: marwasabon@gmail.com
    GitHub: marwasabon
