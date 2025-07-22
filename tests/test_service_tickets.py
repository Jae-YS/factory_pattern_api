import unittest
from app import create_app, db
from app.models import (
    Customer,
    Mechanic,
    Inventory,
    ServiceTicket,
)
from flask import Flask


class ServiceTicketRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and in-memory database"""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create a test customer
            self.customer = Customer(
                name="Jane Customer",
                email="jane@example.com",
                phone="555-2222",
                address="123 Customer St",
            )
            self.customer.set_password("custpass")
            # Create a test mechanic
            self.mechanic = Mechanic(
                name="Mike Mechanic",
                email="mike@example.com",
                phone="555-3333",
                address="456 Mechanic Blvd",
                salary=40000,
            )
            self.mechanic.set_password("mechpass")
            # Create inventory
            self.inventory = Inventory(
                name="Spark Plug", quantity=50, description="Standard spark plug"
            )
            db.session.add_all([self.customer, self.mechanic, self.inventory])
            db.session.commit()
            self.customer_token = self.login_as_customer()
            self.mechanic_token = self.login_as_mechanic()

    def tearDown(self):
        """Clean up database"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login_as_customer(self):
        """Helper to login as customer and get token"""
        response = self.client.post(
            "/customer/login",
            json={"email": "jane@example.com", "password": "custpass"},
        )
        return response.get_json().get("auth_token")

    def login_as_mechanic(self):
        """Helper to login as mechanic and get token"""
        response = self.client.post(
            "/mechanic/login",
            json={"email": "mike@example.com", "password": "mechpass"},
        )
        return response.get_json().get("auth_token")

    def customer_auth_header(self):
        return {"Authorization": f"Bearer {self.customer_token}"}

    def mechanic_auth_header(self):
        return {"Authorization": f"Bearer {self.mechanic_token}"}

    # === TESTS FOR POST /service_tickets ===
    def test_create_service_ticket_success(self):
        response = self.client.post(
            "/service_ticket/",
            headers=self.customer_auth_header(),
            json={
                "title": "Check Engine Light",
                "description": "Light is on constantly.",
                "mechanic_ids": [self.mechanic.id],
                "inventory_items": [{"inventory_id": self.inventory.id, "quantity": 2}],
                "status": "PENDING",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["ticket"]["title"], "Check Engine Light")

    def test_create_service_ticket_invalid_status(self):
        response = self.client.post(
            "/service_ticket/",
            headers=self.customer_auth_header(),
            json={
                "title": "Bad Status Test",
                "description": "Trying invalid status",
                "status": "NOT_A_STATUS",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    def test_create_service_ticket_unauthorized(self):
        response = self.client.post(
            "/service_ticket/",
            json={"title": "No Token Test", "description": "Should fail."},
        )
        self.assertEqual(response.status_code, 401)

    # === TESTS FOR GET /service_tickets ===
    def test_get_service_tickets_success(self):
        # Create a service ticket
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Oil Change",
                description="Routine maintenance",
                customer_id=self.customer.id,
            )
            db.session.add(ticket)
            db.session.commit()

        response = self.client.get("/service_ticket/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("service_tickets", response.get_json())

    # === TESTS FOR GET /service_ticket/<id> ===
    def test_get_service_ticket_success(self):
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Tire Rotation",
                description="Rotate tires for even wear",
                customer_id=self.customer.id,
            )
            db.session.add(ticket)
            db.session.commit()

        response = self.client.get(f"/service_ticket/{ticket.id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn("ticket", response.get_json())

    def test_get_service_ticket_not_found(self):
        response = self.client.get("/service_ticket/9999")
        self.assertEqual(response.status_code, 404)

    # === TESTS FOR PUT /service_ticket/<id> ===
    def test_update_service_ticket_success(self):
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Brake Inspection",
                description="Check brakes for wear",
                customer_id=self.customer.id,
            )
            db.session.add(ticket)
            db.session.commit()

        response = self.client.put(
            f"/service_ticket/{ticket.id}",
            headers=self.mechanic_auth_header(),
            json={"add_mechanics": [self.mechanic.id], "status": "COMPLETED"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.get_json())

    def test_update_service_ticket_invalid_inventory(self):
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Invalid Inventory Test", customer_id=self.customer.id
            )
            db.session.add(ticket)
            db.session.commit()

        response = self.client.put(
            f"/service_ticket/{ticket.id}",
            headers=self.mechanic_auth_header(),
            json={"add_inventory": [{"inventory_id": 9999, "quantity": 1}]},
        )
        self.assertEqual(response.status_code, 404)

    # === TESTS FOR DELETE /service_ticket/<id> ===
    def test_delete_service_ticket_success(self):
        with self.app.app_context():
            ticket = ServiceTicket(title="Delete Me", customer_id=self.customer.id)
            db.session.add(ticket)
            db.session.commit()

        response = self.client.delete(f"/service_ticket/{ticket.id}")
        self.assertEqual(response.status_code, 204)

    def test_delete_service_ticket_not_found(self):
        response = self.client.delete("/service_ticket/9999")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
