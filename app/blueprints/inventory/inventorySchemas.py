from app.extensions import ma
from app.models import Inventory
from marshmallow import fields

class InventorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = Inventory
        load_instance = True 

    id = ma.auto_field()
    part_name = ma.auto_field()
    price = ma.auto_field()
    quantity = ma.auto_field()
    description = ma.auto_field()
    
    inventory_assignments = fields.Nested(
        "InventoryAssignmentSchema",
        many=True,
        dump_only=True,
        exclude=("inventory",) 
    )

