import json
from sqlalchemy.orm import Session

from app.models.config_room_costs import ConfigRoomCost
from app.models.alianzas import Alliance
from app.models.crafting import CatalogoItem
from app.models.inventory import Inventory
from app.models.jugador import Jugador
from app.models.ship import Ship
from app.models.ship_rooms import ShipRoom
from app.models.user import User
from app.services.auth import hash_password

DEMO_CREDENTIALS = {
    "username": "demo_captain",
    "email": "demo@godot.local",
    "password": "demo1234",
}

DEMO_RESOURCE_ITEMS = [
    {
        "id": 1,
        "nombre": "Kliptium",
        "descripcion": "Mineral base para combustible y aleaciones.",
        "tipo": "recurso",
        "rareza": "comun",
        "imagen_url": "/assets/resources/kliptium.png",
    },
    {
        "id": 3,
        "nombre": "Material Orgánico",
        "descripcion": "Biomasa esencial para suministros de supervivencia.",
        "tipo": "recurso",
        "rareza": "comun",
        "imagen_url": "/assets/resources/organic.png",
    },
    {
        "id": 4,
        "nombre": "Litium",
        "descripcion": "Componente de alta densidad para baterías.",
        "tipo": "recurso",
        "rareza": "comun",
        "imagen_url": "/assets/resources/litium.png",
    },
    {
        "id": 5,
        "nombre": "Copper",
        "descripcion": "Metal conductor usado en fabricación y cableado.",
        "tipo": "recurso",
        "rareza": "comun",
        "imagen_url": "/assets/resources/copper.png",
    },
    {
        "id": 7,
        "nombre": "H2O",
        "descripcion": "Agua procesada para soporte vital y operaciones básicas.",
        "tipo": "recurso",
        "rareza": "comun",
        "imagen_url": "/assets/resources/h2o.png",
    },
]

DEMO_ROOM_COSTS = [
    {
        "room_id": "Fabrica",
        "target_level": 2,
        "cost_data": [{"id": 1, "quantity": 20}, {"id": 5, "quantity": 15}],
    },
    {
        "room_id": "Armeria",
        "target_level": 2,
        "cost_data": [{"id": 1, "quantity": 25}, {"id": 4, "quantity": 10}],
    },
]

DEMO_ROOMS = [
    {"room_id": "Fabrica", "level": 1},
    {"room_id": "Armeria", "level": 1},
]

DEMO_INVENTORY = [
    {"resource_id": 1, "quantity": 20},
    {"resource_id": 3, "quantity": 10},
    {"resource_id": 4, "quantity": 10},
    {"resource_id": 5, "quantity": 10},
    {"resource_id": 7, "quantity": 20},
]

DEMO_ALLIANCES = [
    {
        "name": "Nova Orion",
        "tag": "NOVA",
        "level": 7,
        "members_count": 42,
        "max_members": 100,
        "power": "12850",
        "lang": "ES",
        "puntos_prestigio": 9800,
    },
    {
        "name": "Cobalt Union",
        "tag": "CBLT",
        "level": 4,
        "members_count": 18,
        "max_members": 80,
        "power": "6420",
        "lang": "ES",
        "puntos_prestigio": 3100,
    },
    {
        "name": "Sideral Forge",
        "tag": "FORG",
        "level": 5,
        "members_count": 26,
        "max_members": 90,
        "power": "8910",
        "lang": "ES",
        "puntos_prestigio": 4700,
    },
    {
        "name": "Eclipse Vanguard",
        "tag": "ECLP",
        "level": 6,
        "members_count": 31,
        "max_members": 120,
        "power": "10420",
        "lang": "ES",
        "puntos_prestigio": 6100,
    },
    {
        "name": "Helios Pact",
        "tag": "HELI",
        "level": 3,
        "members_count": 12,
        "max_members": 60,
        "power": "3880",
        "lang": "ES",
        "puntos_prestigio": 1900,
    },
    {
        "name": "Iron Nebula",
        "tag": "IRON",
        "level": 8,
        "members_count": 54,
        "max_members": 150,
        "power": "15900",
        "lang": "ES",
        "puntos_prestigio": 12100,
    },
    {
        "name": "Solaris Core",
        "tag": "SOLR",
        "level": 2,
        "members_count": 9,
        "max_members": 50,
        "power": "2240",
        "lang": "ES",
        "puntos_prestigio": 760,
    },
]


def seed_demo_data(db: Session):
    user = db.query(User).filter(User.email == DEMO_CREDENTIALS["email"]).first()
    created_user = False

    if not user:
        user = User(
            username=DEMO_CREDENTIALS["username"],
            email=DEMO_CREDENTIALS["email"],
            password_hash=hash_password(DEMO_CREDENTIALS["password"]),
        )
        db.add(user)
        db.flush()
        created_user = True

    player = db.query(Jugador).filter(Jugador.user_id == user.id).first()
    created_player = False
    if not player:
        player = Jugador(user_id=user.id, nickname=DEMO_CREDENTIALS["username"])
        db.add(player)
        db.flush()
        created_player = True

    ship = db.query(Ship).filter(Ship.owner_id == user.id).first()
    created_ship = False
    if not ship:
        ship = Ship(
            owner_id=user.id,
            current_pos_x=150,
            current_pos_y=340,
            start_pos_x=150,
            start_pos_y=340,
            end_pos_x=150,
            end_pos_y=340,
            is_moving=False,
        )
        db.add(ship)
        created_ship = True

    for item in DEMO_RESOURCE_ITEMS:
        catalog_item = db.query(CatalogoItem).filter(CatalogoItem.id == item["id"]).first()
        if not catalog_item:
            db.add(CatalogoItem(**item))

    for room_cost in DEMO_ROOM_COSTS:
        existing_cost = db.query(ConfigRoomCost).filter(
            ConfigRoomCost.room_id == room_cost["room_id"],
            ConfigRoomCost.target_level == room_cost["target_level"],
        ).first()
        if not existing_cost:
            db.add(
                ConfigRoomCost(
                    room_id=room_cost["room_id"],
                    target_level=room_cost["target_level"],
                    cost_data=json.dumps(room_cost["cost_data"]),
                )
            )

    for room in DEMO_ROOMS:
        existing_room = db.query(ShipRoom).filter(
            ShipRoom.player_id == player.id,
            ShipRoom.room_id == room["room_id"],
        ).first()
        if not existing_room:
            db.add(ShipRoom(player_id=player.id, room_id=room["room_id"], level=room["level"]))

    for resource in DEMO_INVENTORY:
        existing_inventory = db.query(Inventory).filter(
            Inventory.player_id == player.id,
            Inventory.resource_id == resource["resource_id"],
        ).first()
        if existing_inventory:
            existing_inventory.quantity = max(existing_inventory.quantity, resource["quantity"])
        else:
            db.add(
                Inventory(
                    player_id=player.id,
                    resource_id=resource["resource_id"],
                    quantity=resource["quantity"],
                )
            )

    alliances_created = []
    seeded_alliances = []
    for alliance_data in DEMO_ALLIANCES:
        existing_alliance = db.query(Alliance).filter(
            Alliance.name == alliance_data["name"],
            Alliance.tag == alliance_data["tag"],
        ).first()
        if not existing_alliance:
            existing_alliance = Alliance(**alliance_data)
            db.add(existing_alliance)
            alliances_created.append(alliance_data["name"])
        seeded_alliances.append(existing_alliance)

    if player.alliance_id is None and seeded_alliances:
        player.alliance_id = seeded_alliances[0].id
        seeded_alliances[0].members_count = max(seeded_alliances[0].members_count or 0, 1)

    db.commit()
    db.refresh(user)

    return {
        "status": "success",
        "demo_user": {
            "username": DEMO_CREDENTIALS["username"],
            "email": DEMO_CREDENTIALS["email"],
            "password": DEMO_CREDENTIALS["password"],
        },
        "created": {
            "user": created_user,
            "player": created_player,
            "ship": created_ship,
        },
        "alliances_seeded": alliances_created,
        "player_alliance_id": player.alliance_id,
        "player_id": player.id,
    }