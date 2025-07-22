from flask import Blueprint, jsonify, request, abort
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db, limiter
from app.models import Inventory
from app.blueprints.inventory.inventorySchemas import InventorySchema
from app.utils.util import mechanic_token_required


inventory_bp = Blueprint("inventory", __name__, url_prefix="/inventory")

# Schema instances
inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)


@inventory_bp.route("/", methods=["GET"])
@mechanic_token_required
def get_inventory_for_mechanic(mechanic_id):
    """
    Retrieves all inventory items for the authenticated mechanic.
    """
    inventory_items = Inventory.query.all()
    return inventories_schema.jsonify(inventory_items), 200


@inventory_bp.route("/<int:inventory_id>", methods=["GET"])
@mechanic_token_required
def get_inventory_item(mechanic_id, inventory_id):
    """
    Retrieves a specific inventory item by ID.
    """
    item = Inventory.query.get(inventory_id)
    if not item:
        abort(404, description="Inventory item not found.")
    return inventory_schema.jsonify(item), 200


@inventory_bp.route("/", methods=["POST"])
@mechanic_token_required
def create_inventory_item(mechanic_id):
    """
    Creates a new inventory item.
    """
    data = request.get_json()
    try:
        new_item = inventory_schema.load(data)
        db.session.add(new_item)
        db.session.commit()
        return inventory_schema.jsonify(new_item), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        return jsonify({"error": "Invalid request payload"}), 400


@inventory_bp.route("/<int:inventory_id>", methods=["PUT"])
@mechanic_token_required
def update_inventory_item(mechanic_id, inventory_id):
    """
    Updates a specific inventory item by ID.
    """
    item = Inventory.query.get(inventory_id)
    if not item:
        abort(404, description="Inventory item not found.")
    data = request.get_json()
    try:
        updated_item = inventory_schema.load(data, instance=item)
        db.session.commit()
        return inventory_schema.jsonify(updated_item), 200
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception:
        return jsonify({"error": "Invalid request payload"}), 400


@inventory_bp.route("/<int:inventory_id>", methods=["DELETE"])
@mechanic_token_required
def delete_inventory_item(mechanic_id, inventory_id):
    """
    Deletes a specific inventory item by ID.
    """
    item = Inventory.query.get(inventory_id)
    if not item:
        abort(404, description="Inventory item not found.")
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Inventory item deleted successfully"}), 204
    except SQLAlchemyError:
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
