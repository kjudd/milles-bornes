# from flask import Flask
# from wtforms import Form, BooleanField, TextField, PasswordField, IntegerField, validators
from flask_wtf import Form, TextField, BooleanField, PasswordField
from flask_wtf import Required, validators

class RegistrationForm(Form):
    name = TextField('name', [validators.Length(min=1, max=25)])
    email = TextField('email', [validators.Length(min=6, max=35)])
    password = PasswordField('password', [Required()])

class LoginForm(Form):
	email = TextField('email', [validators.Length(min=6, max=35)])
	password = PasswordField('password', [Required()])