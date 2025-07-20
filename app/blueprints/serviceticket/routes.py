from flask import Blueprint, jsonify, request
from app.extensions import db, cache
from app.models import (
    Inventory,
    InventoryServiceTicket,
    Mechanic,
    ServiceAssignment,
    ServiceTicket,
)
from app.blueprints.serviceticket.serviceTicketSchemas import ServiceTicketSchema
from app.utils.util import mechanic_token_required, token_required

service_ticket_bp = Blueprint("service_ticket", __name__, url_prefix="/service_tickets")

# Schema instances
service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)


@service_ticket_bp.route("/", methods=["POST"])
@token_required
def create_service_ticket(user_id):
    """
    Creates a new service ticket for the authenticated user.
    """
    if not user_id:
        return jsonify({"error": "Unauthorized to create a service ticket"}), 403
    data = request.get_json()
    try:
        new_ticket = service_ticket_schema.load(data)
        db.session.add(new_ticket)
        db.session.commit()
        return service_ticket_schema.jsonify(new_ticket), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@service_ticket_bp.route(
    "/<int:ticket_id>/assign-mechanic/<int:mechanic_id>", methods=["POST"]
)
def assign_mechanic(ticket_id, mechanic_id):
    """
    Assigns a mechanic to a service ticket.
    """
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    mechanic = Mechanic.query.get_or_404(mechanic_id)

    # Check if assignment already exists
    existing = ServiceAssignment.query.filter_by(
        service_ticket_id=ticket.id, mechanic_id=mechanic.id
    ).first()

    if not existing:
        assignment = ServiceAssignment(
            service_ticket_id=ticket.id, mechanic_id=mechanic.id
        )
        db.session.add(assignment)

    db.session.commit()

    updated_ticket = ServiceTicket.query.get(ticket_id)
    return service_ticket_schema.jsonify(updated_ticket), 200


@service_ticket_bp.route(
    "/<int:ticket_id>/remove-mechanic/<int:mechanic_id>", methods=["DELETE"]
)
def remove_mechanic(ticket_id, mechanic_id):
    """
    Removes a mechanic from a service ticket.
    """
    assignment = ServiceAssignment.query.filter_by(
        service_ticket_id=ticket_id, mechanic_id=mechanic_id
    ).first()

    if not assignment:
        return jsonify({"error": "Assignment not found"}), 404

    db.session.delete(assignment)
    db.session.commit()

    updated_ticket = ServiceTicket.query.get(ticket_id)
    return service_ticket_schema.jsonify(updated_ticket), 200


@service_ticket_bp.route("/<int:ticket_id>/edit", methods=["PUT"])
def edit_service_ticket(ticket_id):
    """
    Adds/removes mechanics from a service ticket.
    Body:
    {
        "add_ids": [1, 2],
        "remove_ids": [3]
    }
    """
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    data = request.get_json()

    add_ids = data.get("add_ids", [])
    remove_ids = data.get("remove_ids", [])

    try:
        # Add mechanics
        for mechanic_id in add_ids:
            existing = ServiceAssignment.query.filter_by(
                service_ticket_id=ticket.id, mechanic_id=mechanic_id
            ).first()
            if not existing:
                assignment = ServiceAssignment(
                    service_ticket_id=ticket.id, mechanic_id=mechanic_id
                )
                db.session.add(assignment)

        # Remove mechanics
        for mechanic_id in remove_ids:
            assignment = ServiceAssignment.query.filter_by(
                service_ticket_id=ticket.id, mechanic_id=mechanic_id
            ).first()
            if assignment:
                db.session.delete(assignment)

        db.session.commit()
        return service_ticket_schema.jsonify(ticket), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Get all service tickets
@service_ticket_bp.route("/", methods=["GET"])
@cache.cached(timeout=30)
def get_service_tickets():
    """
    Caching is important here because fetching all tickets is a
    **read-heavy operation**. Many clients may request the same data,
    so caching reduces redundant DB queries and speeds up response times.
    """
    tickets = ServiceTicket.query.all()
    return service_tickets_schema.jsonify(tickets), 200


@service_ticket_bp.route("/<int:ticket_id>/add-part", methods=["POST"])
@mechanic_token_required
def add_part_to_service_ticket(ticket_id):
    """
    Adds a part to a service ticket and increments quantity
    if the part is already linked.
    """
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    data = request.get_json()
    inventory_id = data.get("inventory_id")
    quantity = data.get("quantity", 1)

    if not inventory_id:
        return jsonify({"error": "Missing inventory_id in request body"}), 400

    part = Inventory.query.get_or_404(inventory_id)

    try:
        link = InventoryServiceTicket.query.filter_by(
            service_ticket_id=ticket.id, inventory_id=part.id
        ).first()

        if link:
            link.quantity += quantity
        else:
            link = InventoryServiceTicket(
                service_ticket_id=ticket.id, inventory_id=part.id, quantity=quantity
            )
            db.session.add(link)

        db.session.commit()

        updated_ticket = ServiceTicket.query.get(ticket_id)
        return service_ticket_schema.jsonify(updated_ticket), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
