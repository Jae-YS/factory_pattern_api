import select
from flask import Blueprint, jsonify, request
from app.extensions import db, limiter, cache
from app.models import Customer, ServiceTicket
from app.blueprints.customer.customerSchemas import CustomerSchema, LoginSchema
from app.blueprints.serviceticket.serviceTicketSchemas import ServiceTicketSchema
from app.utils.util import encode_token, token_required

customer_bp = Blueprint("customer", __name__, url_prefix="/customers")

# Schema instances
login_schema = LoginSchema()
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)


@customer_bp.route("/login", methods=["POST"])
def login():
    try:
        credentials = login_schema.load(request.get_json())
        email = credentials.get("email")
        password = credentials.get("password")
    except Exception as e:
        return jsonify({"error": "Invalid request format"}), 400

    query = select(Customer).where(Customer.email == email)
    user = db.session.execute(query).scalar_one_or_none()
    if user and user.password == password:
        auth_token = encode_token(user.id, user.email)

        response = {
            "status": "success",
            "message": "Successfully Logged In",
            "auth_token": auth_token,
        }
        return jsonify(response), 200
    else:
        return jsonify({"messages": "Invalid email or password"}), 401


@customer_bp.route("/", methods=["DELETE"])
@token_required
def delete_user(user_id):  # Receiving user_id from the token
    query = select(Customer).where(Customer.id == user_id)
    user = db.session.execute(query).scalars().first()

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"Successfully deleted user {user_id}"}), 200
    else:
        return jsonify({"message": f"User {user_id} not found"}), 404


@customer_bp.route("/my-tickets", methods=["GET"])
@token_required
def get_my_tickets(user_id):
    """
    Returns service tickets for the authenticated customer.
    """
    tickets = ServiceTicket.query.filter_by(customer_id=user_id).all()
    return ServiceTicketSchema.jsonify(tickets), 200


# Create a new customer
@customer_bp.route("/", methods=["POST"])
@limiter.limit("3 per hour")
@cache.cached(timeout=60)
def create_customer():
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
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    pagination = Customer.query.paginate(page=page, per_page=per_page, error_out=False)
    customers = pagination.items

    response = {
        "customers": customers_schema.dump(customers),
        "total": pagination.total,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "pages": pagination.pages,
    }
    return jsonify(response), 200


# Get a single customer
@customer_bp.route("/<int:id>", methods=["GET"])
def get_customer(id):
    customer = Customer.query.get_or_404(id)
    return customer_schema.jsonify(customer), 200


# Update a customer
@customer_bp.route("/<int:id>", methods=["PUT"])
@token_required
def update_customer(user_id, id):
    if user_id != id:
        return jsonify({"error": "Unauthorized to update this user"}), 403
    customer = Customer.query.get_or_404(id)
    data = request.get_json()

    try:
        customer.username = data.get("username", customer.username)
        customer.password = data.get("password", customer.password)
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
@token_required
def delete_customer(user_id, id):
    if user_id != id:
        return jsonify({"error": "Unauthorized to delete this user"}), 403

    customer = Customer.query.get_or_404(id)
    try:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": f"Customer {id} deleted"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
