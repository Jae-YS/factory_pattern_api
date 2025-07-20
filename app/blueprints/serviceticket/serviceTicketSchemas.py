from app.extensions import ma
from app.models import ServiceTicket


class ServiceTicketSchema(ma.SQLAlchemySchema):
    class Meta:
        model = ServiceTicket
        load_instance = True
        include_fk = True

    id = ma.auto_field()
    service_date = ma.auto_field()
    vin = ma.auto_field()
    description = ma.auto_field()
    status = ma.auto_field()
    cost = ma.auto_field()
    date_created = ma.auto_field()
    customer_id = ma.auto_field(required=True)

    customer = ma.Nested("CustomerSchema", only=("id", "name"), dump_only=True)

    service_assignments = ma.Nested(
        "ServiceAssignmentSchema",
        many=True,
        dump_only=True,
        exclude=("service_ticket",),
    )

    mechanics = ma.Nested(
        "MechanicSchema", many=True, dump_only=True, only=("id", "name")
    )
