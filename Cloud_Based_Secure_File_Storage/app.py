from flask import Flask, session, render_template, request, redirect
import pyrebase

app = Flask(__name__)

#Connecting firebase

Config = {
    'apiKey' : "AIzaSyA1WxT_TMDuyXav2OEfQgqMtxPJrNOEgPg",
    'authDomain' : "filestorage-5c63d.firebaseapp.com",
    'projectId' : "filestorage-5c63d",
    'storageBucket' : "filestorage-5c63d.appspot.com",
    'messagingSenderId' : "432920813122",
    'appId' : "1:432920813122:web:893dfcdc5f616c084f57db",
    'measurementId' : "G-DMVJ96KF28",
    'databaseURL' : ''
  }

firebase = pyrebase.initialize_app(Config)
auth = firebase.auth()

#secret key

app.secret_key = 'closetheeyes'

#sign in process

@app.route('/', methods=['POST', 'GET'])
def index():
    if('user' in session):
        return render_template('index.html')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            session['user'] = email
            return redirect('/')
        except:
            return 'Invalid Data'
    return render_template('login.html')

#creating account in fb

@app.route('/register', methods=['POST', 'GET'])
def create_account():

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password != confirm_password:
            return 'Passwords do not match'
        try:
            user = auth.create_user_with_email_and_password(email, password)
            session['user'] = email
            return redirect('/')
        except:
            return 'Failed to create account'
    return render_template('register.html')

#logout session

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/')

if __name__ == '__main__':
    app.run(port=8888)