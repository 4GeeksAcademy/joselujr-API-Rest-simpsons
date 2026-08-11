from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, ForeignKey,select
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()

class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), default=True,nullable=False)
    favorite_characters:Mapped[list["Favorite_character"]] = relationship("Favorite_character",back_populates="user_favorite")
    user_fav_location_by: Mapped[list["Favorite_location"]] = relationship("Favorite_location", back_populates="user_fav_location")


    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            # do not serialize the password, its a security breach
        }



class Character(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    quote: Mapped[str] = mapped_column(String(120), nullable=True)
    favorited_by:Mapped[list["Favorite_character"]] = relationship("Favorite_character",back_populates="charactr_favorite")
#linea 28, el favorite_character esta dentro de comillas para que no me de error.

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "quote": self.quote
        }


    
class Location(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), unique=True, nullable=False)
    use: Mapped[str] = mapped_column(String(180), unique=False, nullable=False)
    location_favorite_by: Mapped[list["Favorite_location"]] = relationship("Favorite_location", back_populates="location_favorite")


    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "use": self.use
            }



class Favorite_character(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_favorite: Mapped[User] = relationship(User, back_populates="favorite_characters")
    charactr_favorite: Mapped[Character] = relationship(Character, back_populates="favorited_by")
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id),nullable=False)
    character_id: Mapped[int] = mapped_column(ForeignKey(Character.id),nullable=False)


    def serialize(self):
        return {
            "id": self.id,
            "character": self.charactr_favorite.serialize()
            }
    


class Favorite_location(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_fav_location: Mapped[User] = relationship(User, back_populates="user_fav_location_by")
    location_favorite: Mapped[Location] = relationship(Location, back_populates="location_favorite_by")
    user_id: Mapped[int] = mapped_column(ForeignKey(User.id),nullable=False)
    location_id: Mapped[int] = mapped_column(ForeignKey(Location.id),nullable=False)


    def serialize(self):
        return {
            "id": self.id,
            "location": self.location_favorite.serialize()
            }