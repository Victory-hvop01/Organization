from fastapi import FastAPI, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from geopy.distance import geodesic
from .database import get_db, create_tables
from .models import Organization as OrganizationModel, Building as BuildingModel, Activity as ActivityModel, \
    Phone as PhoneModel
from .schemas import Organization as OrganizationSchema, OrganizationCreate, PhoneBase, Activity as ActivitySchema, \
    Building as BuildingSchema
from .seed_data import seed_database
import os

app = FastAPI(
    title="Company Directory API",
    description="API для справочника организаций, зданий и видов деятельности",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Конфигурация
API_KEY = os.getenv("API_KEY", "SECRET_KEY123")


@app.on_event("startup")
def startup_event():
    """Событие запуска приложения: создает таблицы и заполняет тестовыми данными"""
    create_tables()
    db = next(get_db())
    try:
        seed_database(db)
        print("✅ Database seeded successfully")
    except Exception as e:
        print(f"❌ Error seeding database: {str(e)}")
    finally:
        db.close()


def verify_api_key(api_key: str = Header(..., alias="X-API-Key")):
    """Проверка API ключа для аутентификации"""
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return True


@app.get("/buildings/{building_id}/organizations",
         response_model=list[OrganizationSchema],
         summary="Организации в здании",
         description="Получение списка всех организаций, расположенных в указанном здании",
         tags=["Организации"])
def get_orgs_by_building(
        building_id: int,
        db: Session = Depends(get_db),
        _: bool = Depends(verify_api_key)
):
    """
    Получает список организаций по ID здания.

    - **building_id**: ID здания
    - Возвращает список организаций
    """
    return db.query(OrganizationModel).filter(OrganizationModel.building_id == building_id).all()


@app.get("/activities/{activity_id}/organizations",
         response_model=list[OrganizationSchema],
         summary="Организации по виду деятельности",
         description="Получение списка организаций, занимающихся указанным видом деятельности",
         tags=["Организации"])
def get_orgs_by_activity(
        activity_id: int,
        db: Session = Depends(get_db),
        _: bool = Depends(verify_api_key)
):
    """
    Получает список организаций по ID вида деятельности.

    - **activity_id**: ID вида деятельности
    - Возвращает список организаций
    """
    activity = db.query(ActivityModel).get(activity_id)
    if not activity:
        return []
    return activity.organizations


@app.get("/organizations/nearby",
         response_model=list[OrganizationSchema],
         summary="Организации в радиусе",
         description="Поиск организаций в заданном радиусе от указанной точки",
         tags=["Организации"])
def get_orgs_in_radius(
        lat: float = Query(..., description="Широта центра", example=55.755826),
        lon: float = Query(..., description="Долгота центра", example=37.617300),
        radius: float = Query(1000, description="Радиус в метрах", example=500),
        db: Session = Depends(get_db),
        _: bool = Depends(verify_api_key)
):
    """
    Находит организации в заданном радиусе от географической точки.

    - **lat**: Широта центра
    - **lon**: Долгота центра
    - **radius**: Радиус поиска в метрах
    - Возвращает список организаций
    """
    orgs = db.query(OrganizationModel).join(BuildingModel).all()
    center = (lat, lon)
    return [
        org for org in orgs
        if geodesic(center, (org.building.latitude, org.building.longitude)).meters <= radius
    ]


@app.get("/organizations/{org_id}",
         response_model=OrganizationSchema,
         summary="Информация об организации",
         description="Получение полной информации об организации по её ID",
         tags=["Организации"])
def get_organization(
        org_id: int,
        db: Session = Depends(get_db),
        _: bool = Depends(verify_api_key)
):
    """
    Получает информацию об организации по её ID.

    - **org_id**: ID организации
    - Возвращает полную информацию об организации
    """
    org = db.query(OrganizationModel).get(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


@app.get("/organizations/search/activity",
         response_model=list[OrganizationSchema],
         summary="Поиск по виду деятельности",
         description="Поиск организаций по виду деятельности с учетом иерархии",
         tags=["Поиск"])
def search_orgs_by_activity_tree(
        activity_name: str = Query(..., description="Название вида деятельности", example="Еда"),
        db: Session = Depends(get_db),
        _: bool = Depends(verify_api_key)
):
    """
    Находит организации по виду деятельности, включая все дочерние виды.

    - **activity_name**: Название вида деятельности
    - Возвращает список организаций
    """
    root_activity = db.query(ActivityModel).filter(
        ActivityModel.name.ilike(f"%{activity_name}%"),
        ActivityModel.parent_id == None
    ).first()

    if not root_activity:
        return []

    all_activity_ids = get_all_children_ids(db, root_activity.id)

    return db.query(OrganizationModel).join(OrganizationModel.activities).filter(
        ActivityModel.id.in_(all_activity_ids)
    ).all()


def get_all_children_ids(db: Session, activity_id: int, level=1, max_level=3):
    """Рекурсивно получает все дочерние ID вида деятельности (до 3 уровня вложенности)"""
    if level > max_level:
        return []

    activity = db.query(ActivityModel).get(activity_id)
    if not activity:
        return []

    ids = [activity_id]
    for child in activity.children:
        ids.extend(get_all_children_ids(db, child.id, level + 1, max_level))
    return ids


@app.get("/organizations/search/name",
         response_model=list[OrganizationSchema],
         summary="Поиск по названию организации",
         description="Поиск организаций по части названия",
         tags=["Поиск"])
def search_orgs_by_name(
        name: str = Query(..., description="Часть названия организации", example="Рога"),
        db: Session = Depends(get_db),
        _: bool = Depends(verify_api_key)
):
    """
    Находит организации по части названия.

    - **name**: Часть названия организации
    - Возвращает список организаций
    """
    return db.query(OrganizationModel).filter(
        OrganizationModel.name.ilike(f"%{name}%")
    ).all()


@app.post("/organizations/",
          response_model=OrganizationSchema,
          summary="Создание организации",
          description="Добавление новой организации в справочник",
          tags=["Организации"])
def create_organization(
        organization: OrganizationCreate,
        db: Session = Depends(get_db),
        _: bool = Depends(verify_api_key)
):
    """
    Создает новую организацию.

    Параметры запроса:
    - **name**: Название организации
    - **building_id**: ID здания
    - **phones**: Список телефонов
    - **activity_ids**: Список ID видов деятельности

    Возвращает созданную организацию
    """
    db_org = OrganizationModel(
        name=organization.name,
        building_id=organization.building_id
    )
    db.add(db_org)
    db.commit()
    db.refresh(db_org)

    for phone in organization.phones:
        db_phone = PhoneModel(number=phone.number, organization_id=db_org.id)
        db.add(db_phone)

    for activity_id in organization.activity_ids:
        activity = db.query(ActivityModel).get(activity_id)
        if activity:
            db_org.activities.append(activity)

    db.commit()
    return db_org


@app.get("/", include_in_schema=False)
def root():
    """Перенаправление на документацию"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/docs")