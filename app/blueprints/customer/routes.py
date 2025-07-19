from flask import Blueprint, jsonify, request
from app.extensions import db
from app.models import Customer, ServiceTicket
from app.blueprints.customer.customerSchemas import CustomerSchema

customer_bp = Blueprint("customer", __name__, url_prefix="/customers")

# Schema instances
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


# Create a new customer
@customer_bp.route("/", methods=["POST"])
def create_customer():
    print("Incoming request:", request.get_json())

    data = request.get_json()

    if Customer.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already exists."}), 409
    try:
        new_customer = customer_schema.load(data)
        db.session.add(new_customer)
        db.session.commit()
        return customer_schema.jsonify(new_customer), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Get all customers
@customer_bp.route("/", methods=["GET"])
def get_customers():
    customers = Customer.query.all()
    return customers_schema.jsonify(customers), 200


# Get a single customer
@customer_bp.route("/<int:id>", methods=["GET"])
def get_customer(id):
    customer = Customer.query.get_or_404(id)
    return customer_schema.jsonify(customer), 200


# Update a customer
@customer_bp.route("/<int:id>", methods=["PUT"])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    data = request.get_json()

    try:
        customer.name = data.get("name", customer.name)
        customer.email = data.get("email", customer.email)
        customer.phone = data.get("phone", customer.phone)
        customer.address = data.get("address", customer.address)

        if "service_tickets" in data:
            ticket_ids = data["service_tickets"]  # Expecting list of ticket IDs
            customer.service_tickets = ServiceTicket.query.filter(
                ServiceTicket.id.in_(ticket_ids)
            ).all()

        db.session.commit()
        return customer_schema.jsonify(customer), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


# Delete a customer
@customer_bp.route("/<int:id>", methods=["DELETE"])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    try:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": f"Customer {id} deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
