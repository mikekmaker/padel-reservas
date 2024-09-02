import sys
import sqlite3
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List,Optional
from fastapi.middleware.cors import CORSMiddleware

version = f"{sys.version_info.major}.{sys.version_info.minor}"

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","https://padel-reservas.onrender.com/"],  # Origins allowed to access the backend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


@app.get("/")
async def read_root():
    message = f"Hello world! From FastAPI running on Uvicorn with Gunicorn. Using Python {version}"
    return {"message": message}


# Database model for the Recordatorio
class Recordatorio(BaseModel):
    titulo: str
    descripcion: str
    fecha: str
    hora: str

# Conectar a la base de datos y crear la tabla si no existe
def init_db():
    conn = sqlite3.connect('recordatorios.db')
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS recordatorios
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              titulo TEXT,
              descripcion TEXT,
              fecha DATE,
              hora TIME)
              ''')
    conn.commit()
    conn.close()

init_db()

# Ruta para crear un nuevo recordatorio (Alta)
@app.post("/recordatorio")
def create_recordatorio(recordatorio: Recordatorio):
    conn = sqlite3.connect('recordatorios.db')
    c = conn.cursor()
    c.execute("INSERT INTO recordatorios (titulo, descripcion, fecha, hora) VALUES (?, ?, ?, ?)",
              (recordatorio.titulo, recordatorio.descripcion, recordatorio.fecha, recordatorio.hora))
    conn.commit()
    conn.close()

    return {"message": "Recordatorio creado con \u00e9xito"}

# Ruta para obtener la lista de recordatorios
@app.get("/recordatorios", response_model=List[Recordatorio])
async def get_recordatorios():
    conn = sqlite3.connect('recordatorios.db')
    c = conn.cursor()
    c.execute("SELECT id, titulo, descripcion, fecha, hora FROM recordatorios")
    rows = c.fetchall()
    conn.close()

    recordatorios = [Recordatorio(id=row[0],titulo=row[1], descripcion=row[2], fecha=row[3], hora=row[4]) for row in rows]
    return recordatorios

# Conectar a la base de datos y crear la tabla si no existe
def init_db():
    conn = sqlite3.connect('reservas.db')
    c = conn.cursor()
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

# Definir el modelo de datos para la reserva
class Reserva(BaseModel):
    cancha_id: int
    usuario_id: int
    horario_id: str  # Se usa str para manejar fechas y horas en formato ISO
    descripcion: str
    num_personas: int

# Ruta para crear una nueva reserva
@app.post('/reserva')
async def create_reserva(reserva: Reserva):
    conn = sqlite3.connect('reservas.db')
    c = conn.cursor()
    c.execute("INSERT INTO reservas (cancha_id, usuario_id, horario_id, descripcion, num_personas) VALUES (?, ?, ?, ?, ?)",
              (reserva.cancha_id, reserva.usuario_id, reserva.horario_id, reserva.descripcion, reserva.num_personas))
    conn.commit()
    conn.close()
    
    return {"message": "Reserva creada con \u00e9xito"}

# Ruta para obtener la lista de reservas
@app.get('/reservas', response_model=list[Reserva])
async def get_reservas():
    conn = sqlite3.connect('reservas.db')
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

# Database model for the Usuario
class Usuario(BaseModel):
    usuarioid: int
    alias: str
    contrasena: str
    nombre: str
    apellido: str
    genero: str
    edad: str
    direccion: str
    email: str
    telefono: str
    nivel: str
    tipoJuego: str
    fotoperfil: Optional[str]  # Assuming a base64 string
    idtipousuario: int

# Conectar a la base de datos y crear la tabla si no existe
def init_db():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS usuarios
              (usuarioid INTEGER PRIMARY KEY AUTOINCREMENT,
              alias TEXT,
              contrasena,
              nombre TEXT,
              apellido TEXT,
              genero TEXT,
              edad TEXT,
              direccion TEXT,
              email TEXT,
              telefono TEXT,
              nivel TEXT,
              tipoJuego TEXT,
              fotoperfil TEXT,
              idtipousuario INTEGER)
              ''')
    conn.commit()
    conn.close()

init_db()

@app.post("/usuario")
async def create_usuario(usuario: Usuario):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO usuarios 
        (alias, contrasena, nombre, apellido, genero, edad, direccion, email, telefono, nivel, tipoJuego, fotoperfil, idtipousuario) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (usuario.alias, usuario.contrasena, usuario.nombre, usuario.apellido, usuario.genero, usuario.edad,
         usuario.direccion, usuario.email, usuario.telefono, usuario.nivel, usuario.tipoJuego, 
         usuario.fotoperfil, usuario.idtipousuario)
    )
    conn.commit()
    conn.close()
    
    return {"message": "Usuario creado con \u00e9xito"}

# Endpoint to retrieve all usuarios
@app.get("/usuarios", response_model=List[Usuario])
async def get_usuarios():
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''
        SELECT usuarioid, alias, contrasena, nombre, apellido, genero, edad, direccion, email, telefono, nivel, tipoJuego, fotoperfil, idtipousuario
        FROM usuarios
    ''')
    rows = c.fetchall()
    conn.close()

    usuarios = [Usuario(
        usuarioid=row[0], alias=row[1], contrasena=row[2], nombre=row[3], apellido=row[4], genero=row[5], 
        edad=row[6], direccion=row[7], email=row[8], telefono=row[9], nivel=row[10], 
        tipoJuego=row[11], fotoperfil=row[12], idtipousuario=row[13]
    ) for row in rows]

    return usuarios  

# Endpoint to retrieve a usuario by alias and contrasena
@app.get("/usuario", response_model=Usuario)
async def get_usuario(alias: str = Query(...), contrasena: str = Query(...)):
    conn = sqlite3.connect('usuarios.db')
    c = conn.cursor()
    c.execute('''
        SELECT usuarioid, alias, contrasena, nombre, apellido, genero, edad, direccion, email, telefono, nivel, tipoJuego, fotoperfil, idtipousuario
        FROM usuarios WHERE alias = ? AND contrasena = ?
    ''', (alias, contrasena))
    row = c.fetchone()
    conn.close()

    if row:
        usuario = Usuario(
            usuarioid=row[0], alias=row[1], contrasena=row[2], nombre=row[3], apellido=row[4], genero=row[5],
            edad=row[6], direccion=row[7], email=row[8], telefono=row[9], 
            nivel=row[10], tipoJuego=row[11], fotoperfil=row[12], idtipousuario=row[13]
        )
        return usuario
    else:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181)
    
