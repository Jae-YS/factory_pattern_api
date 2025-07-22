from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import InventoryAssignment
from app.blueprints.inventoryassignment.inventoryAssignmentSchemas import (
    InventoryAssignmentSchema,
)
from app.utils.util import mechanic_token_required

inventory_assignment_bp = Blueprint(
    "inventory_assignment", __name__, url_prefix="/inventory_assignment"
)

# Schema instances
assignment_schema = InventoryAssignmentSchema()
assignments_schema = InventoryAssignmentSchema(many=True)


@inventory_assignment_bp.route("/", methods=["POST"])
@mechanic_token_required
def create_inventory_assignment(mechanic_id):
    """
    Assign an inventory part to a service ticket.
    """
    data = request.get_json()
    ticket_id = data.get("service_ticket_id")
    inventory_id = data.get("inventory_id")
    quantity = data.get("quantity", 1)
    data["quantity"] = quantity

    existing = db.session.execute(
        db.select(InventoryAssignment).filter_by(
            service_ticket_id=ticket_id, inventory_id=inventory_id
        )
    ).scalar_one_or_none()

    if existing:
        return jsonify({"error": "Inventory item already assigned"}), 400

    assignment = InventoryAssignment(**data)
    db.session.add(assignment)
    db.session.commit()
    return assignment_schema.jsonify(assignment), 201


@inventory_assignment_bp.route("/", methods=["GET"])
@mechanic_token_required
def get_all_inventory_assignments(mechanic_id):
    """
    Get all inventory-service ticket assignments.
    """
    assignments = db.session.scalars(
        db.select(InventoryAssignment)
    ).all()
    return assignments_schema.jsonify(assignments), 200


@inventory_assignment_bp.route("/", methods=["PUT"])
@mechanic_token_required
def update_inventory_assignment(mechanic_id):
    """
    Update the quantity of an inventory assignment.
    """
    data = request.get_json()
    ticket_id = data.get("service_ticket_id")
    inventory_id = data.get("inventory_id")
    quantity = data.get("quantity")

    assignment = db.session.execute(
        db.select(InventoryAssignment).filter_by(
            service_ticket_id=ticket_id, inventory_id=inventory_id
        )
    ).scalar_one_or_none()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    assignment.quantity = quantity
    db.session.commit()
    return assignment_schema.jsonify(assignment), 200


@inventory_assignment_bp.route("/", methods=["DELETE"])
@mechanic_token_required
def delete_inventory_assignment(mechanic_id):
    """
    Remove an inventory item from a service ticket.
    Query params: ?service_ticket_id=1&inventory_id=2
    """
    ticket_id = request.args.get("service_ticket_id")
    inventory_id = request.args.get("inventory_id")

    assignment = db.session.execute(
        db.select(InventoryAssignment).filter_by(
            service_ticket_id=ticket_id, inventory_id=inventory_id
        )
    ).scalar_one_or_none()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"message": "Inventory assignment deleted successfully"}), 200
