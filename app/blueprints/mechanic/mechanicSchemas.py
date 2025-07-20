from app.extensions import ma
from app.models import Mechanic


class MechanicSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Mechanic
        load_instance = True  # Deserialize to SQLAlchemy objects

    id = ma.auto_field()
    name = ma.auto_field()
    email = ma.auto_field()
    phone = ma.auto_field()
    address = ma.auto_field()
    salary = ma.auto_field()
    service_tickets = ma.Nested("ServiceTicketSchema", many=True, dump_only=True)


class MechanicLoginSchema(ma.Schema):
    email = ma.Email(required=True)
    password = ma.String(required=True)

    class Meta:
        ordered = True
        fields = ("email", "password")
