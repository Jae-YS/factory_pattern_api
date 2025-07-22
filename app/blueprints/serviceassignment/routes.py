from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import ServiceAssignment
from app.blueprints.serviceassignment.serviceAssignmentSchemas import (
    ServiceAssignmentSchema,
)
from app.utils.util import mechanic_token_required

service_assignment_bp = Blueprint(
    "service_assignment", __name__, url_prefix="/assignment"
)

# Schema instances
assignment_schema = ServiceAssignmentSchema()
assignments_schema = ServiceAssignmentSchema(many=True)


@service_assignment_bp.route("/", methods=["POST"])
@mechanic_token_required
def create_assignment():
    """
    Assign a mechanic to a service ticket.
    Body:
    {
        "service_ticket_id": 1,
        "mechanic_id": 2,
        "date_assigned": "2025-07-19"  # optional
    }
    """
    data = request.get_json()
    ticket_id = data.get("service_ticket_id")
    mechanic_id = data.get("mechanic_id")

    # Check if assignment already exists
    existing = ServiceAssignment.query.filter_by(
        service_ticket_id=ticket_id, mechanic_id=mechanic_id
    ).first()
    if existing:
        return jsonify({"error": "Assignment already exists"}), 400

    assignment = ServiceAssignment(**data)
    db.session.add(assignment)
    db.session.commit()
    return assignment_schema.jsonify(assignment), 201


@service_assignment_bp.route("/", methods=["GET"])
@mechanic_token_required
def get_all_assignments():
    """
    Get all mechanic-service ticket assignments.
    """
    assignments = ServiceAssignment.query.all()
    return assignments_schema.jsonify(assignments), 200


@service_assignment_bp.route("/", methods=["DELETE"])
@mechanic_token_required
def delete_assignment():
    """
    Remove a mechanic from a service ticket.
    Query params: ?service_ticket_id=1&mechanic_id=2
    """
    ticket_id = request.args.get("service_ticket_id")
    mechanic_id = request.args.get("mechanic_id")

    assignment = ServiceAssignment.query.filter_by(
        service_ticket_id=ticket_id, mechanic_id=mechanic_id
    ).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"message": "Assignment deleted successfully"}), 200
