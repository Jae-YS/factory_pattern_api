from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db, limiter, cache
from app.models import Customer, ServiceTicket
from app.blueprints.customer.customerSchemas import CustomerSchema, LoginSchema
from app.blueprints.serviceticket.serviceTicketSchemas import ServiceTicketSchema
from app.utils.util import encode_token, token_required

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")

# Schema instances
login_schema = LoginSchema()
customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
tickets_schema = ServiceTicketSchema(many=True)


@customer_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    """
    Customer login endpoint.
    """
    try:
        credentials = login_schema.load(request.get_json())
        email = credentials.get("email")
        password = credentials.get("password")
    except Exception:
        return jsonify({"error": "Invalid request format"}), 400
    user = db.session.execute(
        db.select(Customer).filter_by(email=email)
    ).scalar_one_or_none()
    if user and user.check_password(password):
        auth_token = encode_token(user.id)
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Successfully logged in",
                    "auth_token": auth_token,
                }
            ),
            200,
        )

    return jsonify({"error": "Invalid email or password"}), 401


@customer_bp.route("/", methods=["POST"])
# @limiter.limit("5 per hour")
def create_customer():
    """
    Create a new customer.
    """
    try:
        data = request.get_json()
        existing_customer = db.session.execute(
            db.select(Customer).filter_by(email=data.get("email"))
        ).scalar_one_or_none()
        if existing_customer:
            return jsonify({"error": "Email already exists."}), 409

        new_customer = customer_schema.load(data)
        db.session.add(new_customer)
        db.session.commit()
        return customer_schema.jsonify(new_customer), 201

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400


@customer_bp.route("/", methods=["GET"])
@cache.cached(timeout=60)
@limiter.limit("20 per minute")
def get_customers():
    """
    Get a paginated list of customers.
    """
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

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


@customer_bp.route("/<int:id>", methods=["GET"])
@cache.cached(timeout=30)
def get_customer(id):
    """
    Get a specific customer by ID.
    """
    customer = db.session.get(Customer, id)
    if not customer:
        abort(404, description="Customer not found.")
    return customer_schema.jsonify(customer), 200


@customer_bp.route("/my-tickets", methods=["GET"])
@token_required
@cache.cached(timeout=30)
def get_my_tickets(user_id):
    """
    Returns service tickets for the authenticated customer.
    """
    tickets = ServiceTicket.query.filter_by(customer_id=user_id).all()
    return jsonify(tickets_schema.dump(tickets)), 200


@customer_bp.route("/<int:id>", methods=["PUT"])
@token_required
@limiter.limit("5 per hour")
def update_customer(user_id, id):
    """
    Update customer details.
    Only the authenticated user can update their own details.
    """
    if str(user_id) != str(id):
        return jsonify({"error": "Unauthorized to update this user"}), 403

    customer = db.session.get(Customer, id)
    if not customer:
        abort(404, description="Customer not found.")

    try:
        data = request.get_json()
        if "password" in data:
            customer.set_password(data["password"])

        customer.name = data.get("name", customer.name)
        customer.email = data.get("email", customer.email)
        customer.phone = data.get("phone", customer.phone)
        customer.address = data.get("address", customer.address)

        if "service_tickets" in data:
            ticket_ids = data["service_tickets"]
            customer.service_tickets = ServiceTicket.query.filter(
                ServiceTicket.id.in_(ticket_ids)
            ).all()

        db.session.commit()
        return customer_schema.jsonify(customer), 200

    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Invalid data: {str(e)}"}), 400


@customer_bp.route("/<int:id>", methods=["DELETE"])
@token_required
@limiter.limit("2 per hour")
def delete_customer(user_id, id):
    """
    Delete a customer.
    Only the authenticated user can delete their own account.
    """
    if str(user_id) != str(id):
        return jsonify({"error": "Unauthorized to delete this user"}), 403

    customer = db.session.get(Customer, id)
    if not customer:
        abort(404, description="Customer not found.")
    try:
        db.session.delete(customer)
        db.session.commit()
        return jsonify({"message": f"Customer {id} deleted successfully"}), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
