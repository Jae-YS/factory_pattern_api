from datetime import date
import unittest
from app import create_app, db
from app.models import Customer, Mechanic, Inventory, ServiceTicket


class ServiceTicketRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and in-memory database"""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            self.customer = Customer(
                name="Jane Customer",
                email="jane@example.com",
                phone="555-2222",
                address="123 Customer St",
            )
            self.customer.set_password("custpass")

            self.mechanic = Mechanic(
                name="Mike Mechanic",
                email="mike@example.com",
                phone="555-3333",
                address="456 Mechanic Blvd",
                salary=40000,
            )
            self.mechanic.set_password("mechpass")

            self.inventory = Inventory(
                part_name="Spark Plug",
                quantity=50,
                description="Standard spark plug",
                price=2.5,
            )

            db.session.add_all([self.customer, self.mechanic, self.inventory])
            db.session.commit()

            self.customer_id = self.customer.id
            self.mechanic_id = self.mechanic.id
            self.inventory_id = self.inventory.id

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

    # --- TESTS FOR POST /service_ticket ---
    def test_create_service_ticket_success(self):
        response = self.client.post(
            "/service_ticket/",
            headers=self.mechanic_auth_header(),
            json={
                "title": "Check Engine Light",
                "service_date": "2025-07-21",
                "vin": "1HGCM82633A123456",
                "cost": 150.0,
                "customer_id": 1,
                "description": "The check engine light stays on constantly.",
                "status": "PENDING",
                "mechanic_ids": [1],
                "date_created": "2025-07-20",
                "inventory_items": [{"inventory_id": 1, "quantity": 2}],
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["ticket"]["title"], "Check Engine Light")

    def test_create_service_ticket_unauthorized_customer(self):
        """Customers should not be able to create service tickets"""
        response = self.client.post(
            "/service_ticket/",
            headers=self.customer_auth_header(),
            json={"title": "Unauthorized Creation", "description": "Should fail."},
        )
        self.assertEqual(response.status_code, 403)

    def test_create_service_ticket_invalid_status(self):
        response = self.client.post(
            "/service_ticket/",
            headers=self.mechanic_auth_header(),
            json={
                "title": "Bad Status Test",
                "description": "Trying invalid status",
                "status": "NOT_A_STATUS",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    # --- TESTS FOR GET /service_ticket ---
    def test_get_service_tickets_success(self):
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Oil Change",
                description="Routine maintenance",
                customer_id=self.customer_id,
                service_date=date(2025, 7, 21),
                vin="1HGCM82633A123456",
                cost=50.0,
                date_created=date(2025, 7, 20),
                status="PENDING",
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.get(
            "/service_ticket/", headers=self.mechanic_auth_header()
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("service_tickets", response.get_json())

    def test_get_service_tickets_unauthorized_customer(self):
        response = self.client.get(
            "/service_ticket/", headers=self.customer_auth_header()
        )
        self.assertEqual(response.status_code, 403)

    # --- TESTS FOR GET /service_ticket/<id> ---
    def test_get_service_ticket_success(self):
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Tire Rotation",
                description="Rotate tires for even wear",
                customer_id=self.customer_id,
                service_date=date(2025, 7, 21),
                vin="1HGCM82633A123456",
                cost=75.0,
                date_created=date(2025, 7, 20),
                status="PENDING",
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.get(
            f"/service_ticket/{ticket_id}", headers=self.mechanic_auth_header()
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("ticket", response.get_json())

    def test_get_service_ticket_not_found(self):
        response = self.client.get(
            "/service_ticket/9999", headers=self.mechanic_auth_header()
        )
        self.assertEqual(response.status_code, 404)

    # --- TESTS FOR PUT /service_ticket/<id> ---
    def test_update_service_ticket_success(self):
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Brake Inspection",
                description="Check brakes for wear",
                customer_id=self.customer_id,
                service_date=date(2025, 7, 21),
                vin="1HGCM82633A123456",
                cost=100.0,
                date_created=date(2025, 7, 20),
                status="PENDING",
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.put(
            f"/service_ticket/{ticket_id}",
            headers=self.mechanic_auth_header(),
            json={"add_mechanics": [self.mechanic_id], "status": "COMPLETED"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.get_json())

    def test_update_service_ticket_invalid_inventory(self):
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Invalid Inventory Test",
                service_date=date.today(),
                vin="123ABC",
                description="Test",
                status="PENDING",
                cost=0.0,
                date_created=date.today(),
                customer_id=1,
            )

            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.put(
            f"/service_ticket/{ticket_id}",
            headers=self.mechanic_auth_header(),
            json={"add_inventory": [{"inventory_id": 9999, "quantity": 1}]},
        )
        self.assertEqual(response.status_code, 404)

    # --- TESTS FOR DELETE /service_ticket/<id> ---
    def test_delete_service_ticket_success(self):
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Delete Me",
                description="This ticket will be deleted",
                customer_id=self.customer_id,
                service_date=date(2025, 7, 21),
                vin="1HGCM82633A123456",
                cost=75.0,
                date_created=date(2025, 7, 20),
                status="PENDING",
            )
            db.session.add(ticket)
            db.session.commit()
            ticket_id = ticket.id

        response = self.client.delete(
            f"/service_ticket/{ticket_id}", headers=self.mechanic_auth_header()
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_service_ticket_not_found(self):
        response = self.client.delete(
            "/service_ticket/9999", headers=self.mechanic_auth_header()
        )
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
