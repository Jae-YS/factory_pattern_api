from datetime import date
import unittest
from app import create_app, db
from app.models import Customer, ServiceTicket
from flask import Flask


class CustomerRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and in-memory database"""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create a test customer
            self.customer = Customer(
                name="John Doe",
                email="john@example.com",
                phone="1234567890",
                address="123 Main St",
                service_tickets=[],
            )
            self.customer.set_password("password123")
            db.session.add(self.customer)
            db.session.commit()

            self.auth_token = self.login_and_get_token()

    def tearDown(self):
        """Tear down database"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def login_and_get_token(self):
        response = self.client.post(
            "/customer/login",
            json={"email": "john@example.com", "password": "password123"},
        )
        if response.status_code != 200:
            raise Exception(
                f"Login failed: {response.status_code} {response.get_data(as_text=True)}"
            )

        data = response.get_json()
        if not data or "auth_token" not in data:
            raise Exception(f"Login succeeded but no token found: {data}")

        return data["auth_token"]

    def auth_header(self):
        return {"Authorization": f"Bearer {self.auth_token}"}

    # --- TESTS FOR /customer/login ---
    def test_login_success(self):
        response = self.client.post(
            "/customer/login",
            json={"email": "john@example.com", "password": "password123"},
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn("auth_token", response.get_json())

    def test_login_invalid_credentials(self):
        response = self.client.post(
            "/customer/login",
            json={"email": "john@example.com", "password": "wrongpass"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.get_json())

    # --- TESTS FOR /customer (POST) ---
    def test_create_customer_success(self):
        response = self.client.post(
            "/customer/",
            json={
                "name": "Jane Smith",
                "email": "jane@example.com",
                "phone": "0987654321",
                "address": "456 Elm St",
                "password": "securepass",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["name"], "Jane Smith")

    def test_create_customer_existing_email(self):
        response = self.client.post(
            "/customer/",
            json={
                "name": "Duplicate",
                "email": "john@example.com",
                "phone": "0000000000",
                "address": "789 Pine St",
                "password": "anotherpass",
            },
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("error", response.get_json())

    # --- TESTS FOR /customers (GET) ---
    def test_get_customers_success(self):
        response = self.client.get("/customer/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("customers", response.get_json())

    # --- TESTS FOR /customer/<id> (GET) ---
    def test_get_customer_success(self):
        response = self.client.get(f"/customer/{self.customer.id}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["email"], "john@example.com")

    def test_get_customer_not_found(self):
        response = self.client.get("/customer/9999")
        self.assertEqual(response.status_code, 404)

    # --- TESTS FOR /customer/my-tickets (GET) ---
    def test_get_my_tickets_success(self):
        with self.app.app_context():
            ticket = ServiceTicket(
                title="Fix AC",
                description="Air conditioner not cooling",
                vin="1HGCM826CX000000",
                service_date=date(2023, 10, 1),
                status="PENDING",
                cost=150.0,
                date_created=date(2023, 9, 1),
                customer=self.customer,
            )
            db.session.add(ticket)
            db.session.commit()

        response = self.client.get("/customer/my-tickets", headers=self.auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_get_my_tickets_unauthorized(self):
        response = self.client.get("/customer/my-tickets")
        self.assertEqual(response.status_code, 401)

    # --- TESTS FOR /customer/<id> (PUT) ---
    def test_update_customer_success(self):
        response = self.client.put(
            f"/customer/{self.customer.id}",
            headers=self.auth_header(),
            json={"name": "John Updated", "phone": "5555555555"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "John Updated")

    def test_update_customer_unauthorized(self):
        # Try to update a different user (simulate different user_id)
        response = self.client.put(
            "/customer/9999",  # ID that doesn’t match user_id
            headers=self.auth_header(),
            json={"name": "Hacker"},
        )
        self.assertEqual(response.status_code, 403)

    # --- TESTS FOR /customer/<id> (DELETE) ---
    def test_delete_customer_success(self):
        response = self.client.delete(
            f"/customer/{self.customer.id}", headers=self.auth_header()
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.get_json())

    def test_delete_customer_unauthorized(self):
        response = self.client.delete("/customer/9999", headers=self.auth_header())
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
