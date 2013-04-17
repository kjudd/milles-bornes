from flask import Flask, render_template, redirect, request, session
import model
import random
from sqlalchemy import and_

app = Flask(__name__)

#function to display the action of a card in your hand
def cards_in_hand(player_hand):
	cards_in_hand = []
	for card in player_hand:
		int_card = int(card)
		card_info = model.session.query(model.Card).get(int_card)
		cards_in_hand.append(card_info)
	return cards_in_hand

#function to convert a list of cards into a string(if it's not a list of integers)
def cardstring(cardlist):
	string_cardlist = ','.join(cardlist)
	draw_deck = str(string_cardlist)

#login or sign up
@app.route("/")
def login():
	return render_template("login.html")

#choose game when logging in
#commits player to session
@app.route("/authenticate", methods = ["POST"])
def authenticate():
	player_id = request.form['id']
	player_password = request.form['password']
	session['player'] = player_id
	return redirect("/choose_game")

#sign up to create new player
#commit player to session
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
	usergame = model.Usergame(id = None, game_id = game.id, user_id = player, 
		position = 1, hand = player_hand, miles = 0, immunities = 2222,
		can_be_stopped = 0, can_have_flat = 0, can_have_low_gas = 0, 
		can_have_speed_limit = 0, can_be_in_accident = 0, speed_limit = 0, 
		can_go = 0, has_flat = 0, has_accident = 0, gas_empty = 0)
	model.session.add(usergame)
	model.session.commit()
	return "Awaiting players"

#displays list of joinable that have a certain number of cards in draw pile
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
	usergame = model.Usergame(id = None, game_id = game.id, user_id = player, 
		position = 2, hand = player_hand, miles = 0, immunities = 2222,
		can_be_stopped = 0, can_have_flat = 0, can_have_low_gas = 0, 
		can_have_speed_limit = 0, can_be_in_accident = 0, speed_limit = 0, 
		can_go = 0, has_flat = 0, has_accident = 0, gas_empty = 0)
	model.session.add(usergame)
	string_draw = str(deal_cards)
	draw_deck = string_draw.strip('[]')
	game.draw_pile = draw_deck
	model.session.commit()
	return redirect("/turn")

#resume a game in progress from your list
@app.route("/resume_game/<int:id>", methods = ["POST", "GET"])
def resume_game(id):
	session["game"] = id
	return redirect("/turn")

# tracks whose turn it is by Usergame position
@app.route("/turn", methods = ["POST", "GET"])
def turn():
	player = session.get("player")
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter(and_(model.Usergame.user_id == player, model.Usergame.game_id == game)).all()
	usergame = usergame[0]
	if usergame.position != 1:
		return "Not your turn."
	elif usergame.position == 1:
		return redirect("/gameplay")

#displays player options from hand
#evaluates options for all valid moves based on both player statuses
@app.route("/gameplay", methods = ["POST", "GET"])
def gameplay():
	player = session.get("player")
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter(and_(model.Usergame.user_id == player, model.Usergame.game_id == game)).all()
	usergame = usergame[0]
	other_players = model.session.query(model.Usergame).filter(and_(model.Usergame.game_id == game, model.Usergame.position != usergame.position)).all()
	draw_pile = usergame.game.draw_pile
	dealt_cards = usergame.hand
	dealt_tuple = str(dealt_cards)
	dealt_list = dealt_tuple.split(',')
	names = cards_in_hand(dealt_list)
	valid_moves = []

	def check_hazards(card, other_player):
		if card.action == "out of gas":
			if other_player.can_have_low_gas == 1 and str(other_player.immunities)[0] != "1":
				return card
			else: return 0
		elif card.action == "flat tire":
			if other_player.can_have_flat == 1 and str(other_player.immunities)[1] != "1":
				return card
			else: return 0
		elif card.action == "accident":
			if other_player.can_be_in_accident == 1 and str(other_player.immunities)[2] != "1":
				return card
			else: return 0
		elif card.action == "speed_limit":
			if other_player.can_have_speed_limit == 1 and str(other_player.immunities)[3] != "1":
				return card
			else: return 0
		elif card.action == "stop":
			if other_player.can_be_stopped == 1 and str(other_player.immunities)[3] != "1":
				return card
			else: return 0

	def check_miles(card):
		if usergame.can_go == 1:
			if int(card.action) == 200:
				if usergame.miles <= 800 and usergame.speed_limit < 50:
					return card
				else: return 0
			elif int(card.action) == 100:
				if usergame.miles <= 900 and usergame.speed_limit < 50:
					return card
				else: return 0
			elif int(card.action) == 75:
				if usergame.miles <= 925 and usergame.speed_limit < 50:
					return card
				else: return 0
			elif int(card.action) == 50:
				if usergame.miles <= 950:
					return card
				else: return 0
			elif int(card.action) == 25:
				if usergame.miles <= 975:
					return card
				else: return 0
		else:
			return 0

	def check_remedy(card):
		if card.action == "gasoline":
			if usergame.gas_empty == 1:
				return card
			else: return 0
		elif card.action == "spare tire":
			if usergame.has_flat == 1:
				return card
			else: return 0
		elif card.action == "repairs":
			if usergame.has_accident == 1:
				return card
			else: return 0
		elif card.action == "end of limit":
			if usergame.speed_limit == 1:
				return card
		elif card.action == "roll":
			if usergame.can_go == 0:
				if usergame.gas_empty == 0 and usergame.has_flat == 0 and usergame.has_accident == 0:
					return card
			else: return 0

	for card in names:
		if card.type == "hazard":
			for player in other_players:
				add_card = check_hazards(card, player)
				if add_card != 0:
					valid_moves.append(add_card)
		 			break
		elif card.type == "miles":
			add_card = check_miles(card)
			if add_card != 0:
				valid_moves.append(add_card)
		elif card.type == "remedy":
			add_card = check_remedy(card)
			if add_card != 0:
				valid_moves.append(add_card)
		elif card.type == "safety":
			valid_moves.append(card)
		
		miles = usergame.miles
		going = usergame.can_go

	return render_template("gameplay.html", names = names, valid_moves = valid_moves, miles = miles, going = going)

#draw card if less than 7 cards
@app.route("/draw", methods = ["POST"])
def draw():
	player = session.get("player")
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter_by(user_id = player, game_id = game).all()
	usergame = usergame[0]
	game_object = model.session.query(model.Game).get(game)
	draw_pile = game_object.draw_pile
	string_draw = str(draw_pile)
	deal_cards = string_draw.split(',')
	dealt_cards = deal_cards[-1]
	deal_cards[-1: ] = []
	string_draw = ','.join(deal_cards)
	game_object.draw_pile = string_draw
	hand = usergame.hand
	hand = str(hand)
	hand = hand.split(',')
	hand.append(dealt_cards)
	new_hand = ','.join(hand)
	usergame.hand = new_hand
	model.session.commit()
	return redirect("/gameplay")

#discard if not valid moves
@app.route("/discard/<int:id>", methods = ["POST", "GET"])
def discard(id):
	player_id = session.get("player")
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter_by(user_id = player_id, game_id = game).all()
	usergame = usergame[0]
	other_players = model.session.query(model.Usergame).filter(and_(model.Usergame.game_id == game, model.Usergame.position != usergame.position)).all()
	other_player = other_players[0]
	discarded = model.session.query(model.Card).get(id)
	hand = usergame.hand
	hand = str(hand)
	hand = hand.split(',')
	print hand
	for card in hand:
		print card
		if int(card) == id:
			hand.remove(card)
	print hand
	new_hand = ','.join(hand)
	print new_hand
	usergame.hand = new_hand
	usergame.position = 2
	other_player.position = 1
	model.session.commit()
	return redirect("/turn")

#evaluates players selected card and updates db with new move
#changes position for next player turn
@app.route("/play_card/<int:id>", methods = ["POST", "GET"])
def play_card(id):
	player_id = session.get("player")
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter_by(user_id = player_id, game_id = game).all()
	usergame = usergame[0]
	other_players = model.session.query(model.Usergame).filter(and_(model.Usergame.game_id == game, model.Usergame.position != usergame.position)).all()
	other_player = other_players[0]
	usergame_hand = usergame.hand
	string_hand = str(usergame_hand)
	split_hand = string_hand.split(',')
	card = model.session.query(model.Card).get(id)
#HAZARD, MILES, REMEDY SAFETY
#WHAT CAN HAPPEN
	def update_turns():
		usergame.position = 2
		other_player.position = 1
	def stop_everything():
		other_player.can_be_stopped = 0
		other_player.can_have_flat = 0
 		other_player.can_have_low_gas = 0
 		other_player.can_have_speed_limit = 0
 		other_player.can_be_in_accident = 0
 		other_player.can_go = 0
 	def start_everything():
 		usergame.can_be_stopped = 1
		usergame.can_have_flat = 1
		usergame.can_have_low_gas = 1
		usergame.can_have_speed_limit = 1
		usergame.can_be_in_accident = 1
		usergame.can_go = 1

	if card.type == "miles":
		integer = int(card.action)
		usergame.miles += integer
		model.session.commit() 
		if usergame.miles == 1000:
			return redirect("/winner")
		else:
			update_turns()
			model.session.commit()
			return redirect("/turn")
	elif card.type == "safety":
		if card.action == "extra tank":
			usergame.immunities += 1000
		if card.action == "puncture proof":
			usergame.immunities += 100
		if card.action == "driving ace":
			usergame.immunities += 10
		if card.action == "right of way":
			usergame.immunities += 1
		#extra turn, no update
		model.session.commit()
		return redirect("/turn")
 	elif card.type == "hazard":
 		if card.action == "out of gas":
 			stop_everything()
 			other_player.gas_empty = 1
 			update_turns()
 			model.session.commit()
 			return redirect("/turn")
 		if card.action == "flat tire":
 			stop_everything()
 			other_player.has_flat = 1
 			update_turns()
 			model.session.commit()
 			return redirect("/turn")
 		if card.action == "accident":
 			stop_everything()
 			other_player.has_accident = 1
 			update_turns()
 			model.session.commit()
 			return redirect("/turn")
 		if card.action == "stop":
 			stop_everything()
 			update_turns()
 			model.session.commit()
 			return redirect("/turn") 		
 		if card.action == "speed limit":
 			other_player.speed_limit = 50
 			update_turns()
 			model.session.commit()
 			return redirect("/turn")
	elif card.type == "remedy":
		if card.action == "roll":
			start_everything()
			update_turns()
			model.session.commit()
			return redirect("/turn")
		if card.action == "gasoline":
			start_everything()
			usergame.gas_empty = 0
			update_turns()
			model.session.commit()
			return redirect("/turn")
		if card.action == "spare tire":
			start_everything()
			usergame.has_flat = 0
			update_turns()
			model.session.commit()
			return redirect("/turn")
		if card.action == "repairs":
			start_everything()
			usergame.has_accident = 0
			update_turns()
			model.session.commit()
			return redirect("/turn")
		if card.action == "end of limit":
			speed_limit = 0
			update_turns()
			model.session.commit()
			return redirect("/turn")

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
	app.run(debug = True)

