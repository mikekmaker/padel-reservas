import sys
import sqlite3
from fastapi import FastAPI, HTTPException, Query,  Depends, status, Response
from pydantic import BaseModel, Field, conint, validator, ValidationError
from typing import ClassVar, List, Optional
from fastapi.middleware.cors import CORSMiddleware
import re
#librerias de session
#from sqlalchemy.orm import Session
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm
#from jose import JWSError, jwt 
from datetime import datetime, timedelta
#from passlib.context import CryptContext
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
    
  # Los patrones de expresion regular como variables de clase
    fecha_pattern: ClassVar[re.Pattern] = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # Formato YYYY-MM-DD
    hora_pattern: ClassVar[re.Pattern] = re.compile(r"^(?:[01]\d|2[0-3]):([0-5]\d)$")  # Formato HH:MM (24 horas)

    # Usar la nueva sintaxis de Pydantic V2 para validadores
    @validator("fecha")
    def validate_fecha(cls, v):
        if not cls.fecha_pattern.match(v):
            raise ValueError("Fecha invalida. Usa el formato YYYY-MM-DD.")
        return v

    @validator("hora")
    def validate_hora(cls, v):
        if not cls.hora_pattern.match(v):
            raise ValueError("Hora invalida. Usa el formato HH:MM (24 horas).")
        return v
    
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
              fecha TEXT,
              hora TEXT)
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
@app.post("/recordatorio",status_code=status.HTTP_201_CREATED)
def create_recordatorio(recordatorio: Recordatorio,response:Response):
       
                     
    
    # Validar que 'titulo' no este vacio
    if not recordatorio.titulo.strip():
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "detail":"titulo",
            "msg": "El campo 'titulo' no puede estar vacio."
        }      
    
    # Validar que 'descripcion' no este vacia
    elif not recordatorio.descripcion.strip():
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "detail":"descripcion",
            "msg": "El campo 'descripcion' no puede estar vacio."
        }      
    
    # Validar que 'fecha' no este vacio
    elif not recordatorio.fecha.strip():
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "detail":"fecha",
            "msg": "El campo 'fecha' no puede estar vacio."
        }      
    
    # Validar que 'hora' no este vacio
    elif not recordatorio.hora.strip():
        response.status_code = status.HTTP_400_BAD_REQUEST

                                                                   
                    
        return {
            "detail":"hora",
            "msg": "El campo 'hora' no puede estar vacio."
                                        
        }      
     
    # Si las validaciones son correctas, se inserta el recordatorio en la base de datos
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO recordatorios (titulo, descripcion, fecha, hora) VALUES (?, ?, ?, ?)",
              (recordatorio.titulo, recordatorio.descripcion, recordatorio.fecha, recordatorio.hora))
    conn.commit()
    conn.close()
    
     # Obtenemos el ID del recordatorio recien creado
    recordatorio_id = c.lastrowid

    # Respuesta exitosa con los datos del recordatorio y el codigo 201
    return {
    
            "id": recordatorio_id,  # Se añade el ID del nuevo recordatorio
            "titulo": recordatorio.titulo,
            "descripcion": recordatorio.descripcion,
            "fecha": recordatorio.fecha,
            "hora": recordatorio.hora
    }
# Ruta para traer recordatorios existente (GET)
@app.get("/recordatorios")
async def get_recordatorios():
    # Conectar a la base de datos
    conn = sqlite3.connect(db)
    c = conn.cursor()
    
    # Ejecutar consulta para obtener todos los recordatorios
    c.execute("SELECT id, titulo, descripcion, fecha, hora FROM recordatorios")
    rows = c.fetchall()
    conn.close()
    
    # Forzar un error dividiendo entre cero (SIRVE PARA TIRAR UN ERROR 500)
    # error_forzado = 1 / 0  # Esto provocara un error 500   
    
    # Crear los objetos Recordatorio con los resultados de la base de datos
    recordatorios = [{"id": row[0], "titulo": row[1], "descripcion": row[2], "fecha": row[3], "hora": row[4]} for row in rows]
    
    # Devolver la lista de recordatorios con un codigo de estado 200 y estructura personalizada
    return JSONResponse(
        recordatorios,
        status_code=status.HTTP_200_OK
    )
# Ruta para modificar un recordatorio existente
@app.put("/recordatorio/{id}",status_code=status.HTTP_200_OK)
def update_recordatorio(id: int, recordatorio: Recordatorio,response:Response):
    conn = sqlite3.connect(db)
    c = conn.cursor()

                                   
                     

    # Verificar si el recordatorio existe
    c.execute("SELECT * FROM recordatorios WHERE id = ?", (id,))
    existing_recordatorio = c.fetchone()

    if existing_recordatorio:
        # Validaciones antes de actualizar
        if not recordatorio.titulo.strip():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
            "detail":"titulo",
            "msg": "El campo 'titulo' no puede estar vacio."
        }   
        elif not recordatorio.descripcion.strip():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
            "detail":"descripcion",
            "msg": "El campo 'descripcion' no puede estar vacio."
        }   
        elif not recordatorio.fecha.strip():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
            "detail":"fecha",
            "msg": "El campo 'fecha' no puede estar vacio."
        }   
        elif not recordatorio.hora.strip():
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
            "detail":"hora",
            "msg": "El campo 'hora' no puede estar vacio."
        }   
        
                                               
                        
                        
                                                                     

        # Actualizar el recordatorio
        c.execute('''
                  UPDATE recordatorios
                  SET titulo = ?, descripcion = ?, fecha = ?, hora = ?
                  WHERE id = ?
                  ''', (recordatorio.titulo, recordatorio.descripcion, recordatorio.fecha, recordatorio.hora, id))
        conn.commit()
        conn.close()

       # Crear el cuerpo de respuesta con el detalle de lo actualizado
        return {
                     
                "id": id,
                "titulo": recordatorio.titulo,
                "descripcion": recordatorio.descripcion,
                "fecha": recordatorio.fecha,
                "hora": recordatorio.hora
            
        }
    else:
        conn.close()
        # Enviar un error si no se encuentra el recordatorio
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

# Ruta para eliminar un recordatorio por ID
@app.delete("/recordatorio/{id}",status_code=status.HTTP_200_OK)
def delete_recordatorio(id: int):
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Inicializamos el detalleError
    detalleError = ""

    # Verificar si el recordatorio existe
    c.execute("SELECT * FROM recordatorios WHERE id = ?", (id,))
    existing_recordatorio = c.fetchone()

    if existing_recordatorio:
        # Eliminar el recordatorio
        c.execute("DELETE FROM recordatorios WHERE id = ?", (id,))
        conn.commit()
        conn.close()

        # Crear el cuerpo de respuesta con los detalles de lo eliminado
        return {         
                "id": id,
                "titulo": existing_recordatorio[1],
                "descripcion": existing_recordatorio[2],
                "fecha": existing_recordatorio[3],
                "hora": existing_recordatorio[4]
        }
    else:
        conn.close()
        # Enviar un error si no se encuentra el recordatorio
        raise HTTPException(status_code=404, detail="Recordatorio no encontrado")

# Ruta para crear una nueva reserva 
@app.post('/reserva',status_code=status.HTTP_201_CREATED)

                     
async def create_reserva(reserva: Reserva, response:Response):
                                                 
                     
    
    # Validar que cancha_id sea un entero mayor a 0
    if not isinstance(reserva.cancha_id, int) or reserva.cancha_id <= 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "detail":"cancha",
            "msg": "debe seleccionar una cancha valida"
        }
        
    # Validar que usuario_id sea un entero mayor a 0
    if not isinstance(reserva.usuario_id, int) or reserva.usuario_id <= 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "detail":"usuario",
            "msg": "debe seleccionar un usuario valida"
        }      
        
    
    # Validar que horario_id sea un entero mayor a 0
    elif not isinstance(reserva.horario_id, int) or reserva.horario_id <= 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "detail":"horario",
            "msg": "debe seleccionar un horario valido"
        }      
    
    # Validar que descripcion no este vacia
    elif not reserva.descripcion.strip():  # Validamos que descripcion no este vacia
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {
            "detail":"descripcion",
            "msg": "el campo 'descripcion' no debe estar vacio"
        }      
    
    # Validar que num_personas sea un entero mayor a 0
    elif not isinstance(reserva.num_personas, int) or reserva.num_personas <= 0:
        response.status_code = status.HTTP_400_BAD_REQUEST
    
                                                                   
                    
        return {
            "detail":"jugadores",
            "msg": "debe haber al menos 1 jugador"
                                        
        } 
    
    # Si las validaciones son correctas, insertamos en la base de datos
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("INSERT INTO reservas (cancha_id, usuario_id, horario_id, descripcion, num_personas) VALUES (?, ?, ?, ?, ?)",
              (reserva.cancha_id, reserva.usuario_id, reserva.horario_id, reserva.descripcion, reserva.num_personas))
     # Obtenemos el ID del recordatorio recien creado
    reserva_id = c.lastrowid
    conn.commit()
    conn.close()

    # Respuesta exitosa
    return {
            "id": reserva_id,
            "cancha_id": reserva.cancha_id,
            "usuario_id": reserva.usuario_id,
            "horario_id": reserva.horario_id,
            "descripcion": reserva.descripcion,
            "num_personas": reserva.num_personas
    }

# Ruta para obtener una reserva por su ID

@app.get('/reserva/{reserva_id}',status_code=status.HTTP_200_OK)
async def get_reserva(reserva_id: int):
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Verificar si la reserva existe
    c.execute("SELECT * FROM reservas WHERE reserva_id = ?", (reserva_id,))
    reserva = c.fetchone()

    conn.close()

    if reserva:
        return {
                                                      
                        
                "id": reserva[0],  # reserva_id
                "cancha_id": reserva[1],
                "usuario_id": reserva[2],
                "horario_id": reserva[3],
                "descripcion": reserva[4],
                "num_personas": reserva[5],
              
                               
                              
        }
    else:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

    
# Ruta para obtener la lista de reservas
@app.get("/reservas",status_code=status.HTTP_200_OK)
async def get_reservas():
    conn = sqlite3.connect(db)
    c = conn.cursor()
    
	# Ejecutar la consulta para obtener todas las reservas
    c.execute("SELECT reserva_id, cancha_id, usuario_id, horario_id, descripcion, num_personas FROM reservas")
    rows = c.fetchall()
    conn.close()

    # Crear una lista de diccionarios con los datos de cada reserva
    reservas_list = [{"reserva_id": row[0], "cancha_id": row[1],"usuario_id": row[2],"horario_id": row[3],"descripcion": row[4],"num_personas": row[5]} for row in rows]
    
	 # Devolver la lista de recordatorios con un codigo de estado 200 y estructura personalizada
    return JSONResponse(reservas_list)
   
# Ruta para modificar una reserva existente
@app.put("/reserva/{reserva_id}",status_code=status.HTTP_200_OK)
def update_reserva(reserva_id: int, reserva: Reserva,response:Response):
    conn = sqlite3.connect(db)
    c = conn.cursor()

    # Verificar si la reserva existe
    c.execute("SELECT * FROM reservas WHERE reserva_id = ?", (reserva_id,))
    existing_reserva = c.fetchone()
    
    if existing_reserva:
    # Validar que cancha_id sea un entero mayor a 0
        if not isinstance(reserva.cancha_id, int) or reserva.cancha_id <= 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
            "detail":"cancha",
            "msg": "debe seleccionar una cancha valida"
        }
            
         # Validar que usuario_id sea un entero mayor a 0
        elif not isinstance(reserva.usuario_id, int) or reserva.usuario_id <= 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
            "detail":"usuario",
            "msg": "debe seleccionar un usuario valida"
        }          
        
    
    # Validar que horario_id sea un entero mayor a 0
        elif not isinstance(reserva.horario_id, int) or reserva.horario_id <= 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
            "detail":"horario",
            "msg": "debe seleccionar un horario valido"
        }      
    
    # Validar que descripcion no este vacia
        elif not reserva.descripcion.strip():  # Validamos que descripcion no este vacia
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
            "detail":"descripcion",
            "msg": "el campo 'descripcion' no debe estar vacio"
        }      
    
    # Validar que num_personas sea un entero mayor a 0
        elif not isinstance(reserva.num_personas, int) or reserva.num_personas <= 0:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {
            "detail":"jugadores",
            "msg": "debe haber al menos 1 jugador"
        } 

    if existing_reserva:
        # Actualizar la reserva
        c.execute('''
                  UPDATE reservas
                  SET cancha_id = ?, usuario_id = ?, horario_id = ?, descripcion = ?, num_personas = ?
                  WHERE reserva_id = ?
                  ''', (reserva.cancha_id, reserva.usuario_id, reserva.horario_id, reserva.descripcion, reserva.num_personas, reserva_id))
        conn.commit()
        conn.close()
        

     # Crear la respuesta con los detalles de los campos actualizados
        return {
                "reserva_id": reserva_id,
                "cancha_id": reserva.cancha_id,
                "usuario_id": reserva.usuario_id,
                "horario_id": reserva.horario_id,
                "descripcion": reserva.descripcion,
                "num_personas": reserva.num_personas
        }
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="Reserva no encontrada")

# Ruta para eliminar una reserva por ID
@app.delete("/reserva/{reserva_id}",status_code=status.HTTP_200_OK)
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
  # Crear la respuesta con los detalles de la reserva eliminada
        return {     
            "reserva_id": reserva_id,
            "cancha_id": existing_reserva[1],
            "usuario_id": existing_reserva[2],
            "horario_id": existing_reserva[3],
            "descripcion": existing_reserva[4],
            "num_personas": existing_reserva[5]
            }
    else:
        conn.close()
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    

#llamada a api externa
PREFIX = "https://745c-201-216-219-24.ngrok-free.app"
HORARIOS_API_URL = "/api/horarios"
CANCHAS_API_URL = "/api/canchas"
USUARIOS_API_URL = "/api/usuarios"

@app.get("/horariosreservas")
async def get_horario_reserva(horario_id: int = Query(None, description="ID de horario a filtrar")):
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    async with httpx.AsyncClient() as client:
        # Fetching the external data
        full_route = "{}{}".format(PREFIX, HORARIOS_API_URL)
        print(full_route)
        horarios_response = await client.get(full_route)
        if horarios_response.status_code == 200:
            horarios = horarios_response.json()
        else:
            print("Error: {horarios_response.status_code}")
            raise HTTPException(status_code=404)
        
        full_route = "{}{}".format(PREFIX, CANCHAS_API_URL)
        print(full_route)
        canchas_response = await client.get(full_route)
        if canchas_response.status_code == 200:
            canchas = canchas_response.json()
        else:
            print("Error: {canchas_response.status_code}")
            raise HTTPException(status_code=404)
        
        full_route = "{}{}".format(PREFIX, USUARIOS_API_URL)
        print(full_route)      
        usuarios_response = await client.get(full_route, headers=headers)
                                            
                                          
        if usuarios_response.status_code == 200:
            usuarios = usuarios_response.json()
        else:
            print("Error: {usuarios_response.status_code}")
            raise HTTPException(status_code=404)
                                                                                                                                                                                                                                                                                                                                                                                 
        

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
    usuario_map = {usuario['id']: { 'usuario_id': usuario['id'],'nombre': usuario['nombre'], 'apellido': usuario['apellido']} for usuario in usuarios}

    # Combine the data
    horarioreserva_array = []

    for horario in horarios:
        
        if horario_id is not None and horario['horario_id'] != horario_id:
            continue
        
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
        
    if horario_id is not None and not horarioreserva_array:
        raise HTTPException(status_code=404, detail="Horario no encontrado")

    return JSONResponse(content=horarioreserva_array)




if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181)