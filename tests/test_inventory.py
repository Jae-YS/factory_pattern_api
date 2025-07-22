import unittest
from app import create_app, db
from app.models import Mechanic, Inventory
from flask import Flask


class InventoryRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and database"""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create test mechanic
            self.mechanic = Mechanic(
                name="Bob Wrench",
                email="bob@example.com",
                phone="555-0001",
                address="Garage Rd",
                salary=40000,
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
            json={"email": "bob@example.com", "password": "password123"},
        )
        data = response.get_json()
        return data.get("auth_token")

    def auth_header(self):
        return {"Authorization": f"Bearer {self.auth_token}"}

    # === TESTS FOR GET /inventory ===
    def test_get_all_inventory_success(self):
        # Add inventory item
        with self.app.app_context():
            item = Inventory(
                name="Wrench", quantity=10, description="Adjustable wrench"
            )
            db.session.add(item)
            db.session.commit()

        response = self.client.get("/inventory/", headers=self.auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(i["name"] == "Wrench" for i in response.get_json()))

    def test_get_all_inventory_unauthorized(self):
        response = self.client.get("/inventory/")
        self.assertEqual(response.status_code, 401)

    # === TESTS FOR GET /inventory/<id> ===
    def test_get_inventory_item_success(self):
        with self.app.app_context():
            item = Inventory(name="Hammer", quantity=5, description="Steel hammer")
            db.session.add(item)
            db.session.commit()

        response = self.client.get(f"/inventory/{item.id}", headers=self.auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "Hammer")

    def test_get_inventory_item_not_found(self):
        response = self.client.get("/inventory/9999", headers=self.auth_header())
        self.assertEqual(response.status_code, 404)

    # === TESTS FOR POST /inventory ===
    def test_create_inventory_item_success(self):
        response = self.client.post(
            "/inventory/",
            headers=self.auth_header(),
            json={
                "name": "Screwdriver",
                "quantity": 15,
                "description": "Flathead screwdriver",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["name"], "Screwdriver")

    def test_create_inventory_item_invalid_payload(self):
        response = self.client.post(
            "/inventory/",
            headers=self.auth_header(),
            json={"quantity": "not-a-number"},  # invalid data
        )
        self.assertEqual(response.status_code, 400)

    # === TESTS FOR PUT /inventory/<id> ===
    def test_update_inventory_item_success(self):
        with self.app.app_context():
            item = Inventory(name="Drill", quantity=2, description="Electric drill")
            db.session.add(item)
            db.session.commit()

        response = self.client.put(
            f"/inventory/{item.id}",
            headers=self.auth_header(),
            json={"name": "Cordless Drill", "quantity": 3},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["name"], "Cordless Drill")

    def test_update_inventory_item_not_found(self):
        response = self.client.put(
            "/inventory/9999",
            headers=self.auth_header(),
            json={"name": "Nonexistent"},
        )
        self.assertEqual(response.status_code, 404)

    def test_update_inventory_item_invalid_payload(self):
        with self.app.app_context():
            item = Inventory(name="Saw", quantity=4)
            db.session.add(item)
            db.session.commit()

        response = self.client.put(
            f"/inventory/{item.id}",
            headers=self.auth_header(),
            json={"quantity": "invalid"},  # invalid data
        )
        self.assertEqual(response.status_code, 400)

    # === TESTS FOR DELETE /inventory/<id> ===
    def test_delete_inventory_item_success(self):
        with self.app.app_context():
            item = Inventory(name="Pliers", quantity=6)
            db.session.add(item)
            db.session.commit()

        response = self.client.delete(
            f"/inventory/{item.id}", headers=self.auth_header()
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_inventory_item_not_found(self):
        response = self.client.delete("/inventory/9999", headers=self.auth_header())
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
