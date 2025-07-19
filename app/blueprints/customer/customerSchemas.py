from app.models import Customer
from app.extensions import ma


class CustomerSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Customer
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    email = ma.auto_field()
    phone = ma.auto_field()
    address = ma.auto_field()
    service_tickets = ma.Nested("ServiceTicketSchema", many=True, exclude=("customer",))
