import os
from flask import Flask
from dotenv import load_dotenv

from .extensions import db, ma, limiter, cache, migrate
from .blueprints.customer.routes import customer_bp
from .blueprints.serviceticket.routes import service_ticket_bp
from .blueprints.mechanic.routes import mechanic_bp
from .blueprints.inventory.routes import inventory_bp
from .blueprints.serviceassignment.routes import service_assignment_bp
from .blueprints.inventoryassignment.routes import inventory_assignment_bp
from flask_swagger_ui import get_swaggerui_blueprint

SWAGGER_URL = "/api/docs"

if os.getenv("FLASK_ENV") == "production":
    API_URL = "https://mechanic-api-uwqv.onrender.com/static/bundled.yaml"
else:
    API_URL = "/static/bundled.yaml"
    
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Your API Docs", "validatorUrl": None},
)


def create_app(config_name=None):
    load_dotenv()

    app = Flask(__name__)

    if config_name == "testing":
        app.config.from_object("config.TestingConfig")
    elif config_name == "development":
        app.config.from_object("config.DevelopmentConfig")
    else:
        app.config.from_object("config.ProductionConfig")

    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(customer_bp)
    app.register_blueprint(mechanic_bp)
    app.register_blueprint(service_ticket_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(inventory_assignment_bp)
    app.register_blueprint(service_assignment_bp)
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    with app.app_context():
        db.create_all()

    return app
