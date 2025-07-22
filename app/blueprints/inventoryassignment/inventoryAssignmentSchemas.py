from app.models import InventoryAssignment
from app.extensions import ma
from marshmallow import fields


class InventoryAssignmentSchema(ma.SQLAlchemySchema):
    class Meta:
        model = InventoryAssignment
        load_instance = True

    service_ticket_id = ma.auto_field()
    inventory_id = ma.auto_field()
    quantity = ma.auto_field()

    service_ticket = fields.Nested(
        "ServiceTicketSchema",
        only=("id", "title", "status"),  
        dump_only=True
    )
    inventory = fields.Nested(
        "InventorySchema",
        only=("id", "part_name", "price"),
        dump_only=True
    )