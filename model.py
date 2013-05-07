import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, backref

database_url = os.environ.get('DATABASE_URL', 'postgres://localhost/milles-bornes.db')
ENGINE = create_engine(database_url, echo=False)
session = scoped_session(sessionmaker(bind=ENGINE, autocommit=False, autoflush=False))

Base = declarative_base()
Base.query = session.query_property()


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String(140), nullable=True)
    email = Column(String(140), nullable=True)
    password = Column(String(140), nullable=True)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.name)


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True)
    type = Column(String(64), nullable=True)
    action = Column(String(64), nullable=True)
    image = Column(String(500), nullable=True)


class Usergame(Base):
    __tablename__ = "user_game"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer(1000), ForeignKey('games.id'))
    user_id = Column(Integer(1000), ForeignKey('players.id'))
    position = Column(Integer(1))
    hand = Column(String(30), nullable=True)
    miles = Column(Integer(4), nullable=True)
    immunities = Column(Integer(4), nullable=True)
    #Vulnerabilities
    can_be_stopped = Column(Integer(1), nullable=True)
    can_have_flat = Column(Integer(1), nullable=True)
    can_have_low_gas = Column(Integer(1), nullable=True)
    can_have_speed_limit = Column(Integer(1), nullable=True)
    can_be_in_accident = Column(Integer(1), nullable=True)
    #Status
    speed_limit = Column(Integer(1), nullable=True)
    can_go = Column(Integer(1), nullable=True)
    has_flat = Column(Integer(1), nullable=True)
    has_accident = Column(Integer(1), nullable=True)
    gas_empty = Column(Integer(1), nullable=True)
    game_status = Column(Integer(1), nullable=True)

    #Method displays the action of a card in player hand.
    def cards_in_hand(self, player_hand):
        cards_in_hand = []
        for card in player_hand:
            int_card = int(card)
            card_info = session.query(Card).get(int_card)
            cards_in_hand.append(card_info)
        return cards_in_hand

    def check_status(self):
        if self.can_go == 1:
            status = "Going"
        elif self.has_flat == 1:
            status = "Flat Tire"
        elif self.has_accident == 1:
            status = "Accident"
        elif self.gas_empty == 1:
            status = "Gas Empty"
        else:
            status = "Stopped"
        return status

    def check_speed(self):
        if self.speed_limit == 0:
            limit = "None"
        else:
            limit = self.speed_limit
        return limit

    def check_immunities(self):
        current_immunities = []
        string = str(self.immunities)

        if string[0] == "3":
            current_immunities.append("Extra Tank")
        if string[1] == "3":
            current_immunities.append("Puncture Proof")
        if string[2] == "3":
            current_immunities.append("Driving Ace")
        if string[3] == "3":
            current_immunities.append("Right of Way")

        return current_immunities

    def check_hazards(self, card, other_player):
        if card.action == "out of gas":
            if other_player.can_have_low_gas == 1 and str(other_player.immunities)[0] != "3":
                return card
            else:
                return None
        elif card.action == "flat tire":
            if other_player.can_have_flat == 1 and str(other_player.immunities)[1] != "3":
                return card
            else:
                return None
        elif card.action == "accident":
            if other_player.can_be_in_accident == 1 and str(other_player.immunities)[2] != "3":
                return card
            else:
                return None
        elif card.action == "speed limit":
            if other_player.can_have_speed_limit == 1 and str(other_player.immunities)[3] != "3":
                return card
            else:
                return None
        elif card.action == "stop":
            if other_player.can_be_stopped == 1 and str(other_player.immunities)[3] != "3":
                return card
            else:
                return None

    def check_miles(self, card):
        if self.can_go == 1:
            if int(card.action) == 200:
                if self.miles <= 800 and self.speed_limit < 50:
                    return card
                else:
                    return None
            elif int(card.action) == 100:
                if self.miles <= 900 and self.speed_limit < 50:
                    return card
                else:
                    return None
            elif int(card.action) == 75:
                if self.miles <= 925 and self.speed_limit < 50:
                    return card
                else:
                    return None
            elif int(card.action) == 50:
                if self.miles <= 950:
                    return card
                else:
                    return None
            elif int(card.action) == 25:
                if self.miles <= 975:
                    return card
                else:
                    return None
        else:
            return None

    def check_remedy(self, card):
        if card.action == "gasoline":
            if self.gas_empty == 1:
                return card
            else:
                return None
        elif card.action == "spare tire":
            if self.has_flat == 1:
                return card
            else:
                return None
        elif card.action == "repairs":
            if self.has_accident == 1:
                return card
            else:
                return None
        elif card.action == "end of limit":
            if self.speed_limit == 50:
                return card
        elif card.action == "roll":
            if self.can_go == 0:
                if self.gas_empty == 0 and self.has_flat == 0 and self.has_accident == 0:
                    return card
            else:
                return None

    def update_turns(self, other_player):
        self.position = 2
        other_player.position = 1

    def stop_everything(self, other_player):
        other_player.can_be_stopped = 0
        other_player.can_have_flat = 0
        other_player.can_have_low_gas = 0
        other_player.can_have_speed_limit = 0
        other_player.can_be_in_accident = 0
        other_player.can_go = 0

    def start_everything(self):
        self.can_be_stopped = 1
        self.can_have_flat = 1
        self.can_have_low_gas = 1
        self.can_have_speed_limit = 1
        self.can_be_in_accident = 1
        self.can_go = 1

    game = relationship("Game", backref=backref("games", order_by=id))
    player = relationship("Player", backref=backref("players", order_by=id))


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    draw_pile = Column(String(500), nullable=True)
