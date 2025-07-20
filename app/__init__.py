from flask import Flask
from dotenv import load_dotenv
from .extensions import db, ma, limiter, cache
from .blueprints.customer.routes import customer_bp
from .blueprints.serviceticket.routes import service_ticket_bp
from .blueprints.mechanic.routes import mechanic_bp
from .blueprints.inventory.routes import inventory_bp
from .blueprints.serviceassignment.routes import service_assignment_bp
from config import Config


def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(customer_bp)
    app.register_blueprint(mechanic_bp)
    app.register_blueprint(service_ticket_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(service_assignment_bp)

    cache.init_app(app)

    with app.app_context():

        db.create_all()

    return app
