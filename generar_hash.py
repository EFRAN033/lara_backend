from passlib.context import CryptContext

# Configuración estándar para FastAPI
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# La contraseña que quieres usar para tu admin
contraseña_plana = "admin" 

# Generamos el hash
hash_generado = pwd_context.hash(contraseña_plana)

print("\n--- ¡Copia este hash! ---\n")
print(hash_generado)
print("\n--------------------------\n")