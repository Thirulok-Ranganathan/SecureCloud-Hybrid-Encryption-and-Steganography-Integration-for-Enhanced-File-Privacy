from flask import Flask, send_file, session, render_template, request, redirect
import pyrebase,requests
from firebase_admin import storage
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


app = Flask(__name__)

Config = {
  'apiKey': "AIzaSyAzStENNKhEl1FEIsUitAQPj8b3W-9eKl0",
  'authDomain': "cloudstorage-c094b.firebaseapp.com",
  'projectId': "cloudstorage-c094b",
  'storageBucket': "cloudstorage-c094b.appspot.com",
  'messagingSenderId': "493585810197",
  'appId': "1:493585810197:web:8e19eb174dbd4cf7a19f1c",
  'measurementId': "G-Q7QQL6MJZ6",
  'databaseURL' : ''
}

firebase = pyrebase.initialize_app(Config)
auth = firebase.auth()
app.secret_key = 'closetheeyes'
ivs = 'wegotit'

# login user or Homepage

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
            session['key'] = password
            return redirect('/')
        except:
            return 'Invalid Data'
    return render_template('login.html')

# register for account

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
        pwd = session['key']
    if request.method == 'POST':
        try:
            ori_file = request.files['upload_file']
        except KeyError:
            return 'No file selected'
        file_name = request.form.get('file_name')
        cloud_name = email+'/'+file_name

        # Encrypting the data and key
        key = pwd.encode('UTF-8')
        key = pad(key, AES.block_size)
        ive = ivs.encode('UTF-8')
        iv = pad(ive, AES.block_size)
        
        key = key.ljust(16, b'\0')
        iv = iv.ljust(16, b'\0')
        
        
        #Encrypting the file
        data = ori_file.read()
        new_data = pad(data, AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(new_data)


        #uploading

        try:
            storage.child(cloud_name).put(ciphertext)
            return render_template('success.html')
        
        except Exception as e:
            print(str(e))
            return 'Error uploading file'
          
    return render_template('upload.html')

@app.route('/download', methods=['POST','GET'])
def download_file():
    if('user' in session):
        email = session['user']
        pwd = session['key']
        if request.method == 'POST':
            file_name = request.form.get('download_file_name')
            cloud_name = email+'/'+file_name

            # Getting the file from cloud
            encrypted_file = storage.child(cloud_name).get_url(None)
            response_file = requests.get(encrypted_file)
            bytes_data = response_file.content
            # decrypting AES
            key = pwd.encode('UTF-8')
            key = pad(key, AES.block_size)
            ive = ivs.encode('UTF-8')
            iv = pad(ive, AES.block_size)
            key = key.ljust(16, b'\0')
            iv = iv.ljust(16, b'\0')
            
            
            AES_obj = AES.new(key, AES.MODE_CBC, iv)
            cl_file = AES_obj.decrypt(bytes_data)
            source_content = unpad(cl_file, AES.block_size)
            

            with open(file_name, 'wb') as f:
               f.write(source_content)

            return send_file(file_name, as_attachment=True)

        return render_template('download.html')
    return render_template('success.html')

if __name__ == '__main__':
    app.run(port=8888)