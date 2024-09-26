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

#configuracion para session de usuarios
#base de datos
dbJwt ="session.db"
#outh2 scheme
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

#fin configuracion para session de usuarios

db ="dbReservas.db"

version = "{sys.version_info.major}.{sys.version_info.minor}"

app = FastAPI()

origins = ["http://localhost:3000","https://padel-app-odwu.onrender.com"]

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


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181)
    
