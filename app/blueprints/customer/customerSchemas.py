from app.models import Customer
from app.extensions import ma
from marshmallow import post_load


class CustomerSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Customer
        load_instance = True

    id = ma.auto_field()
    password = ma.auto_field(load_only=True)
    name = ma.auto_field()
    email = ma.auto_field()
    phone = ma.auto_field()
    address = ma.auto_field()
    service_tickets = ma.Nested(
        "ServiceTicketSchema",
        many=True,
        exclude=("customer",),
    )

    @post_load
    def hash_password(self, data, **kwargs):
        """
        Automatically hash password if provided in input.
        """
        if hasattr(data, "password") and data.password:
            raw_password = data.password
            data.set_password(raw_password)
        return data


class LoginSchema(ma.Schema):
    email = ma.Email(required=True)
    password = ma.String(required=True)

    class Meta:
        ordered = True
        fields = ("email", "password")
