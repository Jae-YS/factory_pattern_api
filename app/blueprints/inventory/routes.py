from flask import Blueprint, jsonify, request
from sqlalchemy import func
from app.extensions import db, limiter
from app.models import Inventory, Mechanic, ServiceTicket
from app.blueprints.inventory.inventorySchemas import (
    InventorySchema,
)
from app.utils.util import mechanic_token_required, encode_mechanic_token


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
    if not mechanic_id:
        return jsonify({"error": "Unauthorized to view inventory"}), 403

    inventory_items = Inventory.query.all()
    return inventories_schema.jsonify(inventory_items), 200


@inventory_bp.route("/<int:item_id>", methods=["GET"])
@mechanic_token_required
def get_inventory_item(mechanic_id, item_id):
    """
    Retrieves a specific inventory item.
    """
    if not mechanic_id:
        return jsonify({"error": "Unauthorized to view inventory"}), 403

    item = Inventory.query.get_or_404(item_id)
    return inventory_schema.jsonify(item), 200


@inventory_bp.route("/", methods=["POST"])
@mechanic_token_required
def create_inventory_item(mechanic_id):
    """
    Creates a new inventory item.
    """
    if not mechanic_id:
        return jsonify({"error": "Unauthorized to create inventory item"}), 403

    data = request.get_json()
    try:
        new_item = inventory_schema.load(data)
        db.session.add(new_item)
        db.session.commit()
        return inventory_schema.jsonify(new_item), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@inventory_bp.route("/<int:item_id>", methods=["PUT"])
@mechanic_token_required
def update_inventory_item(mechanic_id, item_id):
    """
    Updates a specific inventory item.
    """
    if not mechanic_id:
        return jsonify({"error": "Unauthorized to update inventory item"}), 403

    item = Inventory.query.get_or_404(item_id)
    data = request.get_json()
    try:
        updated_item = inventory_schema.load(data, instance=item)
        db.session.commit()
        return inventory_schema.jsonify(updated_item), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400


@inventory_bp.route("/<int:item_id>", methods=["DELETE"])
@mechanic_token_required
def delete_inventory_item(mechanic_id, item_id):
    """
    Deletes a specific inventory item.
    """
    if not mechanic_id:
        return jsonify({"error": "Unauthorized to delete inventory item"}), 403

    item = Inventory.query.get_or_404(item_id)
    try:
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Inventory item deleted successfully"}), 204
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
