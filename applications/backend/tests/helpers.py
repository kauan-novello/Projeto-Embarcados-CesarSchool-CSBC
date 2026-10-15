SYSTEM_PAYLOAD = {
    "name": "Instalação Residencial",
    "location": "Recife, PE",
    "installed_power_kw": 4.5,
    "inverter_type": "on_grid",
}

PLANT_PAYLOAD = {
    "name": "Usina",
    "location": "Palmares, PE",
    "installed_power_kw": 36,
    "inverter_type": "on_grid",
}

PASSWORD = "s3cret-pw"


def signup_and_create_system(client, email="owner@example.com", payload=SYSTEM_PAYLOAD):
    client.post("/auth/signup", json={"name": "User", "email": email, "password": PASSWORD})
    return client.post("/systems", json=payload).json()


def signup_and_create_plant(client, email="owner@example.com"):
    return signup_and_create_system(client, email, PLANT_PAYLOAD)
