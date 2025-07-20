import requests

BASE_URL = "http://127.0.0.1:5000"
CUSTOMERS_URL = f"{BASE_URL}/customers"
MECHANICS_URL = f"{BASE_URL}/mechanics"
SERVICE_TICKETS_URL = f"{BASE_URL}/service_tickets"
INVENTORY_URL = f"{BASE_URL}/inventory"
ASSIGNMENTS_URL = f"{BASE_URL}/assignments"


def print_response(res):
    print(f"Status Code: {res.status_code}")
    try:
        print("Response:", res.json())
    except Exception:
        print("Response (raw):", res.text)


def test_customers():
    print("\n== Testing Customers API ==")

    payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "test123",
        "phone": "555-9999",
        "address": "123 Test Lane",
    }
    res = requests.post(CUSTOMERS_URL + "/", json=payload)
    print("\n POST /customers")
    print_response(res)

    login_payload = {"email": "testuser@example.com", "password": "test123"}
    res = requests.post(CUSTOMERS_URL + "/login", json=login_payload)
    print("\n POST /customers/login")
    print_response(res)
    token = res.json().get("auth_token") if res.status_code == 200 else None

    print("\n GET /customers")
    res = requests.get(CUSTOMERS_URL)
    print_response(res)

    if token:
        update_payload = {"name": "Updated User"}
        headers = {"Authorization": f"Bearer {token}"}
        res = requests.put(f"{CUSTOMERS_URL}/16", json=update_payload, headers=headers)
        print("\n PUT /customers/16")
        print_response(res)

        res = requests.delete(f"{CUSTOMERS_URL}/16", headers=headers)
        print("\n DELETE /customers/16")
        print_response(res)


def test_mechanics():
    print("\n== Testing Mechanics API ==")

    payload = {
        "name": "Test Mechanic",
        "email": "testmech@example.com",
        "password": "mech123",
        "phone": "555-8888",
        "address": "456 Workshop Rd",
        "salary": 50000.0,
    }
    res = requests.post(MECHANICS_URL + "/", json=payload)
    print("\n POST /mechanics")
    print_response(res)

    login_payload = {"email": "testmech@example.com", "password": "mech123"}
    res = requests.post(MECHANICS_URL + "/login", json=login_payload)
    print("\n POST /mechanics/login")
    print_response(res)
    mech_token = res.json().get("auth_token") if res.status_code == 200 else None

    print("\n GET /mechanics")
    res = requests.get(MECHANICS_URL)
    print_response(res)

    return mech_token


def test_service_tickets(customer_token):
    print("\n== Testing Service Tickets API ==")

    headers = {"Authorization": f"Bearer {customer_token}"}

    payload = {
        "description": "Test service job",
        "vin": "VIN123456799",
        "cost": 199.99,
        "customer_id": 16,
        "service_date": "2025-07-20",
        "status": "Pending",
    }
    res = requests.post(SERVICE_TICKETS_URL + "/", json=payload, headers=headers)
    print("\n POST /service_tickets")
    print_response(res)

    print("\n GET /service_tickets")
    res = requests.get(SERVICE_TICKETS_URL)
    print_response(res)


def test_inventory(mech_token):
    print("\n== Testing Inventory API ==")

    headers = {"Authorization": f"Bearer {mech_token}"}

    payload = {
        "name": "Test Part",
        "description": "A test part for repairs",
        "price": 50.0,
        "quantity": 10,
    }
    res = requests.post(INVENTORY_URL + "/", json=payload, headers=headers)
    print("\n POST /inventory")
    print_response(res)

    print("\n GET /inventory")
    res = requests.get(INVENTORY_URL + "/", headers=headers)
    print_response(res)


def test_service_assignments():
    print("\n== Testing Service Assignments API ==")

    payload = {"service_ticket_id": 17, "mechanic_id": 9, "date_assigned": "2025-07-19"}
    res = requests.post(ASSIGNMENTS_URL + "/", json=payload)
    print("\n POST /assignments")
    print_response(res)

    print("\n GET /assignments")
    res = requests.get(ASSIGNMENTS_URL + "/")
    print_response(res)

    res = requests.delete(f"{ASSIGNMENTS_URL}/?service_ticket_id=17&mechanic_id=9")
    print("\n DELETE /assignments")
    print_response(res)


if __name__ == "__main__":
    test_customers()
    mech_token = test_mechanics()

    res = requests.post(
        CUSTOMERS_URL + "/login",
        json={"email": "testuser@example.com", "password": "test123"},
    )
    customer_token = res.json().get("auth_token") if res.status_code == 200 else None

    if customer_token:
        test_service_tickets(customer_token)

    if mech_token:
        test_inventory(mech_token)

    test_service_assignments()
