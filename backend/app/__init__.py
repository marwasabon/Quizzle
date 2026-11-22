from flask import Flask, render_template
from flask_cors import CORS
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate

from .config import Config
from .models import db
from .models.quizz import PendingQuestion, Quiz  # noqa: F401  (register tables)
from .models.role import Role
from .models.user import User

mail = Mail()
login_manager = LoginManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    CORS(app)

    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('403.html'), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    @app.cli.command('seed-roles')
    def seed_roles():
        """Create the default application roles if they do not exist."""
        db.create_all()
        created_roles = []
        for role_name in ('Admin', 'User'):
            if Role.query.filter_by(name=role_name).first() is None:
                db.session.add(Role(name=role_name))
                created_roles.append(role_name)

        db.session.commit()
        if created_roles:
            print(f"Created roles: {', '.join(created_roles)}")
        else:
            print('Default roles already exist.')

    return app
