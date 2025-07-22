# app/blueprints/inventoryassignment/inventoryAssignmentSchemas.py

from app.models import InventoryServiceTicket
from app.extensions import ma
from marshmallow import fields


class InventoryAssignmentSchema(ma.SQLAlchemySchema):
    class Meta:
        model = InventoryServiceTicket
        load_instance = True

    service_ticket_id = ma.auto_field()
    inventory_id = ma.auto_field()
    quantity = ma.auto_field()

    service_ticket = fields.Nested(
        "ServiceTicketSchema", exclude=("inventory_assignments",)
    )
    inventory = fields.Nested("InventorySchema", exclude=("inventory_assignments",))
