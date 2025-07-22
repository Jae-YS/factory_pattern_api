from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db, limiter, cache
from app.models import (
    Inventory,
    InventoryAssignment,
    Mechanic,
    ServiceAssignment,
    ServiceStatus,
    ServiceTicket,
)
from app.blueprints.serviceticket.serviceTicketSchemas import ServiceTicketSchema
from app.utils.util import mechanic_token_required

service_ticket_bp = Blueprint("service_ticket", __name__, url_prefix="/service_ticket")

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
@mechanic_token_required
@limiter.limit("10 per hour")
def create_service_ticket(mechanic_id):
    """
    Creates a new service ticket and optionally assigns mechanics and parts.
    Only authenticated mechanics can create tickets.
    """
    data = request.get_json()

    mechanic_ids = data.pop("mechanic_ids", [])
    inventory_items = data.pop("inventory_items", [])

    if "customer_id" not in data:
        return jsonify({"error": "customer_id is required"}), 400

    if "status" not in data:
        data["status"] = "PENDING"

    try:
        new_ticket = service_ticket_schema.load(data)

        db.session.add(new_ticket)
        db.session.commit()

        for m_id in mechanic_ids:

            mechanic = db.session.get(Mechanic, m_id)
            if not mechanic:
                db.session.rollback()
                return jsonify({"error": f"Mechanic with ID {m_id} not found."}), 404

            assignment = ServiceAssignment(
                service_ticket_id=new_ticket.id, mechanic_id=m_id
            )
            db.session.add(assignment)

        db.session.commit()

        for item in inventory_items:
            inventory_id = item.get("inventory_id")
            quantity = item.get("quantity", 1)
            inventory = db.session.get(Inventory, inventory_id)
            if not inventory:
                db.session.rollback()
                return (
                    jsonify({"error": f"Inventory with ID {inventory_id} not found."}),
                    404,
                )

            link = db.session.execute(
                db.select(InventoryAssignment).filter_by(
                    service_ticket_id=new_ticket.id, inventory_id=inventory_id
                )
            ).scalar_one_or_none()

            if link:
                link.quantity += quantity
            else:
                link = InventoryAssignment(
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
@mechanic_token_required
@cache.cached(timeout=30)
def get_service_tickets(mechanic_id):
    """
    Retrieves all service tickets (with pagination support, cached for performance).
    Only authenticated mechanics can view tickets.
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
@mechanic_token_required
def get_service_ticket(mechanic_id, ticket_id):
    """
    Retrieves a specific service ticket by ID.
    Only authenticated mechanics can view tickets.
    """
    try:
        ticket = db.session.get(ServiceTicket, ticket_id)
        if not ticket:
            abort(404, description="Service ticket not found.")
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
def update_service_ticket(mechanic_id, ticket_id):
    """
    Updates a service ticket: add/remove mechanics, add/remove inventory parts, and update status.
    Only authenticated mechanics can perform updates. Only fields provided in the request will be updated.
    """
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        abort(404, description="Service ticket not found.")

    data = request.get_json()

    
    add_mechanics = data.pop("add_mechanics", None)
    remove_mechanics = data.pop("remove_mechanics", None)
    add_inventory = data.pop("add_inventory", None)
    remove_inventory = data.pop("remove_inventory", None)
    new_status = data.pop("status", None)

    try:
        service_ticket_schema.load(
            data, instance=ticket, session=db.session, partial=True
        )        
        if add_mechanics:
            for m_id in add_mechanics:
                if not db.session.execute(
                    db.select(ServiceAssignment).filter_by(
                        service_ticket_id=ticket.id, mechanic_id=m_id
                    )
                ).scalar_one_or_none():
                    mechanic = db.session.get(Mechanic, m_id)
                    if not mechanic:
                        return (
                            jsonify({"error": f"Mechanic with ID {m_id} not found."}),
                            404,
                        )
                    assignment = ServiceAssignment(
                        service_ticket_id=ticket.id, mechanic_id=m_id
                    )
                    db.session.add(assignment)

        if remove_mechanics:
            for m_id in remove_mechanics:
                assignment = db.session.execute(
                    db.select(ServiceAssignment).filter_by(
                        service_ticket_id=ticket.id, mechanic_id=m_id
                    )
                ).scalar_one_or_none()
                if assignment:
                    db.session.delete(assignment)

        
        if add_inventory:
            for item in add_inventory:
                inventory_id = item.get("inventory_id")
                quantity = item.get("quantity", 1)
                inventory = db.session.get(Inventory, inventory_id)
                if not inventory:
                    return (
                        jsonify(
                            {"error": f"Inventory with ID {inventory_id} not found."}
                        ),
                        404,
                    )

                link = db.session.execute(
                    db.select(InventoryAssignment).filter_by(
                        service_ticket_id=ticket.id, inventory_id=inventory_id
                    )
                ).scalar_one_or_none()

                if link:
                    link.quantity += quantity
                else:
                    link = InventoryAssignment(
                        service_ticket_id=ticket.id,
                        inventory_id=inventory_id,
                        quantity=quantity,
                    )
                    db.session.add(link)
     
        if remove_inventory:
            for inventory_id in remove_inventory:
                link = db.session.execute(
                    db.select(InventoryAssignment).filter_by(
                        service_ticket_id=ticket.id, inventory_id=inventory_id
                    )
                ).scalar_one_or_none()
                if link:
                    db.session.delete(link)

       
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
@mechanic_token_required
def delete_service_ticket(mechanic_id, ticket_id):
    """
    Deletes a service ticket.
    Only authenticated mechanics can delete tickets.
    """
    ticket = db.session.get(ServiceTicket, ticket_id)
    if not ticket:
        abort(404, description="Service ticket not found.")

    try:
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({"message": "Service ticket deleted successfully"}), 204
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
