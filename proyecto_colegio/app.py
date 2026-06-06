from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Definimos basedir aquí afuera para que exista tanto en local como en Render
basedir = os.path.abspath(os.path.dirname(__file__))

# Configuración inteligente de la base de datos (Igual a la cantina)
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # Si detecta Render, usa la base de datos de internet
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
else:
    # Si estás en tu Mac, usa el archivo local de siempre
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'inventario.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modelo de la Base de Datos ampliado
class Equipo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    estado = db.Column(db.String(50), default="Disponible")  # Disponible, Prestado, En_Reparacion
    informacion = db.Column(db.String(200), default="Sin descripción")
    ubicacion = db.Column(db.String(100), default="Depósito Central")

print("La base de datos se encuentra en:", os.path.join(basedir, 'inventario.db'))

with app.app_context():
    db.create_all()

@app.route('/')
def inicio():
    lista_equipos = Equipo.query.all()
    
    # Cálculo de estadísticas en tiempo real
    stats = {
        'total': len(lista_equipos),
        'disponibles': len([e for e in lista_equipos if e.estado == 'Disponible']),
        'prestados': len([e for e in lista_equipos if e.estado == 'Prestados']),
        'reparacion': len([e for e in lista_equipos if e.estado == 'En_Reparacion'])
    }
    
    return render_template('index.html', lista=lista_equipos, stats=stats)

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
    equipo = db.session.get(Equipo, id)  # Método actualizado para SQLAlchemy moderno
    if equipo:
        # Ciclo de estados limpios sin espacios para el CSS
        estados = ["Disponible", "Prestados", "En_Reparacion"]
        indice_actual = estados.index(equipo.estado) if equipo.estado in estados else 0
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
    # Esto lee el puerto de la nube o usa el 5000 por defecto en local
    puerto = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=puerto)
