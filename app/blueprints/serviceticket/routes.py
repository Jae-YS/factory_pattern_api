from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import Mechanic, ServiceTicket
from app.blueprints.serviceticket.serviceTicketSchemas import ServiceTicketSchema

service_ticket_bp = Blueprint("service_ticket", __name__, url_prefix="/service_tickets")

# Schema instances
service_ticket_schema = ServiceTicketSchema()
service_tickets_schema = ServiceTicketSchema(many=True)


# Create a new service ticket
@service_ticket_bp.route("/", methods=["POST"])
def create_service_ticket():
    data = request.get_json()
    try:
        new_ticket = service_ticket_schema.load(data)
        db.session.add(new_ticket)
        db.session.commit()
        return service_ticket_schema.jsonify(new_ticket), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Adds a relationship between a service ticket and a mechanic
@service_ticket_bp.route(
    "/<int:ticket_id>/assign-mechanic/<int:mechanic_id>", methods=["PUT"]
)
def add_mechanic_to_ticket(ticket_id, mechanic_id):
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    mechanic = Mechanic.query.get_or_404(mechanic_id)

    try:
        if mechanic not in ticket.mechanics:
            ticket.mechanics.append(mechanic)

        db.session.commit()
        return service_ticket_schema.jsonify(ticket), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Removes the relationship from a service ticket and the mechanic
@service_ticket_bp.route(
    "/<int:ticket_id>/remove-mechanic/<int:mechanic_id>", methods=["PUT"]
)
def remove_mechanic_from_ticket(ticket_id, mechanic_id):
    ticket = ServiceTicket.query.get_or_404(ticket_id)
    mechanic = Mechanic.query.get_or_404(mechanic_id)

    try:
        # Remove mechanic from the relationship list
        if mechanic in ticket.mechanics:
            ticket.mechanics.remove(mechanic)

        db.session.commit()
        return service_ticket_schema.jsonify(ticket), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Get all service tickets
@service_ticket_bp.route("/", methods=["GET"])
def get_service_tickets():
    tickets = ServiceTicket.query.all()
    return service_tickets_schema.jsonify(tickets), 200
