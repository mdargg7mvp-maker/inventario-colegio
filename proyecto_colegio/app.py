from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, static_folder='.', static_url_path='')

# Definimos basedir
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuración de la base de datos
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'inventario.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la Base de Datos
class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), default="Disponible")  # Disponible, Prestado, En_Reparacion
    informacion = db.Column(db.String(200), default="Sin descripción")
    ubicacion = db.Column(db.String(100), default="Depósito Central")

with app.app_context():
    db.create_all()

@app.route('/')
def inicio():
    # Obtener término de búsqueda por ubicación desde la URL (?ubicacion_buscar=...)
    ubicacion_buscar = request.args.get('ubicacion_buscar', '').strip()

    # Filtrar si el usuario buscó una ubicación concreta
    if ubicacion_buscar:
        lista_equipos = Equipo.query.filter(Equipo.ubicacion.ilike(f'%{ubicacion_buscar}%')).all()
    else:
        lista_equipos = Equipo.query.all()

    # Cálculo de estadísticas globales sobre el total de la BD
    todos_los_equipos = Equipo.query.all()
    stats = {
        'total': len(todos_los_equipos),
        'disponibles': len([e for e in todos_los_equipos if e.estado == 'Disponible']),
        'prestados': len([e for e in todos_los_equipos if e.estado in ['Prestado', 'Prestados']]),
        'reparacion': len([e for e in todos_los_equipos if e.estado == 'En_Reparacion'])
    }

    return render_template(
        'index.html', 
        lista=lista_equipos, 
        stats=stats, 
        ubicacion_buscar=ubicacion_buscar
    )

@app.route('/agregar', methods=['POST'])
def agregar():
    nombre = request.form.get('nombre')
    info = request.form.get('informacion')
    ubicacion = request.form.get('ubicacion')

    if nombre:
        nuevo = Equipo(
            nombre=nombre, 
            informacion=info, 
            ubicacion=ubicacion if ubicacion else "Depósito Central"
        )
        db.session.add(nuevo)
        db.session.commit()
    return redirect(url_for('inicio'))

@app.route('/cambiar_estado/<int:id>')
def cambiar_estado(id):
    equipo = db.session.get(Equipo, id)
    if equipo:
        estados = ["Disponible", "Prestado", "En_Reparacion"]
        
        # Manejo de compatibilidad con datos previos
        estado_actual = "Prestado" if equipo.estado == "Prestados" else equipo.estado
        indice_actual = estados.index(estado_actual) if estado_actual in estados else 0
        
        proximo_indice = (indice_actual + 1) % len(estados)
        equipo.estado = estados[proximo_indice]
        db.session.commit()
    return redirect(url_for('inicio'))

@app.route('/eliminar/<int:id>')
def eliminar(id):
    equipo = db.session.get(Equipo, id)
    if equipo:
        db.session.delete(equipo)
        db.session.commit()
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    puerto = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=puerto)
