from cryptography.fernet import Fernet

key = Fernet.generate_key()

with open ('secretkey.key','wb') as file:
    file.write(key)