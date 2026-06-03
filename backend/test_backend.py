import sys
from fastapi.testclient import TestClient
from main import app

def test_all():
    # Context manager triggers startup events
    with TestClient(app) as client:
        print("\n--- Testing /health ---")
        response = client.get("/health")
        print(response.json())
        
        print("\n--- Testing /model/info ---")
        response = client.get("/model/info")
        print(response.json())
        
        print("\n--- Testing /current/Hanoi ---")
        response = client.get("/current/Hanoi")
        data = response.json()
        print("Success:", data.get("success"))
        # Print only safe ascii or handle encode for Windows console
        print(str(data)[:200] + "...")

        print("\n--- Testing /predict Hanoi ---")
        response = client.post("/predict", json={"city": "Hanoi"})
        data = response.json()
        print(str(data)[:200] + "...")

if __name__ == "__main__":
    # configure python to output utf-8 safely
    sys.stdout.reconfigure(encoding='utf-8')
    test_all()
