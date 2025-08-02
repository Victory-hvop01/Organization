from sqlalchemy.orm import Session
from models import Building, Activity, Phone, Organization


def seed_database(db: Session):
    # Здания
    building1 = Building(
        address="г. Москва, ул. Ленина 1, офис 3",
        latitude=55.755826,
        longitude=37.617300
    )
    building2 = Building(
        address="г. Москва, ул. Гагарина 15",
        latitude=55.752565,
        longitude=37.621258
    )

    # Виды деятельности
    food = Activity(name="Еда")
    meat = Activity(name="Мясная продукция", parent=food)
    dairy = Activity(name="Молочная продукция", parent=food)
    cars = Activity(name="Автомобили")
    trucks = Activity(name="Грузовые", parent=cars)
    cars_light = Activity(name="Легковые", parent=cars)
    parts = Activity(name="Запчасти", parent=cars_light)
    accessories = Activity(name="Аксессуары", parent=cars_light)

    # Организации
    org1 = Organization(
        name="ООО Рога и Копыта",
        building=building1,
        phones=[
            Phone(number="2-222-222"),
            Phone(number="3-333-333")
        ],
        activities=[meat, dairy]
    )
    org2 = Organization(
        name="АвтоМир",
        building=building2,
        phones=[Phone(number="8-923-666-13-13")],
        activities=[trucks, parts]
    )

    db.add_all([
        building1, building2,
        food, meat, dairy, cars, trucks, cars_light, parts, accessories,
        org1, org2
    ])
    db.commit()
    print("Test data seeded successfully")
