from app.extensions import ma
from app.models import Mechanic
from marshmallow import post_load


class MechanicSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Mechanic
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    email = ma.auto_field()
    phone = ma.auto_field()
    address = ma.auto_field()
    salary = ma.auto_field()
    password = ma.String(load_only=True, required=True)

    service_assignments = ma.Nested(
        "ServiceAssignmentSchema",
        many=True,
        dump_only=True,
        exclude=("mechanic",),
    )

    service_tickets = ma.Nested(
        "ServiceTicketSchema", many=True, dump_only=True, only=("id", "vin")
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


class MechanicLoginSchema(ma.Schema):
    email = ma.Email(required=True)
    password = ma.String(required=True)

    class Meta:
        ordered = True
        fields = ("email", "password")
