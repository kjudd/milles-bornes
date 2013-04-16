from flask import Flask, render_template, redirect, request, session
import model
import random

app = Flask(__name__)

#function to display the action of a card in your hand
def cards_in_hand(player_hand):
	cards_in_hand = []
	for card in player_hand:
		int_card = int(card)
		card_info = model.session.query(model.Card).get(int_card)
		cards_in_hand.append(card_info)
	# named_cards = []
	# for card in cards_in_hand:
	# 	action = card.action
	# 	named_cards.append(action)
	return cards_in_hand

#function to convert a list of cards into a string(if it's not a list of integers)
def cardstring(cardlist):
	string_cardlist = ','.join(cardlist)
	draw_deck = str(string_cardlist)

#login or sign up
@app.route("/")
def login():
	return render_template("login.html")

#choose game on logging in
@app.route("/authenticate", methods = ["POST"])
def authenticate():
	player_id = request.form['id']
	player_password = request.form['password']
	session['player'] = player_id
	return redirect("/choose_game")

#choose game on signing up
@app.route("/signup", methods = ["POST"])
def signup():
	name = request.form['name']
	email = request.form['email']
	password = request.form['password']
	player = model.Player(id = None, name = name, email = email, password = password)
	model.session.add(player)
	model.session.commit()
	session['player'] = player.id
	return redirect("/choose_game")

#choose to join game, new game, or resume game
@app.route("/choose_game", methods = ["GET"])
def choose_game():
	player = session.get("player")
	player_info = model.session.query(model.Usergame).filter_by(user_id = player).all()
	game_ids = []
	for i in player_info:
		games = i.game_id
		game_ids.append(games)
	return render_template("new_game.html", gameplay = game_ids)

#create a new game, shuffles cards and deals you in
@app.route("/create_game", methods = ["POST"])
def create_game():
	player = session.get("player")
	deck = range(1, 101)
	random.shuffle(deck)
	dealt_cards = deck[94: ]
	deck[94: ] = []
	string_deck = str(deck)
	draw_deck = string_deck.strip('[]')
	game = model.Game(id = None, draw_pile = draw_deck)
	model.session.add(game)
	model.session.commit()
	string_hand = str(dealt_cards)
	player_hand = string_hand.strip('[]')
	usergame = model.Usergame(id = None, game_id = game.id, user_id = player, position = 1, hand = player_hand, player_status = "None", player_immunity = "None", miles = 0)
	model.session.add(usergame)
	model.session.commit()
	return "Awaiting players"

#displays list of games to join that have a certain number of cards in draw pile
#currently 2 player
@app.route("/join_game", methods = ["POST"])
def join_game():
	all_usergames = model.session.query(model.Usergame).all()
	open_games = []
	for game in all_usergames:
		draw = game.game.draw_pile.split(',')
		if len(draw) == 94 and game.user_id != session.get("player"):
			open_games.append(game.game)
		else:
			continue
	return render_template("open_games.html", games = open_games)

#joins game, deals you in and adds your usergame
@app.route("/open_game/<int:id>", methods = ["POST", "GET"])
def join_new_game(id):
	session["game"] = id
	player = session.get("player")
	game = model.session.query(model.Game).get(id)
	string_cards = eval(game.draw_pile)	
	deal_cards = list(string_cards)
	dealt_cards = deal_cards[-6: ]
	deal_cards[-6: ] = []
	string_hand = str(dealt_cards)
	player_hand = string_hand.strip('[]')
	usergame = model.Usergame(id = None, game_id = game.id, user_id = player, position = 2, hand = player_hand, player_status = "None", player_immunity = "None", miles = 0)
	model.session.add(usergame)
	string_draw = str(deal_cards)
	draw_deck = string_draw.strip('[]')
	game.draw_pile = draw_deck
	model.session.commit()
	return redirect("/gameplay")

@app.route("/resume_game/<int:id>", methods = ["POST", "GET"])
def resume_game(id):
	session["game"] = id
	return redirect("/gameplay")

@app.route("/gameplay", methods = ["POST", "GET"])
def gameplay():
	player = session.get("player")
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter_by(user_id = player, game_id = game).all()
	usergame = usergame[0]
	draw_pile = usergame.game.draw_pile
	dealt_cards = usergame.hand
	dealt_tuple = str(dealt_cards)
	dealt_list = dealt_tuple.split(',')
	names = cards_in_hand(dealt_list)
	print names
	status = usergame.player_status
	immunity = usergame.player_immunity
	miles = usergame.miles
	return render_template("gameplay.html", names = names, status = status, immunity = immunity, miles = miles)

@app.route("/draw", methods = ["POST"])
def draw():
	player = session.get("player")
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter_by(user_id = player, game_id = game).all()
	usergame = usergame[0]
	game_object = model.session.query(model.Game).get(game)
	draw_pile = game_object.draw_pile
	evaluation = eval(draw_pile)
	deal_cards = list(evaluation)
	dealt_cards = deal_cards[-1]
	deal_cards[-1: ] = []
	string_draw = str(deal_cards)
	draw_deck = string_draw.strip('[]')
	game_object.draw_pile = draw_deck
	hand = usergame.hand
	hand = eval(hand)
	hand = list(hand)
	hand.append(dealt_cards)
	new_hand = str(hand)
	commit_hand = new_hand.strip('[]')
	usergame.hand = commit_hand
	model.session.commit()
	return redirect("/gameplay")

# @app.route("/play_card<int:id>", methods = ["POST", "GET"])
# #IF TREE
# CARD DOWN
# IF your status is roll, you can add miles 
# or put hazards on the other player unless that player has immunities
# or discard
# or put down an immunity card (+1 turn)
# ELIF your status is none you can put down a roll 
# or put hazards on another player unless that player had immunities
# or put down an immunity card
# or discard
# ELIF your status is a hazard type card
# you can put down a hazard card on another player unless that player has immunities
# or discard
# or put down an immunity card
# or put down the matching remedy card


 
# def play_card(id):
# 	player_id = session.get("player")
# 	game = session.get("game")
# 	usergame = model.session.query(model.Usergame).filter_by(user_id = player, game_id = game).all()
# 	usergame_hand = usergame[0].hand
# 	string_hand = str(usergame_hand)
# 	split_hand = string_hand.split(',')
# 	card = model.session.query(model.Card).get(id)
# 	if len(split_hand) < 7:
# 		return "You can't play until you draw"
# 	if usergame.player_status != "roll":
# 		if card.type == "hazard":
# 			other_player = model.session.query(model.Usergame).filter_by(game_id = game, position != usergame.position).all()
# 			#DO THEY HAVE IMMUNITIES?
# 		elif card.type == 	
# 	elif usergame.player_status == "roll"
# 		if card.type == "miles":
# 			integer = int(card.action)
# 			usergame.miles += integer
# 			model.session.commit() 
# 			return redirect("/gameplay")

# # 	elif card.type == "hazard":


# # 	elif card.type == "remedy":

# # 	elif card.type == "safety":











app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
	app.run(debug = True)

