from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from app.extensions import db, limiter
from app.models import Mechanic, ServiceAssignment, ServiceTicket
from app.blueprints.mechanic.mechanicSchemas import MechanicSchema, MechanicLoginSchema
from app.utils.util import mechanic_token_required, encode_mechanic_token

mechanic_bp = Blueprint("mechanic", __name__, url_prefix="/mechanic")

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
    except Exception:
        return jsonify({"error": "Invalid request format"}), 400

    mechanic = db.session.execute(
        db.select(Mechanic).filter_by(email=email)
    ).scalar_one_or_none()

    if mechanic and mechanic.check_password(password):
        auth_token = encode_mechanic_token(mechanic.id)
        response = {
            "status": "success",
            "message": "Mechanic successfully logged in",
            "auth_token": auth_token,
        }
        return jsonify(response), 200

    return jsonify({"error": "Invalid email or password"}), 401


@mechanic_bp.route("/", methods=["POST"])
@limiter.limit("5 per hour")
def create_mechanic():
    """
    Creates a new mechanic (with hashed password).
    """
    try:
        data = request.get_json()
        existing_mechanic = db.session.execute(
            db.select(Mechanic).filter_by(email=data.get("email"))
        ).scalar_one_or_none()
        if existing_mechanic:
            return jsonify({"error": "Email already exists."}), 409

        new_mechanic = mechanic_schema.load(data)
        db.session.add(new_mechanic)
        db.session.commit()
        return mechanic_schema.jsonify(new_mechanic), 201
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400


@mechanic_bp.route("/", methods=["GET"])
def get_mechanics():
    """
    Retrieves all mechanics (with pagination support).
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = Mechanic.query.paginate(page=page, per_page=per_page, error_out=False)
    mechanics = pagination.items

    response = {
        "mechanics": mechanics_schema.dump(mechanics),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }
    return jsonify(response), 200


@mechanic_bp.route("/<int:id>", methods=["GET"])
@mechanic_token_required
def get_mechanic(user_id, id):
    """
    Retrieves a specific mechanic by ID.
    """
    if str(user_id) != str(id):
        return jsonify({"error": "Unauthorized to access this user"}), 403

    mechanic = db.session.get(Mechanic, id)
    if not mechanic:
        abort(404, description="Mechanic not found.")
    return mechanic_schema.jsonify(mechanic), 200


@mechanic_bp.route("/<int:id>", methods=["PUT"])
@mechanic_token_required
def update_mechanic(user_id, id):
    """
    Updates a mechanic by ID (only self).
    """
    if str(user_id) != str(id):
        return jsonify({"error": "Unauthorized to update this user"}), 403

    mechanic = db.session.get(Mechanic, id)
    if not mechanic:
        abort(404, description="Mechanic not found.")

    try:
        data = request.get_json()

        if "password" in data:
            mechanic.set_password(data["password"])

        mechanic.name = data.get("name", mechanic.name)
        mechanic.email = data.get("email", mechanic.email)
        mechanic.phone = data.get("phone", mechanic.phone)
        mechanic.address = data.get("address", mechanic.address)
        mechanic.salary = data.get("salary", mechanic.salary)

        if "service_ticket_ids" in data:
            mechanic.service_assignments.clear()
            for ticket_id in data["service_ticket_ids"]:
                assignment = ServiceAssignment(
                    service_ticket_id=ticket_id, mechanic_id=mechanic.id
                )
                db.session.add(assignment)

        db.session.commit()
        return mechanic_schema.jsonify(mechanic), 200

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400


@mechanic_bp.route("/<int:id>", methods=["DELETE"])
@mechanic_token_required
def delete_mechanic(user_id, id):
    """
    Deletes a specific mechanic (only self).
    """
    if str(user_id) != str(id):
        return jsonify({"error": "Unauthorized to delete this user"}), 403

    mechanic = db.session.get(Mechanic, id)
    if not mechanic:
        abort(404, description="Mechanic not found.")
    try:
        db.session.delete(mechanic)
        db.session.commit()
        return jsonify({"message": "Mechanic deleted successfully"}), 204
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500


@mechanic_bp.route("/rankings", methods=["GET"])
def get_mechanic_rankings():
    """
    Returns mechanics ordered by the number of tickets they worked on.
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
