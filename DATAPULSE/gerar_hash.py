from werkzeug.security import generate_password_hash

senha = "TxcE47g!"
hash_senha = generate_password_hash(senha)

print("HASH GERADO:")
print(hash_senha)
