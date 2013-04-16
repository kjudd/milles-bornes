from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

ENGINE = create_engine("postgresql://localhost/milles-bornes.db", echo = False)
session = scoped_session(sessionmaker(bind=ENGINE, autocommit = False, autoflush = False))


Base = declarative_base()
Base.query = session.query_property()

## Class declarations go here

class Player(Base):
	__tablename__ = "players"

	id = Column(Integer, primary_key = True)
	name = Column(String(140), nullable = True)
	email = Column(String(140), nullable = True)
	password = Column(String(140), nullable = True)

class Card(Base):
	__tablename__ = "cards"

	id = Column(Integer, primary_key = True)
	type = Column(String(64), nullable = True)
	action = Column(String(64), nullable = True)
	image = Column(String(300), nullable = True)

class Usergame(Base):

	__tablename__ = "user_game"

	id = Column(Integer, primary_key = True)
	game_id = Column(Integer(1000), ForeignKey('games.id'))
	user_id = Column(Integer(1000), ForeignKey('players.id'))
	position = Column(Integer(1))
	hand = Column(String(30), nullable = True)
	player_status = Column(String(140), nullable = True)
	player_immunity = Column(String(4), nullable = True)
	miles = Column(Integer(4), nullable = True)


	game = relationship("Game", backref = backref("games", order_by=id))
	player = relationship("Player", backref = backref("players", order_by=id))


class Game(Base):
	__tablename__ = "games"
	id = Column(Integer, primary_key = True)
	draw_pile = Column(String(500), nullable = True)


### End class declarations


def main():
    """In case we need this for something"""
    pass

if __name__ == "__main__":
    main()