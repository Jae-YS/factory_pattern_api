from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db, limiter, cache
from app.models import (
    Inventory,
    InventoryServiceTicket,
    Mechanic,
    ServiceAssignment,
    ServiceStatus,
    ServiceTicket,
)
from app.blueprints.serviceticket.serviceTicketSchemas import ServiceTicketSchema
from app.utils.util import mechanic_token_required, token_required

service_ticket_bp = Blueprint("service_ticket", __name__, url_prefix="/service_tickets")

# Schema instances
service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)


def parse_status(status_str):
    """
    Helper function to safely parse a status string into ServiceStatus enum.
    """
    try:
        return ServiceStatus[status_str.upper()]
    except (KeyError, AttributeError):
        valid_statuses = [e.name for e in ServiceStatus]
        raise ValueError(
            f"Invalid status '{status_str}'. Allowed values: {valid_statuses}"
        )


@service_ticket_bp.route("/", methods=["POST"])
@token_required
@limiter.limit("10 per hour")
def create_service_ticket(user_id):
    """
    Creates a new service ticket for the authenticated user and optionally assigns mechanics and parts.
    """
    if not user_id:
        return jsonify({"error": "Unauthorized to create a service ticket"}), 403

    data = request.get_json()

    mechanic_ids = data.pop("mechanic_ids", [])
    inventory_items = data.pop("inventory_items", [])

    if "status" not in data:
        data["status"] = ServiceStatus.PENDING.name
    else:
        try:
            data["status"] = parse_status(data["status"])
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400

    try:
        new_ticket = service_ticket_schema.load(data)
        db.session.add(new_ticket)
        db.session.commit()

        for mechanic_id in mechanic_ids:
            mechanic = Mechanic.query.get(mechanic_id)
            if not mechanic:
                db.session.rollback()
                return (
                    jsonify({"error": f"Mechanic with ID {mechanic_id} not found."}),
                    404,
                )
            assignment = ServiceAssignment(
                service_ticket_id=new_ticket.id, mechanic_id=mechanic_id
            )
            db.session.add(assignment)

        for item in inventory_items:
            inventory_id = item.get("inventory_id")
            quantity = item.get("quantity", 1)
            inventory = Inventory.query.get(inventory_id)
            if not inventory:
                db.session.rollback()
                return (
                    jsonify({"error": f"Inventory with ID {inventory_id} not found."}),
                    404,
                )

            link = InventoryServiceTicket.query.filter_by(
                service_ticket_id=new_ticket.id, inventory_id=inventory_id
            ).first()

            if link:
                link.quantity += quantity
            else:
                link = InventoryServiceTicket(
                    service_ticket_id=new_ticket.id,
                    inventory_id=inventory_id,
                    quantity=quantity,
                )
                db.session.add(link)

        db.session.commit()

        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Service ticket created successfully",
                    "ticket": service_ticket_schema.dump(new_ticket),
                }
            ),
            201,
        )

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400


@service_ticket_bp.route("/", methods=["GET"])
@cache.cached(timeout=30)
def get_service_tickets():
    """
    Retrieves all service tickets (with pagination support, cached for performance).
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    try:
        pagination = ServiceTicket.query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        tickets = pagination.items

        response = {
            "service_tickets": service_tickets_schema.dump(tickets),
            "total": pagination.total,
            "page": pagination.page,
            "per_page": pagination.per_page,
            "pages": pagination.pages,
        }
        return jsonify(response), 200
    except SQLAlchemyError:
        return jsonify({"error": "Database error occurred"}), 500


@service_ticket_bp.route("/<int:ticket_id>", methods=["GET"])
def get_service_ticket(ticket_id):
    """
    Retrieves a specific service ticket by ID.
    """
    try:
        ticket = ServiceTicket.query.get_or_404(ticket_id)
        return (
            jsonify(
                {"status": "success", "ticket": service_ticket_schema.dump(ticket)}
            ),
            200,
        )
    except SQLAlchemyError:
        return jsonify({"error": "Database error occurred"}), 500


@service_ticket_bp.route("/<int:ticket_id>", methods=["PUT"])
@mechanic_token_required
def update_service_ticket(ticket_id):
    """
    Updates a service ticket: add/remove mechanics, add/remove inventory parts, and update status.

    Example request body:
    {
        "add_mechanics": [1, 2],
        "remove_mechanics": [3],
        "add_inventory": [
            {"inventory_id": 1, "quantity": 2},
            {"inventory_id": 4, "quantity": 1}
        ],
        "remove_inventory": [2],
        "status": "COMPLETED"
    }
    """
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    data = request.get_json()

    add_mechanics = data.get("add_mechanics", [])
    remove_mechanics = data.get("remove_mechanics", [])
    add_inventory = data.get("add_inventory", [])
    remove_inventory = data.get("remove_inventory", [])
    new_status = data.get("status")

    try:
        # ✅ Add mechanics
        for mechanic_id in add_mechanics:
            if not ServiceAssignment.query.filter_by(
                service_ticket_id=ticket.id, mechanic_id=mechanic_id
            ).first():
                mechanic = Mechanic.query.get(mechanic_id)
                if not mechanic:
                    return (
                        jsonify(
                            {"error": f"Mechanic with ID {mechanic_id} not found."}
                        ),
                        404,
                    )
                assignment = ServiceAssignment(
                    service_ticket_id=ticket.id, mechanic_id=mechanic_id
                )
                db.session.add(assignment)

        # ✅ Remove mechanics
        for mechanic_id in remove_mechanics:
            assignment = ServiceAssignment.query.filter_by(
                service_ticket_id=ticket.id, mechanic_id=mechanic_id
            ).first()
            if assignment:
                db.session.delete(assignment)

        # ✅ Add inventory parts
        for item in add_inventory:
            inventory_id = item.get("inventory_id")
            quantity = item.get("quantity", 1)
            inventory = Inventory.query.get(inventory_id)
            if not inventory:
                return (
                    jsonify({"error": f"Inventory with ID {inventory_id} not found."}),
                    404,
                )

            link = InventoryServiceTicket.query.filter_by(
                service_ticket_id=ticket.id, inventory_id=inventory_id
            ).first()

            if link:
                link.quantity += quantity
            else:
                link = InventoryServiceTicket(
                    service_ticket_id=ticket.id,
                    inventory_id=inventory_id,
                    quantity=quantity,
                )
                db.session.add(link)

        # ✅ Remove inventory parts
        for inventory_id in remove_inventory:
            link = InventoryServiceTicket.query.filter_by(
                service_ticket_id=ticket.id, inventory_id=inventory_id
            ).first()
            if link:
                db.session.delete(link)

        # ✅ Update status if provided
        if new_status:
            ticket.status = parse_status(new_status)

        db.session.commit()
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Service ticket updated successfully",
                    "ticket": service_ticket_schema.dump(ticket),
                }
            ),
            200,
        )

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400


@service_ticket_bp.route("/<int:ticket_id>", methods=["DELETE"])
def delete_service_ticket(ticket_id):
    """
    Deletes a service ticket.
    """
    ticket = ServiceTicket.query.get_or_404(ticket_id)

    try:
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({"message": "Service ticket deleted successfully"}), 204
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
