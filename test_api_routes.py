import requests

BASE_URL = "http://127.0.0.1:5000"


def debug_response(res):
    print("Status Code:", res.status_code)
    try:
        print("JSON:", res.json())
    except Exception:
        print("Raw Response:", res.text)


def safe_json(response):
    """Helper to handle non-JSON responses."""
    try:
        return response.json()
    except ValueError:
        return {"non_json_response": response.text}


def test_customers():
    print("\n--- Testing Customers ---\n")
    # Create customer
    customer_data = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "123-456-7890",
        "address": "123 Main St",
    }
    res = requests.post(f"{BASE_URL}/customers/", json=customer_data)
    print("\nCreate Customer:")
    debug_response(res)

    # Handle duplicate
    if res.status_code == 409:
        print("Customer already exists, fetching existing customer...")
        res = requests.get(f"{BASE_URL}/customers/")
        customers = safe_json(res)
        customer_id = next(
            (c["id"] for c in customers if c["email"] == customer_data["email"]), None
        )
    elif res.status_code == 201:
        customer_id = res.json().get("id")
    else:
        print("Failed to create customer, stopping test.")
        return None

    # Get all customers
    res = requests.get(f"{BASE_URL}/customers/")
    print("Get All Customers:", res.status_code, safe_json(res))

    return customer_id


def test_mechanics(skip_delete=False):
    print("\n--- Testing Mechanics ---\n")
    mechanic_data = {
        "name": "John Wrench",
        "email": "john@example.com",
        "phone": "987-654-3210",
        "address": "456 Elm St",
        "salary": 55000.00,
    }

    # Check if mechanic already exists
    res = requests.get(f"{BASE_URL}/mechanics/")
    mechanics = safe_json(res)
    mechanic = next(
        (m for m in mechanics if m["email"] == mechanic_data["email"]), None
    )

    if mechanic:
        print("Mechanic already exists, skipping create.")
        mechanic_id = mechanic["id"]
    else:
        res = requests.post(f"{BASE_URL}/mechanics/", json=mechanic_data)
        print("Create Mechanic:", res.status_code, safe_json(res))
        if res.status_code == 201:
            mechanic_id = res.json().get("id")
        else:
            print("Failed to create mechanic, stopping test.")
            return None

    # Update mechanic
    update_data = {"salary": 60000.00}
    res = requests.put(f"{BASE_URL}/mechanics/{mechanic_id}", json=update_data)
    print("Update Mechanic:", res.status_code, safe_json(res))

    # Delete only if requested
    if not skip_delete:
        res = requests.delete(f"{BASE_URL}/mechanics/{mechanic_id}")
        print("Delete Mechanic:", res.status_code, safe_json(res))

    return mechanic_id


def test_service_tickets(customer_id, mechanic_id):
    print("\n--- Testing Service Tickets ---\n")
    # Create service ticket
    ticket_data = {
        "service_date": "2025-07-20",
        "vin": "1HGCM82633A004352",
        "description": "Brake inspection",
        "status": "open",
        "cost": 120.50,
        "date_created": "2025-07-19",
        "customer_id": customer_id,
    }
    res = requests.post(f"{BASE_URL}/service_tickets/", json=ticket_data)
    print("Create Service Ticket:", res.status_code, safe_json(res))

    if res.status_code != 201:
        print("Failed to create service ticket, stopping test.")
        return None
    ticket_id = res.json()["id"]

    # Get all service tickets
    res = requests.get(f"{BASE_URL}/service_tickets/")
    print("Get All Service Tickets:", res.status_code, safe_json(res))
    debug_response(res)

    # Assign mechanic
    res = requests.put(
        f"{BASE_URL}/service_tickets/{ticket_id}/assign-mechanic/{mechanic_id}"
    )
    print("Assign Mechanic:", res.status_code, safe_json(res))

    # Remove mechanic
    res = requests.put(
        f"{BASE_URL}/service_tickets/{ticket_id}/remove-mechanic/{mechanic_id}"
    )
    print("Remove Mechanic:", res.status_code, safe_json(res))


if __name__ == "__main__":
    # Run customer and mechanic tests
    customer_id = test_customers()
    mechanic_id = test_mechanics(skip_delete=True)  # Keep mechanic for ticket test

    if customer_id and mechanic_id:
        test_service_tickets(customer_id, mechanic_id)

    # Cleanup mechanic after service ticket test
    if mechanic_id:
        res = requests.delete(f"{BASE_URL}/mechanics/{mechanic_id}")
        print("\nCleanup: Delete Mechanic:", res.status_code, safe_json(res))
