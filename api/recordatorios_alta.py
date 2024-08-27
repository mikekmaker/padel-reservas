from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

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
@app.route('/recordatorios', methods=['POST'])
def create_recordatorio():
    data = request.get_json()  # Obtenemos los datos en formato JSON
    
    if(data):
        titulo = data['titulo']
        descripcion = data['descripcion']
        fecha = data['fecha']
        hora = data['hora']

        conn = sqlite3.connect('recordatorios.db')
        c = conn.cursor()
        c.execute("INSERT INTO recordatorios (titulo, descripcion, fecha, hora) VALUES (?, ?, ?, ?)",
              (titulo, descripcion, fecha, hora))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Recordatorio creado con éxito'}), 201

    else :
        return jsonify({'message': 'campos vacios'}), 400

if __name__ == '__main__':
    app.run(debug=True)