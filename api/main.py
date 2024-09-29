import sys
import sqlite3
from fastapi import FastAPI, HTTPException, Query,  Depends, status
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
#librerias de session
from sqlalchemy.orm import Session
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm
from jose import JWSError, jwt 
from datetime import datetime, timedelta
from passlib.context import CryptContext
#from database import SessionLocal, engine
#from models import User
#librerias acceso a api externa
import httpx
from fastapi.responses import JSONResponse


#configuracion para session de usuarios
#base de datos
dbJwt ="session.db"
#outh2 scheme
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#fin configuracion para session de usuarios

db ="dbReservas.db"

version = "{sys.version_info.major}.{sys.version_info.minor}"

app = FastAPI()

#origins = ["http://localhost:3000","https://padel-app-odwu.onrender.com,*"]
origins = ["*"]
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins= origins,  # Origins allowed to access the backend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
async def read_root():
    message = "Hello world! From FastAPI running on Uvicorn with Gunicorn. Using Python {version}"
    return {"message": message}


# Database model for the Recordatorio
class Recordatorio(BaseModel):
    titulo: str
    descripcion: str
    fecha: str
    hora: str
    
# Definir el modelo de datos para la reserva
class Reserva(BaseModel):
    cancha_id: int
    usuario_id: int
    horario_id: int
    descripcion: str
    num_personas: int


# Conectar a la base de datos y crear la tabla si no existe
def init_db():
    conn = sqlite3.connect(db)
    c = conn.cursor() 
    
    #creacion tabla recordatorios
    c.execute('''
              CREATE TABLE IF NOT EXISTS recordatorios
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              titulo TEXT,
              descripcion TEXT,
              fecha DATE,
              hora TIME)
              ''')
    
    #creacion tabla reservas
    c.execute('''
              CREATE TABLE IF NOT EXISTS reservas
              (reserva_id INTEGER PRIMARY KEY AUTOINCREMENT,
              cancha_id INTEGER,
              usuario_id INTEGER,
              horario_id DATETIME,
              descripcion TEXT,
              num_personas INTEGER)
              ''')
    conn.commit()
    conn.close()

init_db()

# Ruta para crear un nuevo recordatorio (Alta)
@app.post("/recordatorio")
def create_recordatorio(recordatorio: Recordatorio):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO recordatorios (titulo, descripcion, fecha, hora) VALUES (?, ?, ?, ?)",
              (recordatorio.titulo, recordatorio.descripcion, recordatorio.fecha, recordatorio.hora))
    conn.commit()
    conn.close()

    return {"message": "Recordatorio creado con \u00e9xito"}

# Ruta para obtener la lista de recordatorios
@app.get("/recordatorios", response_model=List[Recordatorio])
async def get_recordatorios():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT id, titulo, descripcion, fecha, hora FROM recordatorios")
    rows = c.fetchall()
    conn.close()

    recordatorios = [Recordatorio(id=row[0],titulo=row[1], descripcion=row[2], fecha=row[3], hora=row[4]) for row in rows]
    return recordatorios


# Ruta para crear una nueva reserva
@app.post('/reserva')
async def create_reserva(reserva: Reserva):
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO reservas (cancha_id, usuario_id, horario_id, descripcion, num_personas) VALUES (?, ?, ?, ?, ?)",
              (reserva.cancha_id, reserva.usuario_id, reserva.horario_id, reserva.descripcion, reserva.num_personas))
    conn.commit()
    conn.close()
    
    return {"message": "Reserva creada con \u00e9xito"}

# Ruta para obtener la lista de reservas
@app.get('/reservas', response_model=list[Reserva])
async def get_reservas():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT cancha_id, usuario_id, horario_id, descripcion, num_personas FROM reservas")
    reservas = c.fetchall()
    conn.close()
    
    # Convertir los resultados en una lista de diccionarios
    reservas_list = [
        {"cancha_id": row[0], "usuario_id": row[1], "horario_id": row[2], "descripcion": row[3], "num_personas": row[4]}
        for row in reservas
    ]
    
    return reservas_list

# Ruta para modificar un recordatorio existente
@app.put("/recordatorio/{id}")
def update_recordatorio(id: int, recordatorio: Recordatorio):
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Verificar si el recordatorio existe
    c.execute("SELECT * FROM recordatorios WHERE id = ?", (id,))
    existing_recordatorio = c.fetchone()

    if existing_recordatorio:
        # Actualizar el recordatorio
        c.execute('''
                  UPDATE recordatorios
                  SET titulo = ?, descripcion = ?, fecha = ?, hora = ?
                  WHERE id = ?
                  ''', (recordatorio.titulo, recordatorio.descripcion, recordatorio.fecha, recordatorio.hora, id))
        conn.commit()
        conn.close()

        return {"message": "Recordatorio actualizado con éxito"}
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

# Ruta para modificar una reserva existente
@app.put("/reserva/{reserva_id}")
def update_reserva(reserva_id: int, reserva: Reserva):
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Verificar si la reserva existe
    c.execute("SELECT * FROM reservas WHERE reserva_id = ?", (reserva_id,))
    existing_reserva = c.fetchone()

    if existing_reserva:
        # Actualizar la reserva
        c.execute('''
                  UPDATE reservas
                  SET cancha_id = ?, usuario_id = ?, horario_id = ?, descripcion = ?, num_personas = ?
                  WHERE reserva_id = ?
                  ''', (reserva.cancha_id, reserva.usuario_id, reserva.horario_id, reserva.descripcion, reserva.num_personas, reserva_id))
        conn.commit()
        conn.close()

        return {"message": "Reserva actualizada con éxito"}
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    
    # Ruta para eliminar un recordatorio por ID
@app.delete("/recordatorio/{id}")
def delete_recordatorio(id: int):
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Verificar si el recordatorio existe
    c.execute("SELECT * FROM recordatorios WHERE id = ?", (id,))
    existing_recordatorio = c.fetchone()

    if existing_recordatorio:
        # Eliminar el recordatorio
        c.execute("DELETE FROM recordatorios WHERE id = ?", (id,))
        conn.commit()
        conn.close()

        return {"message": "Recordatorio eliminado con éxito"}
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

# Ruta para eliminar una reserva por ID
@app.delete("/reserva/{reserva_id}")
def delete_reserva(reserva_id: int):
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Verificar si la reserva existe
    c.execute("SELECT * FROM reservas WHERE reserva_id = ?", (reserva_id,))
    existing_reserva = c.fetchone()

    if existing_reserva:
        # Eliminar la reserva
        c.execute("DELETE FROM reservas WHERE reserva_id = ?", (reserva_id,))
        conn.commit()
        conn.close()

        return {"message": "Reserva eliminada con éxito"}
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    

#llamada a api externa
# Replace these with actual URLs for the external services
HORARIOS_API_URL = "https://e114-181-171-103-188.ngrok-free.app/api/horarios"
CANCHAS_API_URL = "https://e114-181-171-103-188.ngrok-free.app/api/canchas"
USUARIOS_API_URL = "https://e114-181-171-103-188.ngrok-free.app/api/usuarios"

@app.get("/horariosreservas")
async def get_horario_reserva():
    async with httpx.AsyncClient() as client:
        # Fetching the external data
        #horarios_response = await client.get(HORARIOS_API_URL)
        #canchas_response = await client.get(CANCHAS_API_URL)
        
        #mock canchas and horarios
        horarios = [
            {"horario_id": 1, "fecha": "2024-09-23", "hora": "10:00"},
            {"horario_id": 2, "fecha": "2024-09-28", "hora": "12:00"},
            {"horario_id": 3, "fecha": "2024-09-30", "hora": "14:00"},
            {"horario_id": 4, "fecha": "2024-10-01", "hora": "16:00"},
            {"horario_id": 5, "fecha": "2024-10-04", "hora": "18:00"},
            {"horario_id": 6, "fecha": "2024-10-06", "hora": "20:00"},
            {"horario_id": 7, "fecha": "2024-10-09", "hora": "22:00"},
            {"horario_id": 8, "fecha": "2024-10-12", "hora": "10:00"},
        ]

        canchas = [
            {"cancha_id": 1, "nombre": "Cancha A", "ubicacion": "Location A"},
            {"cancha_id": 2, "nombre": "Cancha B", "ubicacion": "Location B"},
            {"cancha_id": 3, "nombre": "Cancha C", "ubicacion": "Location C"},
        ]

        
        usuarios_response = await client.get(USUARIOS_API_URL)
        
        # Parsing JSON responses
        #horarios = horarios_response.json()
        #canchas = canchas_response.json()
        if usuarios_response.status_code == 200:
            usuarios = usuarios_response.json()
        else:
            print(f"Error: {usuarios_response.status_code}, {usuarios_response.text}")
            usuarios = [{"id":1,"nivel":"intermedio","apellido":"Lopez","recontrasena":"ana2024!","edad":"22","alias":"aLopez","contrasena":"ana2024!","telefono":"5491123456","fotoPerfil":"perfil_ana.jpg","idTipoUsuario":4,"nombre":"Ana","tipoDeJuego":"Deportes","email":"ana.lopez@example.com","genero":"Femenino","direccion":"Paseo de los Olmos 100","remail":"ana.lopez@example.com"},
                        {"id":2,"nivel":"intermedio","apellido":"Perez","recontrasena":"test","edad":"22","alias":"Pepe","contrasena":"test","telefono":"5411112233","fotoPerfil":"algo.jpg","idTipoUsuario":3,"nombre":"Juan","tipoDeJuego":"Drive","email":"juan.perez@example.com","genero":"Femenino","direccion":"Paseo de los Olmos 100","remail":"ana.lopez@example.com"}]
        

    # fetch reservas from the local DB
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("SELECT reserva_id, cancha_id, usuario_id, horario_id, descripcion, num_personas FROM reservas")
    reservas = c.fetchall()
    conn.close()
    
    # Convertir los resultados en una lista de diccionarios
    reservas = [
        {"reserva_id":row[0], "cancha_id": row[1], "usuario_id": row[2], "horario_id": row[3], "descripcion": row[4], "num_personas": row[5]}
        for row in reservas
    ]

    # Map cancha_id and usuario_id to their details
    cancha_map = {cancha['cancha_id']: cancha for cancha in canchas}
    usuario_map = {usuario['id']: {'nombre': usuario['nombre'], 'apellido': usuario['apellido']} for usuario in usuarios}

    # Combine the data
    horarioreserva_array = []

    for horario in horarios:
        horarioreserva = {
            "horario_id": horario['horario_id'],
            "fecha": horario['fecha'],
            "hora": horario['hora'],
            "reserva": None
        }

        for reserva in reservas:
            if reserva['horario_id'] == horario['horario_id']:
                cancha = cancha_map.get(reserva['cancha_id'], {})
                usuario = usuario_map.get(reserva['usuario_id'], {})

                horarioreserva['reserva'] = {
                    "reserva_id": reserva['reserva_id'],
                    "descripcion": reserva['descripcion'],
                    "num_personas": reserva['num_personas'],
                    "cancha": cancha,  # Include cancha details
                    "usuario": usuario  # Include user details
                }
                break  # Only one reserva per horario

        horarioreserva_array.append(horarioreserva)

    return JSONResponse(content=horarioreserva_array)




if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181)
    
