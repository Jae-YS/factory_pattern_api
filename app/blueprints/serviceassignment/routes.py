import datetime
from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import select
from app.extensions import db
from app.models import ServiceAssignment
from app.blueprints.serviceassignment.serviceAssignmentSchemas import (
    ServiceAssignmentSchema,
)
from app.utils.util import mechanic_token_required

service_assignment_bp = Blueprint(
    "service_assignment", __name__, url_prefix="/service_assignment"
)

# Schema instances
assignment_schema = ServiceAssignmentSchema()
assignments_schema = ServiceAssignmentSchema(many=True)


@service_assignment_bp.route("/", methods=["POST"])
@mechanic_token_required
def create_assignment(mechanic_id):
    """
    Assign a mechanic to a service ticket.
    Body:
    {
        "service_ticket_id": 1,
        "mechanic_id": 2,
        "date_assigned": "2025-07-19"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No input data provided"}), 400

    ticket_id = data.get("service_ticket_id")
    mechanic_id = data.get("mechanic_id")

    if "date_assigned" in data and isinstance(data["date_assigned"], str):
        try:
            data["date_assigned"] = datetime.datetime.strptime(
                data["date_assigned"], "%Y-%m-%d"
            ).date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    try:
        stmt = select(ServiceAssignment).filter_by(
            service_ticket_id=ticket_id, mechanic_id=mechanic_id
        )
        existing = db.session.execute(stmt).scalar_one_or_none()
        if existing:
            return jsonify({"error": "Assignment already exists"}), 400

        assignment = ServiceAssignment(**data)
        db.session.add(assignment)
        db.session.commit()
        return assignment_schema.jsonify(assignment), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@service_assignment_bp.route("/", methods=["GET"])
@mechanic_token_required
def get_all_assignments(mechanic_id):
    """
    Get all mechanic-service ticket assignments.
    """
    try:
        stmt = select(ServiceAssignment)
        assignments = db.session.scalars(stmt).all()
        return assignments_schema.jsonify(assignments), 200
    except SQLAlchemyError as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500


@service_assignment_bp.route("/", methods=["DELETE"])
@mechanic_token_required
def delete_assignment(mechanic_id):
    """
    Remove a mechanic from a service ticket.
    Query params: ?service_ticket_id=1&mechanic_id=2
    """
    ticket_id = request.args.get("service_ticket_id")
    mechanic_id = request.args.get("mechanic_id")

    if not ticket_id or not mechanic_id:
        return jsonify({"error": "Missing service_ticket_id or mechanic_id"}), 400

    try:
        stmt = select(ServiceAssignment).filter_by(
            service_ticket_id=ticket_id, mechanic_id=mechanic_id
        )
        assignment = db.session.execute(stmt).scalar_one_or_none()

        if not assignment:
            return jsonify({"error": "Assignment not found"}), 404

        db.session.delete(assignment)
        db.session.commit()
        return jsonify({"message": "Assignment deleted successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}"}), 500
