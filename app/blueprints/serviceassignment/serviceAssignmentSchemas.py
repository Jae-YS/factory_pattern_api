from app.models import ServiceAssignment
from app.extensions import ma
from marshmallow import fields


class ServiceAssignmentSchema(ma.SQLAlchemySchema):
    class Meta:
        model = ServiceAssignment
        load_instance = True

    service_ticket_id = ma.auto_field()
    mechanic_id = ma.auto_field()
    date_assigned = ma.auto_field()

    service_ticket = fields.Nested(
        "ServiceTicketSchema", exclude=("service_assignments",)
    )
    mechanic = fields.Nested("MechanicSchema", exclude=("service_assignments",))
