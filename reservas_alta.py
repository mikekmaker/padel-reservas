from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Conectar a la base de datos y crear la tabla si no existe
def init_db():
    conn = sqlite3.connect('reservas.db')
    c = conn.cursor()
    c.execute('''
              CREATE TABLE IF NOT EXISTS reservas
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              nombre TEXT,
              fecha DATE,
              hora TIME,
              num_personas INTEGER)
              ''')
    conn.commit()
    conn.close()
  
init_db()

# Ruta para crear una nueva reserva
@app.route('/reservas', methods=['POST'])
def create_reserva():
    data = request.get_json()  # Obtenemos los datos en formato JSON.
    
    if(data):
        nombre = data['nombre']
        fecha = data['fecha']
        hora = data['hora']
        num_personas = data['num_personas']
    
        conn = sqlite3.connect('reservas.db')
        c = conn.cursor()
        c.execute("INSERT INTO reservas (nombre, fecha, hora, num_personas) VALUES (?, ?, ?, ?)",
              (nombre, fecha, hora, num_personas))
        conn.commit()
        conn.close()
    
        return jsonify({'message': 'Reserva creada con éxito'}), 201

    else :
        return jsonify({'message': 'campos vacios'}), 400

if __name__ == '__main__':
    app.run(debug=True)

