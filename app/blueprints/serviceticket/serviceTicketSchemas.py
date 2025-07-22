from app.extensions import ma
from app.models import ServiceTicket, ServiceStatus
from marshmallow import fields, ValidationError


#
class EnumField(fields.Field):
    def __init__(self, enum_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.enum_class = enum_class

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None
        return value.name  

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        if isinstance(value, self.enum_class):
            return value  
        try:
            return self.enum_class[value.upper()]  
        except KeyError:
            raise ValidationError(
                f"Invalid status '{value}'. Allowed values: {[e.name for e in self.enum_class]}"
            )


class ServiceTicketSchema(ma.SQLAlchemySchema):
    class Meta:
        model = ServiceTicket
        load_instance = True
        include_fk = True

    id = ma.auto_field()
    title = ma.auto_field()
    service_date = ma.auto_field()
    vin = ma.auto_field()
    description = ma.auto_field()
    status = EnumField(ServiceStatus, required=True)
    cost = ma.auto_field()
    date_created = ma.auto_field()
    customer_id = ma.auto_field()

    customer = ma.Nested("CustomerSchema", only=("id", "name"), dump_only=True)
    service_assignments = ma.Nested(
        "ServiceAssignmentSchema",
        many=True,
        dump_only=True,
        exclude=("service_ticket",),
    )
    mechanics = ma.Nested(
        "MechanicSchema", many=True, dump_only=True, only=("id", "name"), 
    )

    inventory_assignments = fields.Nested(
        "InventoryAssignmentSchema",
        many=True,
        dump_only=True,
        exclude=("service_ticket",) 
    )
