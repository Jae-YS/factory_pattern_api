import unittest
from app import create_app, db
from app.models import Mechanic, ServiceTicket, ServiceAssignment
from flask import Flask


class MechanicRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and database"""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create test mechanic
            self.mechanic = Mechanic(
                name="Alice Mechanic",
                email="alice@example.com",
                phone="555-1234",
                address="123 Workshop Rd",
                salary=50000,
            )
            self.mechanic.set_password("password123")
            db.session.add(self.mechanic)
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
            json={"email": "alice@example.com", "password": "password123"},
        )
        data = response.get_json()
        return data.get("auth_token")

    def auth_header(self):
        return {"Authorization": f"Bearer {self.auth_token}"}

    # === TESTS FOR /mechanic/login ===
    def test_mechanic_login_success(self):
        response = self.client.post(
            "/mechanic/login",
            json={"email": "alice@example.com", "password": "password123"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("auth_token", response.get_json())

    def test_mechanic_login_invalid_credentials(self):
        response = self.client.post(
            "/mechanic/login",
            json={"email": "alice@example.com", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.get_json())

    # === TESTS FOR /mechanics (POST) ===
    def test_create_mechanic_success(self):
        response = self.client.post(
            "/mechanics",
            json={
                "name": "Bob Builder",
                "email": "bob@example.com",
                "phone": "555-5678",
                "address": "456 Garage St",
                "salary": 45000,
                "password": "securepass",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["name"], "Bob Builder")

    def test_create_mechanic_duplicate_email(self):
        response = self.client.post(
            "/mechanics",
            json={
                "name": "Duplicate",
                "email": "alice@example.com",  # already exists
                "phone": "000-0000",
                "address": "999 Loop Rd",
                "salary": 50000,
                "password": "anotherpass",
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("error", response.get_json())

    # === TESTS FOR /mechanics (GET) ===
    def test_get_mechanics_success(self):
        response = self.client.get("/mechanics")
        self.assertEqual(response.status_code, 200)
        self.assertIn("mechanics", response.get_json())

    # === TESTS FOR /mechanic/<id> (GET) ===
    def test_get_mechanic_success(self):
        response = self.client.get(
            f"/mechanic/{self.mechanic.id}", headers=self.auth_header()
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["email"], "alice@example.com")

    def test_get_mechanic_unauthorized(self):
        response = self.client.get(f"/mechanic/{self.mechanic.id}")  # no auth
        self.assertEqual(response.status_code, 401)

    # === TESTS FOR /mechanic/<id> (PUT) ===
    def test_update_mechanic_success(self):
        response = self.client.put(
            f"/mechanic/{self.mechanic.id}",
            headers=self.auth_header(),
            json={"name": "Alice Updated", "salary": 55000},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "Alice Updated")

    def test_update_mechanic_unauthorized(self):
        # Simulate wrong user
        response = self.client.put(
            "/mechanic/9999",  # Wrong ID
            headers=self.auth_header(),
            json={"name": "Hacker"},
        )
        self.assertEqual(response.status_code, 403)

    # === TESTS FOR /mechanic/<id> (DELETE) ===
    def test_delete_mechanic_success(self):
        response = self.client.delete(
            f"/mechanic/{self.mechanic.id}", headers=self.auth_header()
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_mechanic_unauthorized(self):
        response = self.client.delete("/mechanic/9999", headers=self.auth_header())
        self.assertEqual(response.status_code, 403)

    # === TESTS FOR /mechanic/rankings (GET) ===
    def test_get_mechanic_rankings(self):
        # Add a service ticket and assignment
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Fix Car", description="Oil change", customer_id=None
            )
            db.session.add(ticket)
            db.session.flush()
            assignment = ServiceAssignment(
                service_ticket_id=ticket.id, mechanic_id=self.mechanic.id
            )
            db.session.add(assignment)
            db.session.commit()

        response = self.client.get("/mechanic/rankings")
        self.assertEqual(response.status_code, 200)
        rankings = response.get_json()
        self.assertTrue(any(m["ticket_count"] >= 1 for m in rankings))


if __name__ == "__main__":
    unittest.main()
