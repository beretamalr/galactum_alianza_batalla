# app/services/map_service.py
from sqlalchemy.orm import Session, joinedload
from app.models.ship import Ship
from app.models.user import User

def get_asteroids():
    """
    Devuelve una lista mock de asteroides.
    """
    return [
        {"id": "AST-001", "position": {"x": 150, "y": 340}, "resourceType": "Roderitium"},
        {"id": "AST-002", "position": {"x": 800, "y": 600}, "resourceType": "Kliptium"},
        {"id": "AST-003", "position": {"x": 450, "y": 120}, "resourceType": "Ore"}
    ]

def get_ships(db: Session):
    """
    Devuelve una lista simplificada de naves y sus posiciones.
    """
    ships_db = db.query(Ship).options(
        joinedload(Ship.owner).joinedload(User.jugador)
    ).all()

    ships_list = []
    for ship in ships_db:
        if ship.owner and ship.owner.jugador:
            ships_list.append({
                "id": ship.owner.jugador.nickname,
                "position": {"x": ship.current_pos_x, "y": ship.current_pos_y}
            })
    return ships_list

def set_player_move(db: Session, player_id: int, target_position: dict):
    """
    Establece una nueva posición objetivo para la nave de un jugador.
    """
    # Buscamos la nave a través de la relación Jugador -> User -> Ship
    ship_to_move = db.query(Ship).join(User).join(User.jugador).filter(
        User.jugador.has(id=player_id)
    ).first()

    if not ship_to_move:
        raise Exception("Nave no encontrada para el jugador especificado.")

    # Actualizamos las coordenadas objetivo
    ship_to_move.end_pos_x = target_position['x'] # type: ignore
    ship_to_move.end_pos_y = target_position['y'] # type: ignore
    # Podríamos añadir más lógica aquí, como poner is_moving = True

    db.commit()
    return {"status": "success", "message": f"Nuevo destino establecido para el jugador {player_id}."}