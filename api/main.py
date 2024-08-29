# from flask import Flask, request, jsonify
import sys
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import List

version = f"{sys.version_info.major}.{sys.version_info.minor}"

app = FastAPI()


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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8181)
