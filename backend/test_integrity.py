import os
import django
import requests
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

BASE_URL = "http://localhost:8000"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzYxODYzNDY4LCJpYXQiOjE3NjE4NjE2NjgsImp0aSI6ImUyM2UwNDEyYzhhODRmNzVhMGMxM2ExY2NkNDA5ZmIxIiwidXNlcl9pZCI6MSwiZW1haWwiOiJtZXZhbGVuY2lhY0B1am1kLmVkdS5zdiJ9.mp1K9tfisC-lwuDAjdWmlNLrsJ0yGr2ttui62eMXB88"  # 🔥 REEMPLAZA

headers = {"Authorization": f"Bearer {TOKEN}"}

def test_system_integrity():
    """Probar que todo el sistema funciona después de la limpieza"""
    
    print("🧪 PROBANDO INTEGRIDAD DEL SISTEMA...")
    
    endpoints = [
        ("GET", "/api/users/users/me/", None),
        ("GET", "/api/permissions/roles/", None),
        ("GET", "/api/organization/departments/", None),
        ("GET", "/api/organization/assignments/my_assignment/", None),
        ("POST", "/api/permissions/assign-role/", {
            "user_id": 1,
            "role_id": 1,
            "department_id": 1
        }),
    ]
    
    for method, endpoint, data in endpoints:
        print(f"\n🔍 {method} {endpoint}")
        
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(f"{BASE_URL}{endpoint}", json=data, headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"   ✅ Éxito")
            else:
                print(f"   ❌ Error {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   💥 Excepción: {e}")

if __name__ == "__main__":
    if TOKEN != "tu_token_jwt_aqui":
        test_system_integrity()
    else:
        print("❌ Configura el token JWT para probar")