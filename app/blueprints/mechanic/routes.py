from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import Mechanic, ServiceTicket
from app.blueprints.mechanic.mechanicSchemas import MechanicSchema


mechanic_bp = Blueprint("mechanic", __name__, url_prefix="/mechanics")

# Schema instances
mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)


# Create a new mechanic
@mechanic_bp.route("/", methods=["POST"])
def create_mechanic():
    data = request.get_json()
    try:
        new_mechanic = mechanic_schema.load(data)
        db.session.add(new_mechanic)
        db.session.commit()
        return mechanic_schema.jsonify(new_mechanic), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Get all mechanics
@mechanic_bp.route("/", methods=["GET"])
def get_mechanics():
    mechanics = Mechanic.query.all()
    return mechanics_schema.jsonify(mechanics), 200


# Updates a specific mechanic
@mechanic_bp.route("/<int:id>", methods=["PUT"])
def update_mechanic(id):
    mechanic = Mechanic.query.get_or_404(id)
    data = request.get_json()

    try:
        mechanic.name = data.get("name", mechanic.name)
        mechanic.email = data.get("email", mechanic.email)
        mechanic.phone = data.get("phone", mechanic.phone)
        mechanic.address = data.get("address", mechanic.address)
        mechanic.salary = data.get("salary", mechanic.salary)

        if "service_tickets" in data:
            ticket_ids = data["service_tickets"]
            mechanic.service_tickets = ServiceTicket.query.filter(
                ServiceTicket.id.in_(ticket_ids)
            ).all()

        db.session.commit()
        return mechanic_schema.jsonify(mechanic), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Delete a specific mechanic
@mechanic_bp.route("/<int:id>", methods=["DELETE"])
def delete_mechanic(id):
    mechanic = Mechanic.query.get_or_404(id)
    try:
        db.session.delete(mechanic)
        db.session.commit()
        return jsonify({"message": "Mechanic deleted successfully"}), 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
