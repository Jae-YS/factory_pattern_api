from flask import Flask, app
from dotenv import load_dotenv
from .extensions import db, ma
from .blueprints.customer.routes import customer_bp
from .blueprints.serviceticket.routes import service_ticket_bp
from .blueprints.mechanic.routes import mechanic_bp
from config import Config


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    ma.init_app(app)

    app.register_blueprint(customer_bp)
    app.register_blueprint(mechanic_bp)
    app.register_blueprint(service_ticket_bp)

    with app.app_context():
        db.create_all()

    print("🔗 Registered routes:")
    for rule in app.url_map.iter_rules():
        print(rule, rule.methods)

    return app
