import unittest
from app import create_app, db
from app.models import Mechanic, ServiceTicket, ServiceAssignment
from flask import Flask


class ServiceAssignmentRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and database"""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create test mechanic and service ticket
            self.mechanic = Mechanic(
                name="Sarah Wrench",
                email="sarah@example.com",
                phone="555-1111",
                address="Mechanic Ave",
                salary=45000,
            )
            self.mechanic.set_password("securepass")
            self.ticket = ServiceTicket(
                title="Brake Replacement",
                description="Replace brake pads",
                customer_id=None,
            )
            db.session.add_all([self.mechanic, self.ticket])
            db.session.commit()
            self.auth_token = self.login_and_get_token()

    def tearDown(self):
        """Clean up database"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login_and_get_token(self):
        """Helper to log in mechanic and get token"""
        response = self.client.post(
            "/mechanic/login",
            json={"email": "sarah@example.com", "password": "securepass"},
        )
        data = response.get_json()
        return data.get("auth_token")

    def auth_header(self):
        return {"Authorization": f"Bearer {self.auth_token}"}

    # === TESTS FOR POST /service_assignment ===
    def test_create_service_assignment_success(self):
        response = self.client.post(
            "/service_assignment/",
            headers=self.auth_header(),
            json={
                "service_ticket_id": self.ticket.id,
                "mechanic_id": self.mechanic.id,
                "date_assigned": "2025-07-21",
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["service_ticket_id"], self.ticket.id)
        self.assertEqual(data["mechanic_id"], self.mechanic.id)

    def test_create_service_assignment_duplicate(self):
        # First creation
        self.client.post(
            "/service_assignment/",
            headers=self.auth_header(),
            json={
                "service_ticket_id": self.ticket.id,
                "mechanic_id": self.mechanic.id,
                "date_assigned": "2025-07-21",
            },
        )
        # Duplicate creation
        response = self.client.post(
            "/service_assignment/",
            headers=self.auth_header(),
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
        # Create assignment
        with self.app.app_context():
            assignment = ServiceAssignment(
                service_ticket_id=self.ticket.id,
                mechanic_id=self.mechanic.id,
                date_assigned="2025-07-21",
            )
            db.session.add(assignment)
            db.session.commit()

        response = self.client.get("/service_assignment/", headers=self.auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(a["service_ticket_id"] == self.ticket.id for a in response.get_json())
        )

    def test_get_all_service_service_assignment_unauthorized(self):
        response = self.client.get("/service_assignment/")
        self.assertEqual(response.status_code, 401)

    # === TESTS FOR DELETE /service_assignment ===
    def test_delete_service_assignment_success(self):
        # Create assignment
        with self.app.app_context():
            assignment = ServiceAssignment(
                service_ticket_id=self.ticket.id,
                mechanic_id=self.mechanic.id,
                date_assigned="2025-07-21",
            )
            db.session.add(assignment)
            db.session.commit()

        response = self.client.delete(
            f"/service_assignment/?service_ticket_id={self.ticket.id}&mechanic_id={self.mechanic.id}",
            headers=self.auth_header(),
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.get_json())

    def test_delete_service_assignment_not_found(self):
        response = self.client.delete(
            "/service_assignment/?service_ticket_id=9999&mechanic_id=9999",
            headers=self.auth_header(),
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
