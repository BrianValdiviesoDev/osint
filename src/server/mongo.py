import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

# Crea la URI de conexión a MongoDB
mongo_uri = os.environ.get("MONGO_DB_URI")

# Verifica si todas las variables de entorno necesarias están configuradas
if not mongo_uri:
    raise Exception("Faltan variables de entorno para la conexión a MongoDB")

# Crea un cliente de MongoDB
mongoConnection = MongoClient(mongo_uri)
db = mongoConnection.get_database()
