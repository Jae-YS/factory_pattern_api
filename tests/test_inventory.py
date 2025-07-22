import unittest
from app import create_app, db
from app.models import Mechanic, Inventory


class InventoryRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and database"""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
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
        with self.app.app_context():
            item = Inventory(
                part_name="Wrench",
                quantity=10,
                description="Adjustable wrench",
                price=15.99,
            )
            db.session.add(item)
            db.session.commit()

        response = self.client.get("/inventory/", headers=self.auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any(i["part_name"] == "Wrench" for i in response.get_json()))

    def test_get_all_inventory_unauthorized(self):
        response = self.client.get("/inventory/")
        self.assertEqual(response.status_code, 401)

    # === TESTS FOR GET /inventory/<id> ===
    def test_get_inventory_item_success(self):
        with self.app.app_context():
            item = Inventory(
                part_name="Hammer",
                quantity=5,
                description="Steel hammer",
                price=12.99,
            )
            db.session.add(item)
            db.session.commit()
            item_id = item.id

        response = self.client.get(f"/inventory/{item_id}", headers=self.auth_header())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["part_name"], "Hammer")

    def test_get_inventory_item_not_found(self):
        response = self.client.get("/inventory/9999", headers=self.auth_header())
        self.assertEqual(response.status_code, 404)

    # === TESTS FOR POST /inventory ===
    def test_create_inventory_item_success(self):
        response = self.client.post(
            "/inventory/",
            headers=self.auth_header(),
            json={
                "part_name": "Screwdriver",
                "quantity": 15,
                "description": "Flathead screwdriver",
                "price": 5.99,
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["part_name"], "Screwdriver")

    def test_create_inventory_item_invalid_payload(self):
        response = self.client.post(
            "/inventory/",
            headers=self.auth_header(),
            json={"quantity": "not-a-number"},
        )
        self.assertEqual(response.status_code, 400)

    # === TESTS FOR PUT /inventory/<id> ===
    def test_update_inventory_item_success(self):
        with self.app.app_context():
            item = Inventory(
                part_name="Drill", quantity=2, description="Electric drill", price=99.99
            )
            db.session.add(item)
            db.session.commit()
            item_id = item.id

        response = self.client.put(
            f"/inventory/{item_id}",
            headers=self.auth_header(),
            json={"part_name": "Cordless Drill", "quantity": 3},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["part_name"], "Cordless Drill")

    def test_update_inventory_item_not_found(self):
        response = self.client.put(
            "/inventory/9999",
            headers=self.auth_header(),
            json={"part_name": "Nonexistent"},
        )
        self.assertEqual(response.status_code, 404)

    def test_update_inventory_item_invalid_payload(self):
        with self.app.app_context():
            item = Inventory(
                part_name="Saw", quantity=4, description="Hand saw", price=20.00
            )
            db.session.add(item)
            db.session.commit()
            item_id = item.id

        response = self.client.put(
            f"/inventory/{item_id}",
            headers=self.auth_header(),
            json={"quantity": "invalid"},
        )
        self.assertEqual(response.status_code, 400)

    # === TESTS FOR DELETE /inventory/<id> ===
    def test_delete_inventory_item_success(self):
        with self.app.app_context():
            item = Inventory(
                part_name="Pliers",
                quantity=6,
                description="Needle-nose pliers",
                price=8.99,
            )
            db.session.add(item)
            db.session.commit()
            item_id = item.id

        response = self.client.delete(
            f"/inventory/{item_id}", headers=self.auth_header()
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_inventory_item_not_found(self):
        response = self.client.delete("/inventory/9999", headers=self.auth_header())
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
