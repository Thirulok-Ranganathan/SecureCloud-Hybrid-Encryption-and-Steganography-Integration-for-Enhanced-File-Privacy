from flask import Flask, send_file, session, render_template, request, redirect, make_response
import pyrebase,requests, rsa, stepic
from firebase_admin import storage
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
from cryptography.fernet import Fernet
from PIL import Image


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

# authentication and keys
firebase = pyrebase.initialize_app(Config)
auth = firebase.auth()
app.secret_key = 'closetheeyes'
ivs = 'wegotit'
key = RSA.generate(3072)
pubkey = key.publickey().export_key('PEM')
prikey = key.export_key('PEM')
ferkey = Fernet.generate_key()

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
            usr_finder = email.rfind("@")
            usr_name = email[:usr_finder]
            session['usrname'] = usr_name
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
            usr_finder = email.rfind("@")
            usr_name = email[:usr_finder]
            session['usrname'] = usr_name
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
        img_file = request.files['upload_image']
        without_ext = file_name.rfind(".")
        filename_no_ext = file_name[:without_ext]

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

        #Working on secret_keys

        enc = Fernet(ferkey)
        key_enc = enc.encrypt(prikey)
        img = Image.open(img_file)
        img_stego = stepic.encode(img, key_enc)
        img_stego.save(filename_no_ext+"keyimage.png")

        with open(filename_no_ext+'keytext.txt','wb') as maif:
            maif.write(ferkey)
        

        #Now rsa encrypt
        message = ciphertext
        puky = RSA.import_key(pubkey)
        new_cipher = PKCS1_OAEP.new(puky)
        encytxt = new_cipher.encrypt(message)

        #uploading

        try:
            storage.child(cloud_name).put(encytxt)
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
            key_file = request.files['key_file_from_user']
            key_value = request.files['key_text']
            simg = Image.open(key_file)
            value_byte_key = key_value.read()

            # Getting the file from cloud
            encrypted_file = storage.child(cloud_name).get_url(None)
            response_file = requests.get(encrypted_file)
            bytes_data = response_file.content

            #image to key
            decode_img = stepic.decode(simg)
            dec = Fernet(value_byte_key)
            disp = dec.decrypt(decode_img.encode())
            

            #rsa contents
            pkey = RSA.import_key(disp.decode())
            nw_cip = PKCS1_OAEP.new(pkey)
            ori_enc = nw_cip.decrypt(bytes_data)

            # decrypting AES
            key = pwd.encode('UTF-8')
            key = pad(key, AES.block_size)
            ive = ivs.encode('UTF-8')
            iv = pad(ive, AES.block_size)
            key = key.ljust(16, b'\0')
            iv = iv.ljust(16, b'\0')
            
            
            AES_obj = AES.new(key, AES.MODE_CBC, iv)
            cl_file = AES_obj.decrypt(ori_enc)
            source_content = unpad(cl_file, AES.block_size)
            

            with open("data/exports"+'/'+file_name, 'wb') as f:
               f.write(source_content)

            return send_file("data/exports"+'/'+file_name, as_attachment=True)

        return render_template('download.html')
    return render_template('success.html')

if __name__ == '__main__':
    app.run(port=8888)