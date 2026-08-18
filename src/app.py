"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Character, Location, Favorite_location, Favorite_character
from sqlalchemy import select
 
app = Flask(__name__)
app.url_map.strict_slashes = False
 
 
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
 
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)
 
# Usuario por defecto, porque el proyecto todavia no tiene sistema de login
CURRENT_USER_ID = 1
 
 
def get_current_user_id():
    """Devuelve el user_id del query param si viene, si no el usuario por defecto."""
    return int(request.args.get("user_id", CURRENT_USER_ID))
 
 
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code
 
 
@app.route('/')
def sitemap():
    return generate_sitemap(app)
 

 
@app.route("/users", methods=["GET"])
def get_users():
    users = db.session.execute(select(User)).scalars().all()
    return jsonify([user.serialize() for user in users]), 200
 
 
@app.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "usuario no existe"}), 404
    return jsonify(user.serialize()), 200
 
 
@app.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email y password son requeridos"}), 400
    existe_user = db.session.execute(select(User).where(
        User.email == data.get("email"))).scalar_one_or_none()
    if existe_user:
        return jsonify({"error": "Ya existe un usuario con este email"}), 400
    new_user = User(email=data.get("email"), password=data.get("password"))
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.serialize()), 201
 
 
@app.route("/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "usuario no existe"}), 404
    data = request.get_json()
    if data.get("email"):
        user.email = data.get("email")
    if data.get("password"):
        user.password = data.get("password")
    db.session.commit()
    return jsonify(user.serialize()), 200
 
 
@app.route("/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "usuario no existe"}), 404
    # primero se borran sus favoritos, si no la base de datos rechaza el borrado
    fav_personajes = db.session.execute(select(Favorite_character).where(
        Favorite_character.user_id == user_id)).scalars().all()
    fav_locaciones = db.session.execute(select(Favorite_location).where(
        Favorite_location.user_id == user_id)).scalars().all()
    for favorito in fav_personajes + fav_locaciones:
        db.session.delete(favorito)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"msg": "usuario eliminado con exito"}), 200
 
 

 
@app.route("/people", methods=["GET"])
def get_people():
    characters = db.session.execute(select(Character)).scalars().all()
    return jsonify([character.serialize() for character in characters]), 200
 
 
@app.route("/people/<int:people_id>", methods=["GET"])
def get_person(people_id):
    character = db.session.get(Character, people_id)
    if character is None:
        return jsonify({"error": "personaje no existe"}), 404
    return jsonify(character.serialize()), 200
 
 
@app.route("/people", methods=["POST"])
def create_person():
    data = request.get_json()
    if not data.get("name"):
        return jsonify({"error": "El nombre es obligatorio"}), 400
    existe = db.session.execute(select(Character).where(
        Character.name == data.get("name"))).scalar_one_or_none()
    if existe:
        return jsonify({"error": "Ya existe un personaje con ese nombre"}), 400
    new_character = Character(
        name=data.get("name"), quote=data.get("quote", ""))
    db.session.add(new_character)
    db.session.commit()
    return jsonify(new_character.serialize()), 201
 
 
@app.route("/people/<int:people_id>", methods=["PUT"])
def update_person(people_id):
    character = db.session.get(Character, people_id)
    if character is None:
        return jsonify({"error": "personaje no existe"}), 404
    data = request.get_json()
    if data.get("name"):
        character.name = data.get("name")
    if data.get("quote"):
        character.quote = data.get("quote")
    db.session.commit()
    return jsonify(character.serialize()), 200
 
 
@app.route("/people/<int:people_id>", methods=["DELETE"])
def delete_person(people_id):
    character = db.session.get(Character, people_id)
    if character is None:
        return jsonify({"error": "personaje no existe"}), 404
    favoritos = db.session.execute(select(Favorite_character).where(
        Favorite_character.character_id == people_id)).scalars().all()
    for favorito in favoritos:
        db.session.delete(favorito)
    db.session.delete(character)
    db.session.commit()
    return jsonify({"msg": "personaje eliminado con exito"}), 200
 
 

 
@app.route("/planets", methods=["GET"])
def get_planets():
    locations = db.session.execute(select(Location)).scalars().all()
    return jsonify([location.serialize() for location in locations]), 200
 
 
@app.route("/planets/<int:planet_id>", methods=["GET"])
def get_planet(planet_id):
    location = db.session.get(Location, planet_id)
    if location is None:
        return jsonify({"error": "esta locacion no existe"}), 404
    return jsonify(location.serialize()), 200
 
 
@app.route("/planets", methods=["POST"])
def create_planet():
    data = request.get_json()
    if not data.get("name") or not data.get("use"):
        return jsonify({"error": "El name y el use son obligatorios"}), 400
    existe = db.session.execute(select(Location).where(
        Location.name == data.get("name"))).scalar_one_or_none()
    if existe:
        return jsonify({"error": "Ya existe una locacion con ese nombre"}), 400
    new_location = Location(name=data.get("name"), use=data.get("use"))
    db.session.add(new_location)
    db.session.commit()
    return jsonify(new_location.serialize()), 201
 
 
@app.route("/planets/<int:planet_id>", methods=["PUT"])
def update_planet(planet_id):
    location = db.session.get(Location, planet_id)
    if location is None:
        return jsonify({"error": "esta locacion no existe"}), 404
    data = request.get_json()
    if data.get("name"):
        location.name = data.get("name")
    if data.get("use"):
        location.use = data.get("use")
    db.session.commit()
    return jsonify(location.serialize()), 200
 
 
@app.route("/planets/<int:planet_id>", methods=["DELETE"])
def delete_planet(planet_id):
    location = db.session.get(Location, planet_id)
    if location is None:
        return jsonify({"error": "esta locacion no existe"}), 404
    favoritos = db.session.execute(select(Favorite_location).where(
        Favorite_location.location_id == planet_id)).scalars().all()
    for favorito in favoritos:
        db.session.delete(favorito)
    db.session.delete(location)
    db.session.commit()
    return jsonify({"msg": "locacion eliminada con exito"}), 200
 
 

 
@app.route("/users/favorites", methods=["GET"])
def get_user_favorites():
    user_id = get_current_user_id()
    location_fav = db.session.execute(select(Favorite_location).where(
        Favorite_location.user_id == user_id)).scalars().all()
    character_fav = db.session.execute(select(Favorite_character).where(
        Favorite_character.user_id == user_id)).scalars().all()
    return jsonify({
        "favorite_location": [location.serialize() for location in location_fav],
        "favorite_character": [character.serialize() for character in character_fav]
    }), 200
 
 
@app.route("/favorite/planet/<int:planet_id>", methods=["POST"])
def add_favorite_planet(planet_id):
    user_id = get_current_user_id()
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "usuario no existe"}), 404
    location = db.session.get(Location, planet_id)
    if location is None:
        return jsonify({"error": "planeta no existe"}), 404
    existe = db.session.execute(select(Favorite_location).where(
        Favorite_location.user_id == user_id,
        Favorite_location.location_id == planet_id)).scalar_one_or_none()
    if existe:
        return jsonify({"error": "este planeta ya esta en tus favoritos"}), 400
    new_favorite_planet = Favorite_location(
        user_id=user_id, location_id=planet_id)
    db.session.add(new_favorite_planet)
    db.session.commit()
    return jsonify(new_favorite_planet.serialize()), 201
 
 
@app.route("/favorite/people/<int:people_id>", methods=["POST"])
def add_favorite_people(people_id):
    user_id = get_current_user_id()
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "usuario no existe"}), 404
    character = db.session.get(Character, people_id)
    if character is None:
        return jsonify({"error": "personaje no existe"}), 404
    existe = db.session.execute(select(Favorite_character).where(
        Favorite_character.user_id == user_id,
        Favorite_character.character_id == people_id)).scalar_one_or_none()
    if existe:
        return jsonify({"error": "este personaje ya esta en tus favoritos"}), 400
    new_favorite_character = Favorite_character(
        user_id=user_id, character_id=people_id)
    db.session.add(new_favorite_character)
    db.session.commit()
    return jsonify(new_favorite_character.serialize()), 201
 
 
@app.route("/favorite/planet/<int:planet_id>", methods=["DELETE"])
def delete_favorite_planet(planet_id):
    user_id = get_current_user_id()
    favorite_planet = db.session.execute(select(Favorite_location).where(
        Favorite_location.user_id == user_id,
        Favorite_location.location_id == planet_id)).scalar_one_or_none()
    if favorite_planet is None:
        return jsonify({"error": "no tienes ese planeta como favorito"}), 404
    db.session.delete(favorite_planet)
    db.session.commit()
    return jsonify({"msg": "favorito eliminado con exito"}), 200
 
 
@app.route("/favorite/people/<int:people_id>", methods=["DELETE"])
def delete_favorite_people(people_id):
    user_id = get_current_user_id()
    favorite_people = db.session.execute(select(Favorite_character).where(
        Favorite_character.user_id == user_id,
        Favorite_character.character_id == people_id)).scalar_one_or_none()
    if favorite_people is None:
        return jsonify({"error": "no tienes ese personaje como favorito"}), 404
    db.session.delete(favorite_people)
    db.session.commit()
    return jsonify({"msg": "favorito eliminado con exito"}), 200
 

 
# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)