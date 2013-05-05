from flask_wtf import Form, TextField, BooleanField, PasswordField
from flask_wtf import Required, validators

class RegistrationForm(Form):
    name = TextField('Name', [validators.Length(min=1, max=25)])
    email = TextField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [Required()])

class LoginForm(Form):
	email = TextField('Email', [validators.Length(min=6, max=35)])
	password = PasswordField('Password', [Required()])