from flask import Flask, render_template, redirect, request, session, flash
import model
import random
from sqlalchemy import and_
import forms
import os
from flask_login import LoginManager
from flask_login import login_user, logout_user, current_user, login_required
import bcrypt
import pusher
import config_pusher

app = Flask(__name__)

#Set up config for WTForms CSRF.
app.config.from_object('config')

#Set up login manager for Flask-Login.
lm = LoginManager()
lm.setup_app(app)

p = pusher.Pusher(app_id=app.config['PUSHER_APP_ID'], key=app.config['PUSHER_APP_KEY'], secret=app.config['PUSHER_APP_SECRET'])

#Login manager setup for Flask-Login.
@lm.user_loader
def load_user(id):
	return model.session.query(model.Player).get(int(id))

#View to login or sign up.
@app.route("/", methods = ["POST", "GET"])
def login():
	#If user is already in session, redirect to choose game.
	if current_user is not None and current_user.is_authenticated():
		return redirect("/choose_game")

	#Sign up view to add player id, name, email, and hashed password to database.
	form = forms.RegistrationForm()
	if form.validate_on_submit():
		email_query = model.session.query(model.Player).filter_by(email = form.email.data).all()
		hashed = bcrypt.hashpw(form.password.data, bcrypt.gensalt(10))
		if not email_query:
			player = model.Player(id = None, name = form.name.data, email = form.email.data,
				password = hashed)
			model.session.add(player)
			model.session.commit()
			login_user(player)
			return redirect("/choose_game")
		else:
			print email_query
			flash('Account exists. Please log in.')
			return redirect('/')

	#Login view to allow user to log in, compares given password to salted password.
	login_form = forms.LoginForm()
	if login_form.validate_on_submit():
		player = model.session.query(model.Player).filter_by(email = login_form.email.data).first()
		if player is None:
			flash('Invalid login. Please try again.')
			return redirect('/')
		elif bcrypt.hashpw(login_form.password.data, player.password) == player.password:
				login_user(player)
				return redirect("/choose_game")
		else:
			flash('Invalid password. Please try again.')
			return redirect('/')
	else: return render_template("login.html", form = form)

#View to choose join game, new game, or resume game.
@app.route("/choose_game", methods = ["GET"])
@login_required
def choose_game():
	player = current_user.id
	player_games = model.session.query(model.Usergame).filter_by(user_id = player).all()
	awaiting_player = []
	game_won = []
	game_lost = []
	game_tied = []
	current_game = []
	for game in player_games:
		str_game = str(game.game.draw_pile)
		split_game = str_game.split(',')
		game_id = game.game_id
		if len(split_game) == 100:
			awaiting_player.append(game_id)
		elif len(split_game) <= 94:
			if game.game_status == 0:
				current_game.append(game_id)
			elif game.game_status == 1:
				game_won.append(game_id)
			elif game.game_status == 2:
				game_tied.append(game_id)
			else:
				game_lost.append(game_id)
	return render_template("new_game.html", awaiting_player = awaiting_player, game_won = game_won,
		game_lost = game_lost, game_tied = game_tied, current_game = current_game)

#View to create a new game, shuffles cards and deals player in at position 2.
@app.route("/create_game", methods = ["POST"])
@login_required
def create_game():
	player = current_user.id
	deck = range(1, 107)
	random.shuffle(deck)
	dealt_cards = deck[100: ]
	deck[100: ] = []
	string_deck = str(deck)
	draw_deck = string_deck.strip('[]')
	game = model.Game(id = None, draw_pile = draw_deck)
	model.session.add(game)
	model.session.commit()
	string_hand = str(dealt_cards)
	player_hand = string_hand.strip('[]')
	usergame = model.Usergame(id = None, game_id = game.id, user_id = player,
		position = 2, hand = player_hand, miles = 0, immunities = 2222,
		can_be_stopped = 0, can_have_flat = 0, can_have_low_gas = 0,
		can_have_speed_limit = 0, can_be_in_accident = 0, speed_limit = 0,
		can_go = 0, has_flat = 0, has_accident = 0, gas_empty = 0, game_status = 0)
	model.session.add(usergame)
	model.session.commit()
	return render_template("await_players.html")

#View to display list of joinable games
#Joinable games have a certain number of cards in draw pile, currently 2 player
@app.route("/join_game", methods = ["POST"])
@login_required
def join_game():
	all_usergames = model.session.query(model.Usergame).all()
	open_games = []
	for game in all_usergames:
		draw = game.game.draw_pile.split(',')
		if len(draw) == 100 and game.user_id != current_user.id:
			open_games.append(game.game)
		else:
			continue
	return render_template("open_games.html", games = open_games)

#View for player to join game, deals player in and adds player usergame.
@app.route("/open_game/<int:id>", methods = ["POST", "GET"])
@login_required
def join_new_game(id):
	session["game"] = id
	player = current_user.id
	game = model.session.query(model.Game).get(id)
	string_cards = eval(game.draw_pile)
	deal_cards = list(string_cards)
	dealt_cards = deal_cards[-6: ]
	deal_cards[-6: ] = []
	string_hand = str(dealt_cards)
	player_hand = string_hand.strip('[]')
	usergame = model.Usergame(id = None, game_id = game.id, user_id = player,
		position = 1, hand = player_hand, miles = 0, immunities = 2222,
		can_be_stopped = 0, can_have_flat = 0, can_have_low_gas = 0,
		can_have_speed_limit = 0, can_be_in_accident = 0, speed_limit = 0,
		can_go = 0, has_flat = 0, has_accident = 0, gas_empty = 0, game_status = 0)
	model.session.add(usergame)
	string_draw = str(deal_cards)
	draw_deck = string_draw.strip('[]')
	game.draw_pile = draw_deck
	model.session.commit()
	return redirect("/gameplay")

#View to resume a game in progress from list.
@app.route("/resume_game/<int:id>", methods = ["POST", "GET"])
@login_required
def resume_game(id):
	session["game"] = id
	return redirect("/turn")

#View to tracks whose turn it is by Usergame position.
@app.route("/turn", methods = ["POST", "GET"])
@login_required
def turn():
	player = current_user.id
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter(and_(model.Usergame.user_id == player, model.Usergame.game_id == game)).all()
	usergame = usergame[0]
	if usergame.position != 1:
		return redirect("/await_turn")
	elif usergame.position == 1:
		return redirect("/gameplay")

@app.route("/await_turn", methods = ["POST", "GET"])
@login_required
def await_turn():
	player = current_user.id
	game = session.get("game")
	channel = str(game)
	usergame = model.session.query(model.Usergame).filter(and_(model.Usergame.user_id == player, model.Usergame.game_id == game)).all()
	usergame = usergame[0]
	other_players = model.session.query(model.Usergame).filter(and_(model.Usergame.game_id == game, model.Usergame.position != usergame.position)).all()
	other_player = other_players[0]
	draw_pile = usergame.game.draw_pile
	if usergame.miles == 1000:
		return redirect("/winner")
	elif other_players[0].miles == 1000:
		return redirect("/loser")
	draw_pile = usergame.game.draw_pile
	if len(draw_pile) == 0:
		usergame.game_status += 2
		other_player.game_status += 2
		return redirect("/tie_game")
	dealt_cards = usergame.hand
	dealt_tuple = str(dealt_cards)
	dealt_list = dealt_tuple.split(',')
	names = model.Usergame.cards_in_hand(usergame, dealt_list)
	player_miles = usergame.miles
	player_status = model.Usergame.check_status(usergame)
	player_speed = model.Usergame.check_speed(usergame)
	player_immunity = model.Usergame.check_immunities(usergame)
	op_miles = other_players[0].miles
	op_status = model.Usergame.check_status(other_players[0])
	op_speed = model.Usergame.check_speed(other_players[0])
	op_immunity = model.Usergame.check_immunities(other_players[0])
	return render_template("await_turn.html", names = names, channel = channel,
		player_miles = player_miles, player_status = player_status,	player_speed = player_speed,
		player_immunity = player_immunity, op_miles = op_miles, op_status = op_status,
		op_speed = op_speed, op_immunity = op_immunity)

#View to display player options from hand.
#Evaluates options for all valid moves based on both player statuses before displaying.
@app.route("/gameplay", methods = ["POST", "GET"])
@login_required
def gameplay():
	player = current_user.id
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter(and_(model.Usergame.user_id == player, model.Usergame.game_id == game)).all()
	usergame = usergame[0]
	other_players = model.session.query(model.Usergame).filter(and_(model.Usergame.game_id == game, model.Usergame.position != usergame.position)).all()
	if usergame.miles == 1000:
		return redirect("/winner")
	elif other_players[0].miles == 1000:
		return redirect("/loser")
	draw_pile = usergame.game.draw_pile
	if len(draw_pile) == 0:
		return redirect("/tie_game")
	dealt_cards = usergame.hand
	dealt_tuple = str(dealt_cards)
	dealt_list = dealt_tuple.split(',')
	names = model.Usergame.cards_in_hand(usergame, dealt_list)
	valid_moves = []

	def check_hazards(card, other_player):
		if card.action == "out of gas":
			if other_player.can_have_low_gas == 1 and str(other_player.immunities)[0] != "1":
				return card
			else: return None
		elif card.action == "flat tire":
			if other_player.can_have_flat == 1 and str(other_player.immunities)[1] != "1":
				return card
			else: return None
		elif card.action == "accident":
			if other_player.can_be_in_accident == 1 and str(other_player.immunities)[2] != "1":
				return card
			else: return None
		elif card.action == "speed limit":
			if other_player.can_have_speed_limit == 1 and str(other_player.immunities)[3] != "1":
				return card
			else: return None
		elif card.action == "stop":
			if other_player.can_be_stopped == 1 and str(other_player.immunities)[3] != "1":
				return card
			else: return None

	def check_miles(card):
		if usergame.can_go == 1:
			if int(card.action) == 200:
				if usergame.miles <= 800 and usergame.speed_limit < 50:
					return card
				else: return None
			elif int(card.action) == 100:
				if usergame.miles <= 900 and usergame.speed_limit < 50:
					return card
				else: return None
			elif int(card.action) == 75:
				if usergame.miles <= 925 and usergame.speed_limit < 50:
					return card
				else: return None
			elif int(card.action) == 50:
				if usergame.miles <= 950:
					return card
				else: return None
			elif int(card.action) == 25:
				if usergame.miles <= 975:
					return card
				else: return None
		else:
			return None

	def check_remedy(card):
		if card.action == "gasoline":
			if usergame.gas_empty == 1:
				return card
			else: return None
		elif card.action == "spare tire":
			if usergame.has_flat == 1:
				return card
			else: return None
		elif card.action == "repairs":
			if usergame.has_accident == 1:
				return card
			else: return None
		elif card.action == "end of limit":
			if usergame.speed_limit == 1:
				return card
		elif card.action == "roll":
			if usergame.can_go == 0:
				if usergame.gas_empty == 0 and usergame.has_flat == 0 and usergame.has_accident == 0:
					return card
			else: return None

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

		player_miles = usergame.miles
		player_status = model.Usergame.check_status(usergame)
		player_speed = model.Usergame.check_speed(usergame)
		player_immunity = model.Usergame.check_immunities(usergame)
		op_miles = other_players[0].miles
		op_status = model.Usergame.check_status(other_players[0])
		op_speed = model.Usergame.check_speed(other_players[0])
		op_immunity = model.Usergame.check_immunities(other_players[0])
	return render_template("gameplay.html", names = names, valid_moves = valid_moves,
		miles = player_miles, status = player_status, limit = player_speed,
		op_miles = op_miles, op_status = op_status, op_speed = op_speed,
		player_immunity = player_immunity, op_immunity = op_immunity)

#Draw view, forces player to draw card if there are less than 7 cards in player hand.
@app.route("/draw", methods = ["POST", "GET"])
@login_required
def draw():
	player = current_user.id
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter_by(user_id = player, game_id = game).all()
	usergame = usergame[0]
	game_object = model.session.query(model.Game).get(game)
	draw_pile = game_object.draw_pile
	if len(draw_pile) == 0:
		p[str_game].trigger('tied', {})
		return redirect("/tie_game")
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

#View to discard selected card if it is not a valid move.
@app.route("/discard/<int:id>", methods = ["POST", "GET"])
@login_required
def discard(id):
	player_id = current_user.id
	game = session.get("game")
	str_game = str(game)
	p[str_game].trigger('an_event', {"played" : "discard" })
	usergame = model.session.query(model.Usergame).filter_by(user_id = player_id, game_id = game).all()
	usergame = usergame[0]
	other_players = model.session.query(model.Usergame).filter(and_(model.Usergame.game_id == game, model.Usergame.position != usergame.position)).all()
	other_player = other_players[0]
	discarded = model.session.query(model.Card).get(id)
	hand = usergame.hand
	hand = str(hand)
	hand = hand.split(',')
	for card in hand:
		if int(card) == id:
			hand.remove(card)
	new_hand = ','.join(hand)
	usergame.hand = new_hand
	usergame.position = 2
	other_player.position = 1
	model.session.commit()
	return redirect("/turn")

#View to evaluate players selected card and update database with new move.
#Changes position for next player turn.
@app.route("/play_card/<int:id>", methods = ["POST", "GET"])
@login_required
def play_card(id):
	player_id = current_user.id
	game = session.get("game")
	usergame = model.session.query(model.Usergame).filter_by(user_id = player_id, game_id = game).all()
	usergame = usergame[0]
	other_players = model.session.query(model.Usergame).filter(and_(model.Usergame.game_id == game, model.Usergame.position != usergame.position)).all()
	other_player = other_players[0]
	usergame_hand = usergame.hand
	string_hand = str(usergame_hand)
	split_hand = string_hand.split(',')
	card = model.session.query(model.Card).get(id)
	str_game = str(game)
	for i in split_hand:
		if int(i) == id:
			split_hand.remove(i)
	new_hand = ','.join(split_hand)
	usergame.hand = new_hand
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
			p[str_game].trigger('winner', {})
			usergame.game_status += 1
			other_player.game_status += 3
			return redirect("/winner")
		else:
			p[str_game].trigger('an_event', {"played" : card.action })
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
 	elif card.type == "hazard":
 		if card.action == "out of gas":
 			stop_everything()
 			other_player.gas_empty = 1
 		if card.action == "flat tire":
 			stop_everything()
 			other_player.has_flat = 1
 		if card.action == "accident":
 			stop_everything()
 			other_player.has_accident = 1
 		if card.action == "stop":
 			stop_everything()
 		if card.action == "speed limit":
 			other_player.speed_limit = 50
 		update_turns()
	elif card.type == "remedy":
		if card.action == "roll":
			start_everything()
		if card.action == "gasoline":
			usergame.gas_empty = 0
		if card.action == "spare tire":
			usergame.has_flat = 0
		if card.action == "repairs":
			usergame.has_accident = 0
		if card.action == "end of limit":
			speed_limit = 0
		update_turns()
	p[str_game].trigger('an_event', {"played" : card.action })
	model.session.commit()
	return redirect("/turn")

@app.route("/winner")
def winner():
	return "You Won!"

@app.route("/loser")
def loser():
	return "You lost :("

@app.route("/tie_game")
def tie_game():
	return "Out of cards! This game is a draw."

@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')

app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

if __name__ == "__main__":
	app.run(debug = True)

