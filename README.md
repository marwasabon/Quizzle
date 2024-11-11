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

## Project Structure

backend/ ├── app/ │ ├── init.py │ ├── models.py │ ├── routes/ │ │ ├── main.py │ │ └── auth.py │ ├── templates/ │ │ ├── base.html │ │ ├── login.html │ │ ├── register.html │ │ ├── profile.html │ │ ├── leaderboard.html │ │ ├── create_user.html │ │ └── edit_role.html │ └── static/ │ ├── css/ │ ├── js/ │ └── images/ ├── migrations/ ├── tests/ ├── config.py └── run.py
## Setup

### Prerequisites

- Python 3.10+
- Flask
- SQLite (or PostgreSQL for production)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/quizzle.git
   cd quizzle

    Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Set up the database:

flask db init
flask db migrate
flask db upgrade

Run the application:

    flask run

    Access the application at http://127.0.0.1:5000.

### Usage

    Login/Registration: Users can register and log in to access the quizzes.
    Quizzes: Select a topic and start a quiz. Answer multiple-choice questions and get immediate feedback.
    Profile: View your quiz history and performance insights.
    Admin Panel: Manage users and roles (accessible only to users with the 'Admin' role).

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
