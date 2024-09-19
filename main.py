from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from typing import List
from fastapi.middleware.cors import CORSMiddleware

# Cargar variables de entorno
load_dotenv()

app = FastAPI()

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las fuentes (dominios) de origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todas las cabeceras
)

# Conexión a la base de datos MongoDB
MONGO_DETAILS = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_DETAILS)
db = client['finpro_db']  # Nombre de la base de datos
contacts_collection = db['contacts']  # Colección donde almacenaremos los mensajes

# Esquema del mensaje
class Contact(BaseModel):
    name: str
    email: EmailStr
    message: str

class ContactInDB(Contact):
    id: str

# Crear un contacto en la base de datos
async def add_contact(contact: Contact):
    contact_data = contact.dict()
    result = await contacts_collection.insert_one(contact_data)
    return str(result.inserted_id)

# Obtener todos los contactos
async def retrieve_contacts():
    contacts = []
    async for contact in contacts_collection.find():
        contacts.append(ContactInDB(
            id=str(contact["_id"]),
            name=contact["name"],
            email=contact["email"],
            message=contact["message"]
        ))
    return contacts

# Ruta para recibir y almacenar el formulario de contacto
@app.post("/contact")
async def create_contact(contact: Contact):
    contact_id = await add_contact(contact)
    if not contact_id:
        raise HTTPException(status_code=400, detail="Error al guardar el mensaje")
    return {"message": "Mensaje enviado correctamente", "contact_id": contact_id}

# Ruta para obtener todos los contactos
@app.get("/contacts", response_model=List[ContactInDB])
async def get_contacts():
    contacts = await retrieve_contacts()
    if not contacts:
        raise HTTPException(status_code=404, detail="No hay contactos disponibles")
    return contacts
