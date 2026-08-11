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
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False


db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200




@app.route("/user", methods=["POST"])
def create_user():
    data = request.get_json()
    if not data.get("email") or not data.get("password"):
        return jsonify ({"error": "Email y password son requeridos"}), 400
    existe_user = db.session.execute(select(User).where(
        User.email == data.get("email"))).scalar_one_or_none()
    if existe_user:
        return jsonify({"error":"Ya existe un usuario con este email"}), 400

    new_user = User(email=data.get("email"), password=data.get("password"))
    db.session.add(new_user)
    db.session.commit()
    return jsonify(new_user.serialize()), 201


@app.route("/character", methods=["POST"])
def create_character():
    data = request.get_json()
    if not data.get("name"):
        return jsonify({"error": "El nombre es obligatorio"}), 400
    new_character = Character(name=data.get("name"), quote=data.get("quote", ""))
    db.session.add(new_character)
    db.session.commit()
    return jsonify(new_character.serialize()), 201


@app.route("/people", methods=["GET"])
def get_people():
    characters = db.session.execute(select(Character)).scalars().all()
    return jsonify([character.serialize() for character in characters]), 200


@app.route("/people/<int:people_id>", methods=["GET"])
def get_people_id(people_id):
    person_id = db.session.get(Character, people_id)
    if person_id is None:
        return jsonify ({"error": "personaje no existe"}), 404
    return jsonify (person_id.serialize()), 200



@app.route("/planets", methods=["GET"])
def get_planets():
    locations = db.session.execute(select(Location)).scalars().all()
    return jsonify([location.serialize() for location in locations]), 200

@app.route("/planets/<int:planets_id>", methods=["GET"])
def get_planet_id(planets_id):
    location_id = db.session.get(Location, planets_id)
    if location_id is None:
        return jsonify ({"error": "esta locacion no existe"}), 404
    return jsonify (location_id.serialize()), 200


@app.route("/users", methods=["GET"])
def get_user_all():
    users = db.session.execute(select(User)).scalars().all()
    return jsonify([user.serialize() for user in users]), 200


@app.route("/users/favorites/<int:user_id>", methods=["GET"])
def user_favorites(user_id):
    location_fav = db.session.execute(select(Favorite_location).where(Favorite_location.user_id == user_id)).scalars().all()
    character_fav = db.session.execute(select(Favorite_character).where(Favorite_character.user_id == user_id)).scalars().all()
    return jsonify ({
            "favorite_location": [location.serialize() for location in location_fav],
            "favorite_character": [character.serialize() for character in character_fav]
            }), 200

        
@app.route("/favorite/planet/<int:planet_id>", methods=["POST"])
def add_favorite_planet(planet_id):
    data = request.get_json()
    if not data.get("user_id"):
        return jsonify({"error": "es obligatorio el user_id"}), 400
    location = db.session.get(Location, planet_id)
    if location is None:
        return jsonify({"error": "planeta no existe"}), 404
    new_favorite_planet = Favorite_location(user_id= data.get("user_id"), location_id=planet_id)
    db.session.add(new_favorite_planet)
    db.session.commit()
    return jsonify(new_favorite_planet.serialize()), 201
   

@app.route("/favorite/people/<int:people_id>", methods=["POST"])
def add_favorite_people(people_id):
    data = request.get_json()
    if not data.get("user_id"):
        return jsonify({"error": "es obligatorio el user_id"}), 400
    character = db.session.get(Character, people_id)
    if character is None:
        return jsonify({"error": "personaje no existe"}), 404
    new_favorite_character = Favorite_character(user_id= data.get("user_id"), character_id=people_id)
    db.session.add(new_favorite_character)
    db.session.commit()
    return jsonify(new_favorite_character.serialize()), 201

    



# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
