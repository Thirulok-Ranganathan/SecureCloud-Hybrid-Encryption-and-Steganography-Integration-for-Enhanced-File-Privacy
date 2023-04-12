from flask import Flask, send_file, session, render_template, request, redirect
import pyrebase
from cryptography.fernet import Fernet
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from firebase_admin import storage
import requests


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
key = Fernet.generate_key()

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


#upload files to cloud

storage = firebase.storage()

@app.route('/upload', methods=['POST','GET'])
def upload_file():
    if('user' in session):
        email = session['user']
    if request.method == 'POST':
        try:
            uploaded_file = request.files['upload_file']
        except KeyError:
            return 'No file selected'
        file_name = request.form.get('file_name')
        cloud_name = email+'/'+file_name    


        # encrpting process with fernet

        with open('secretkey.key', 'rb') as f:
            key = f.read()

        fk = Fernet(key)

        encrypted_file_content = fk.encrypt(uploaded_file.read())

        # generating rsa keys

        rsaky = RSA.generate(2048)

        with open('private_key.pem', 'wb') as privateky:
            privateky.write(rsaky.export_key())

        publicky = rsaky.publickey()

        cipher_rsa = PKCS1_OAEP.new(publicky)
        encrypted_file_content_rsa = cipher_rsa.encrypt(encrypted_file_content)

        #uploading

        try:
            storage.child(cloud_name).put(encrypted_file_content_rsa)
            session['key'] = key
            return render_template('success.html')
        
        except Exception as e:
            print(str(e))
            return 'Error uploading file'
          
    return render_template('upload.html')



@app.route('/download', methods=['POST','GET'])
def download_file():
    if('user' in session):
        email = session['user']
        if request.method == 'POST':
            file_name = request.form.get('download_file_name')
            private_key = request.files['key_file'].read()

            cloud_name = email+'/'+file_name

             # download encrypted file from Firebase
            encrypted_file = storage.child(cloud_name).get_url(None)
            response = requests.get(encrypted_file)

            # decrypt with RSA private key
            rsaky = RSA.import_key(private_key)
            cipher_rsa = PKCS1_OAEP.new(rsaky)
            decrypted_file_content_rsa = cipher_rsa.decrypt(response.content)

            # decrypt with Fernet key
            with open('secretkey.key', 'rb') as f:
                key = f.read()
            fk = Fernet(key)
            decrypted_file_content = fk.decrypt(decrypted_file_content_rsa)

            # save decrypted file to disk
            with open(file_name, 'wb') as f:
                f.write(decrypted_file_content)

            return send_file(file_name, as_attachment=True)

        return render_template('download.html')
    return render_template('success.html')



#port

if __name__ == '__main__':
    app.run(port=8888)



