import model
import csv
import os

def load_cards(session):
    with open('seed_data/u.cards', 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter = "|")
        for row in reader:
            type = row[0]
            action = row[1]
            new_card = model.Card(id = None, type = type, action = action, image = None)
            session.add(new_card)
        session.commit()

def load_players(session):
    session.add()
    session.commit()

def load_usergame(session):
    usergame = model.Usergame(id = None, game_id = 1, user_id = 1, position = 1, hand = None)
    session.add(usergame)

def load_games(session):
    game = model.Game(id = None, draw_pile = "0")
    session.add(game)
    session.commit()

def main(session):
    # load_players(session)
    load_cards(session)
    # load_usergame(session)
    # load_games(session)
    # You'll call each of the load_* functions with the session as an argument

if __name__ == "__main__":
    s= model.session
    main(s)