from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import InventoryServiceTicket, Inventory, ServiceTicket
from app.blueprints.inventoryassignment.inventoryAssignmentSchemas import (
    InventoryAssignmentSchema,
)

inventory_assignment_bp = Blueprint(
    "inventory_assignment", __name__, url_prefix="/inventory_assignments"
)

# Schema instances
assignment_schema = InventoryAssignmentSchema()
assignments_schema = InventoryAssignmentSchema(many=True)


@inventory_assignment_bp.route("/", methods=["POST"])
def create_inventory_assignment():
    """
    Assign an inventory part to a service ticket.
    """
    data = request.get_json()
    ticket_id = data.get("service_ticket_id")
    inventory_id = data.get("inventory_id")
    quantity = data.get("quantity", 1)

    # Check if assignment already exists
    existing = InventoryServiceTicket.query.filter_by(
        service_ticket_id=ticket_id, inventory_id=inventory_id
    ).first()
    if existing:
        return jsonify({"error": "Inventory item already assigned"}), 400

    assignment = InventoryServiceTicket(**data)
    db.session.add(assignment)
    db.session.commit()
    return assignment_schema.jsonify(assignment), 201


@inventory_assignment_bp.route("/", methods=["GET"])
def get_all_inventory_assignments():
    """
    Get all inventory-service ticket assignments.
    """
    assignments = InventoryServiceTicket.query.all()
    return assignments_schema.jsonify(assignments), 200


@inventory_assignment_bp.route("/", methods=["PUT"])
def update_inventory_assignment():
    """
    Update the quantity of an inventory assignment.
    """
    data = request.get_json()
    ticket_id = data.get("service_ticket_id")
    inventory_id = data.get("inventory_id")
    quantity = data.get("quantity")

    assignment = InventoryServiceTicket.query.filter_by(
        service_ticket_id=ticket_id, inventory_id=inventory_id
    ).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    assignment.quantity = quantity
    db.session.commit()
    return assignment_schema.jsonify(assignment), 200


@inventory_assignment_bp.route("/", methods=["DELETE"])
def delete_inventory_assignment():
    """
    Remove an inventory item from a service ticket.
    Query params: ?service_ticket_id=1&inventory_id=2
    """
    ticket_id = request.args.get("service_ticket_id")
    inventory_id = request.args.get("inventory_id")

    assignment = InventoryServiceTicket.query.filter_by(
        service_ticket_id=ticket_id, inventory_id=inventory_id
    ).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    db.session.delete(assignment)
    db.session.commit()
    return jsonify({"message": "Inventory assignment deleted successfully"}), 200
