from flask import Blueprint, jsonify, request
from sqlalchemy import func
from app.extensions import db, limiter
from app.models import Mechanic, ServiceTicket
from app.blueprints.mechanic.mechanicSchemas import MechanicSchema, MechanicLoginSchema
from app.utils.util import mechanic_token_required, encode_mechanic_token


mechanic_bp = Blueprint("mechanic", __name__, url_prefix="/mechanics")

# Schema instances
mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)
mechanic_login_schema = MechanicLoginSchema()


@mechanic_bp.route("/login", methods=["POST"])
def mechanic_login():
    """
    Logs in a mechanic and returns an authentication token.
    """
    try:
        credentials = mechanic_login_schema.load(request.get_json())
        email = credentials.get("email")
        password = credentials.get("password")
    except Exception as e:
        return jsonify({"error": "Invalid request format"}), 400

    mechanic = Mechanic.query.filter_by(email=email).first()

    if mechanic and mechanic.password == password:
        auth_token = encode_mechanic_token(mechanic.id)
        response = {
            "status": "success",
            "message": "Mechanic successfully logged in",
            "auth_token": auth_token,
        }
        return jsonify(response), 200
    else:
        return jsonify({"message": "Invalid email or password"}), 401


@mechanic_bp.route("/", methods=["POST"])
@limiter.limit("5 per hour")
def create_mechanic():
    """
    Rate limiting is important here because creating mechanics
    is a **write-heavy operation**. Limiting prevents abuse
    (like spamming thousands of mechanics) and protects DB performance.
    """
    data = request.get_json()
    try:
        new_mechanic = mechanic_schema.load(data)
        db.session.add(new_mechanic)
        db.session.commit()
        return mechanic_schema.jsonify(new_mechanic), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@mechanic_bp.route("/", methods=["GET"])
def get_mechanics():
    """
    Retrieves all mechanics.
    """
    mechanics = Mechanic.query.all()
    return mechanics_schema.jsonify(mechanics), 200


@mechanic_bp.route("/<int:id>", methods=["PUT"])
@mechanic_token_required
def update_mechanic(user_id, id):
    """
    Updates a specific mechanic's details.
    """
    if user_id != id:
        return jsonify({"error": "Unauthorized to update this user"}), 403
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


@mechanic_bp.route("/<int:id>", methods=["DELETE"])
@mechanic_token_required
def delete_mechanic(user_id, id):
    """
    Deletes a specific mechanic.
    """
    if user_id != id:
        return jsonify({"error": "Unauthorized to delete this user"}), 403
    mechanic = Mechanic.query.get_or_404(id)
    try:
        db.session.delete(mechanic)
        db.session.commit()
        return jsonify({"message": "Mechanic deleted successfully"}), 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@mechanic_bp.route("/rankings", methods=["GET"])
def get_mechanic_rankings():
    """
    Returns mechanics ordered by number of tickets they worked on.
    """
    rankings = (
        db.session.query(Mechanic, func.count(ServiceTicket.id).label("ticket_count"))
        .outerjoin(Mechanic.service_tickets)
        .group_by(Mechanic.id)
        .order_by(db.desc("ticket_count"))
        .all()
    )

    result = [
        {"mechanic": mechanic_schema.dump(mechanic), "ticket_count": count}
        for mechanic, count in rankings
    ]

    return jsonify(result), 200
