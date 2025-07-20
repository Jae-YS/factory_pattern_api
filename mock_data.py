from datetime import date, timedelta
from random import choice, randint, uniform
from dotenv import load_dotenv

from app.models import (
    Customer,
    Inventory,
    InventoryServiceTicket,
    Mechanic,
    ServiceAssignment,
    ServiceTicket,
)

load_dotenv()

from app import create_app
from app.extensions import db

# Create the Flask app
app = create_app()


def seed_mock_data():
    with app.app_context():

        print("Seeding mock data...")

        try:
            # Add Customers
            customers = []
            for i in range(5):
                customer = Customer(
                    name=f"Customer {i+1}",
                    email=f"customer{i+1}@example.com",
                    password="password123",
                    phone=f"555-100{i}",
                    address=f"{100+i} Main St, City",
                )
                db.session.add(customer)
                customers.append(customer)

            # Add Mechanics
            mechanics = []
            for i in range(3):
                mechanic = Mechanic(
                    name=f"Mechanic {i+1}",
                    email=f"mechanic{i+1}@example.com",
                    phone=f"555-200{i}",
                    address=f"{200+i} Workshop Ave, City",
                    salary=round(uniform(40000, 60000), 2),
                )
                db.session.add(mechanic)
                mechanics.append(mechanic)

            # Add Inventory Parts
            parts = []
            for i in range(10):
                part = Inventory(
                    part_name=f"Part {i+1}",
                    price=round(uniform(10, 500), 2),
                )
                db.session.add(part)
                parts.append(part)

            # Add Service Tickets and assign mechanics/parts
            for i in range(8):
                ticket = ServiceTicket(
                    service_date=date.today() - timedelta(days=randint(1, 30)),
                    vin=f"VIN12345678{i}",
                    description=f"Service job {i+1}",
                    status=choice(["Pending", "In Progress", "Completed"]),
                    cost=round(uniform(100, 1000), 2),
                    date_created=date.today() - timedelta(days=randint(1, 30)),
                    customer=choice(customers),
                )
                db.session.add(ticket)

                # Assign mechanics
                assigned_mechanics = [choice(mechanics)]
                if randint(0, 1):
                    mech = choice(mechanics)
                    if mech not in assigned_mechanics:
                        assigned_mechanics.append(mech)

                for mech in assigned_mechanics:
                    assignment = ServiceAssignment(
                        service_ticket=ticket,
                        mechanic=mech,
                    )
                    db.session.add(assignment)

                # Assign parts
                for _ in range(randint(1, 3)):
                    part = choice(parts)
                    quantity = randint(1, 5)
                    link = InventoryServiceTicket(
                        service_ticket=ticket,
                        inventory=part,
                        quantity=quantity,
                    )
                    db.session.add(link)

            db.session.commit()
            print("Mock data inserted successfully.")

        except Exception as e:
            db.session.rollback()
            print("Error inserting mock data:", e)


if __name__ == "__main__":
    seed_mock_data()
