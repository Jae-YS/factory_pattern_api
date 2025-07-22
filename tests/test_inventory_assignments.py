import unittest
from app import create_app, db
from app.models import Inventory, ServiceTicket, InventoryServiceTicket
from flask import Flask


class InventoryAssignmentRoutesTestCase(unittest.TestCase):
    def setUp(self):
        """Set up test client and in-memory database"""
        self.app = create_app("testing")
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()
            # Create related service ticket and inventory item
            self.ticket = ServiceTicket(
                title="Engine Repair", description="Fix engine noise", customer_id=None
            )
            self.inventory = Inventory(
                name="Engine Oil", quantity=100, description="5W-30 synthetic oil"
            )
            db.session.add_all([self.ticket, self.inventory])
            db.session.commit()

    def tearDown(self):
        """Tear down database"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    # === TESTS FOR POST /inventory_assignments ===
    def test_create_inventory_assignment_success(self):
        response = self.client.post(
            "/inventory_assignment/",
            json={
                "service_ticket_id": self.ticket.id,
                "inventory_id": self.inventory.id,
                "quantity": 2,
            },
        )
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertEqual(data["service_ticket_id"], self.ticket.id)
        self.assertEqual(data["inventory_id"], self.inventory.id)
        self.assertEqual(data["quantity"], 2)

    def test_create_inventory_assignment_duplicate(self):
        # First create
        self.client.post(
            "/inventory_assignment/",
            json={
                "service_ticket_id": self.ticket.id,
                "inventory_id": self.inventory.id,
                "quantity": 1,
            },
        )
        # Try duplicate
        response = self.client.post(
            "/inventory_assignment/",
            json={
                "service_ticket_id": self.ticket.id,
                "inventory_id": self.inventory.id,
                "quantity": 3,
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.get_json())

    # === TESTS FOR GET /inventory_assignments ===
    def test_get_all_inventory_assignments_success(self):
        # Create assignment
        with self.app.app_context():
            assignment = InventoryServiceTicket(
                service_ticket_id=self.ticket.id,
                inventory_id=self.inventory.id,
                quantity=5,
            )
            db.session.add(assignment)
            db.session.commit()

        response = self.client.get("/inventory_assignment/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            any(a["service_ticket_id"] == self.ticket.id for a in response.get_json())
        )

    # === TESTS FOR PUT /inventory_assignments ===
    def test_update_inventory_assignment_success(self):
        # Create assignment
        with self.app.app_context():
            assignment = InventoryServiceTicket(
                service_ticket_id=self.ticket.id,
                inventory_id=self.inventory.id,
                quantity=1,
            )
            db.session.add(assignment)
            db.session.commit()

        response = self.client.put(
            "/inventory_assignment/",
            json={
                "service_ticket_id": self.ticket.id,
                "inventory_id": self.inventory.id,
                "quantity": 10,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["quantity"], 10)

    def test_update_inventory_assignment_not_found(self):
        response = self.client.put(
            "/inventory_assignment/",
            json={
                "service_ticket_id": 9999,  # Non-existent
                "inventory_id": 9999,
                "quantity": 5,
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())

    # === TESTS FOR DELETE /inventory_assignments ===
    def test_delete_inventory_assignment_success(self):
        # Create assignment
        with self.app.app_context():
            assignment = InventoryServiceTicket(
                service_ticket_id=self.ticket.id,
                inventory_id=self.inventory.id,
                quantity=2,
            )
            db.session.add(assignment)
            db.session.commit()

        response = self.client.delete(
            f"/inventory_assignment/?service_ticket_id={self.ticket.id}&inventory_id={self.inventory.id}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.get_json())

    def test_delete_inventory_assignment_not_found(self):
        response = self.client.delete(
            "/inventory_assignment/?service_ticket_id=9999&inventory_id=9999"
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.get_json())


if __name__ == "__main__":
    unittest.main()
