from datetime import date
import unittest
from app import create_app, db
from app.models import Customer, Mechanic, ServiceTicket, ServiceAssignment


class ServiceAssignmentRoutesTestCase(unittest.TestCase):
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

            db.session.add_all([self.customer, self.mechanic])
            db.session.commit()

            self.customer_id = self.customer.id
            self.mechanic_id = self.mechanic.id

            self.ticket = ServiceTicket(
                title="Brake Replacement",
                description="Replace brake pads",
                customer_id=self.customer_id,
                service_date=date(2025, 7, 20),
                vin="1HGCM82633A123456",
                cost=150.0,
                date_created=date(2025, 7, 19),
                status="PENDING",
            )
            db.session.add(self.ticket)
            db.session.commit()

            self.ticket_id = self.ticket.id
            self.mechanic_token = self.login_as_mechanic()
            self.customer_token = self.login_as_customer()

    def tearDown(self):
        """Clean up database"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login_as_customer(self):
        """Helper: log in as customer and get auth token"""
        response = self.client.post(
            "/customer/login",
            json={"email": self.customer.email, "password": "custpass"},
        )
        self.assertEqual(response.status_code, 200, "Customer login failed")
        data = response.get_json()
        return data["auth_token"]

    def login_as_mechanic(self):
        """Helper: log in as mechanic and get auth token"""
        response = self.client.post(
            "/mechanic/login",
            json={"email": self.mechanic.email, "password": "mechpass"},
        )
        self.assertEqual(response.status_code, 200, "Mechanic login failed")
        data = response.get_json()
        return data["auth_token"]

    def customer_auth_header(self):
        return {"Authorization": f"Bearer {self.customer_token}"}

    def mechanic_auth_header(self):
        return {"Authorization": f"Bearer {self.mechanic_token}"}


    # === TESTS FOR POST /service_assignment ===
    def test_create_service_assignment_success(self):
        response = self.client.post(
            "/service_assignment/",
            headers=self.mechanic_auth_header(),
            json={
                "service_ticket_id": self.ticket_id,
                "mechanic_id": self.mechanic_id,
                "date_assigned": "2025-07-21",  
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["service_ticket_id"], self.ticket_id)
        self.assertEqual(data["mechanic_id"], self.mechanic_id)

    def test_create_service_assignment_duplicate(self):

        self.client.post(
            "/service_assignment/",
            headers=self.mechanic_auth_header(),
            json={
                "service_ticket_id": self.ticket.id,
                "mechanic_id": self.mechanic.id,
                "date_assigned": "2025-07-21",  
            },
        )

        response = self.client.post(
            "/service_assignment/",
            headers=self.mechanic_auth_header(),
            json={
                "service_ticket_id": self.ticket.id,
                "mechanic_id": self.mechanic.id,
                "date_assigned": "2025-07-21",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    # === TESTS FOR GET /service_assignment ===
    def test_get_all_service_service_assignment_success(self):

        with self.app.app_context():
            assignment = ServiceAssignment(
                service_ticket_id=self.ticket.id,
                mechanic_id=self.mechanic.id,
                date_assigned=date(2025, 7, 21),
            )
            db.session.add(assignment)
            db.session.commit()

        response = self.client.get("/service_assignment/", headers=self.mechanic_auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(a["service_ticket_id"] == self.ticket.id for a in response.get_json())
        )

    def test_get_all_service_service_assignment_unauthorized(self):
        response = self.client.get("/service_assignment/")
        self.assertEqual(response.status_code, 401)

    # === TESTS FOR DELETE /service_assignment ===
    def test_delete_service_assignment_success(self):

        with self.app.app_context():
            assignment = ServiceAssignment(
                service_ticket_id=self.ticket.id,
                mechanic_id=self.mechanic.id,
                date_assigned=date(2025, 7, 21),
            )
            db.session.add(assignment)
            db.session.commit()

        response = self.client.delete(
            f"/service_assignment/?service_ticket_id={self.ticket.id}&mechanic_id={self.mechanic.id}",
            headers=self.mechanic_auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.get_json())

    def test_delete_service_assignment_not_found(self):
        response = self.client.delete(
            "/service_assignment/?service_ticket_id=9999&mechanic_id=9999",
            headers=self.mechanic_auth_header(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
