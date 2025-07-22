from app.extensions import ma
from app.models import Inventory


class InventorySchema(ma.SQLAlchemySchema):
    class Meta:
        model = Inventory
        load_instance = True  # Deserialize to SQLAlchemy objects

    id = ma.auto_field()
    part_name = ma.auto_field()
    price = ma.auto_field()
    quantity = ma.auto_field()
    description = ma.auto_field()
