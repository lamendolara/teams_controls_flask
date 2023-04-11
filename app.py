from models import *
import os
from datetime import datetime
import requests as requests
from flask import Flask, render_template, redirect, url_for, request
from flask_wtf import FlaskForm
from sqlalchemy import func, engine
from sqlalchemy.orm import sessionmaker
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import matplotlib.pyplot as plt


file_path = os.path.abspath(os.getcwd()) + r"\database\team_controls.db"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Orestrepo'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + file_path

Session = sessionmaker(bind=engine)
session = Session(expire_on_commit=False)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Model): #CLASE  PARA CREAR USUARIOS
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(20), unique=True)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __repr__(self):
        return '<User %r>' % self.username


class RegisterForm(FlaskForm): #FORMULARIO DE REGISTRO USUARIOS
    username = StringField('Usuario', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Contraseña', validators=[InputRequired(), Length(min=8, max=20)])
    email = StringField('E-mail', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    submit = SubmitField('Registrarse')


class LoginForm(FlaskForm): #FORMULARIO DE LOG IN USUARIOS
    username = StringField('Usuario', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('Contraseña', validators=[InputRequired(), Length(min=8, max=20)])
    remember_me = BooleanField('Recuérdame')
    submit = SubmitField('Ingresar')


with app.app_context(): #CREA EL CONTEXTO DE LA APP AL INICIARSE Y LAS TABLAS NUEVAS. SE IMPRIMEN.
    db.create_all()
    db.session.commit()
    users = User.query.all()
    db.session.close()
    print(users)


@app.route("/") #HOME DE LA WEB
def index():
    return render_template("index.html")


@app.route("/signup/", methods=['GET', 'POST'])
def signup():
    """Método para registro de usuarios de la app mediante formulario"""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    form = RegisterForm()
    if request.method == "POST":
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            print("User query: ", user)
            print("username form data: ", form.username.data)
            email = User.query.filter_by(email=form.email.data).first()
            print("email query: ", email)
            print("email Form Data:", form.email.data)
            if user is None:
                hashed_password = generate_password_hash(form.password.data, method='sha256')
                new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
                db.session.add(new_user)
                db.session.commit()
                db.session.close()
                response = requests.post("http://127.0.0.1:5000/signup/")
                print("Response.status_code= ", response.status_code)
                if response.status_code == 200:
                    alertas["type"] = "success"
                    alertas["mensaje"] = "El usuario se creó con éxito!."
                    # return redirect(url_for("index")
            else:
                alertas["type"] = "danger"
                alertas["mensaje"] = "No se pudo crear un usuario nuevo, vuelva a intentarlo!"

    return render_template("signup.html", form=form, alertas=alertas)


@app.route("/login", methods=['GET', 'POST'])
def login():
    """Método para logeo de usuarios registrados en la app mediante formulario"""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember_me.data)
                alertas["type"] = "success"
                alertas["mensaje"] = "Bienvenido!"
                return redirect(url_for('sesion'))
            else:
                alertas["type"] = "danger"
                alertas["mensaje"] = "Usuario o contraseña incorrecta, vuelva a intentarlo!"
        else:
            alertas["type"] = "danger"
            alertas["mensaje"] = "Usuario o contraseña incorrecta, vuelva a intentarlo!"

        # return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template("login.html", form=form, alertas=alertas)


@app.route("/logout")
@login_required
def logout():
    """Método para cerrar la sesion de usuario"""
    logout_user()
    return redirect(url_for('index'))


@login_manager.user_loader
def load_user(user_id):
    """Carga el usuario loggeado en la app"""
    return User.query.get(int(user_id))


@app.route("/sesion")
@login_required
def sesion():
    """Método para el PANEL DE GESTION JUGADORES muestra los jugadores cargados y las acciones sobre ellos.
    Se accede a los sub menus 'crear entrenamiento' y 'reporte entrenamiento"""
    todos_los_jugadores = db.session.query(Jugadores).order_by(
        Jugadores.apellidos).all()  # Consultamos y almacenamos todas las tareas ordenadas por fecha ascendente
    # Ahora en la variable todas_las_tareas se tienen almacenadas todas las tareas en una lista de objetos.
    # #Vamos a entregar esta variable al template index.html
    total_tg = db.session.query(Jugadores).count()  # TOTAL JUGADORES#
    todos_los_porteros = db.session.query(Jugadores).filter_by(posicion="Portero").count()  # TOTAL PORTEROS#
    todos_los_defensores = db.session.query(Jugadores).filter_by(posicion="Defensor").count()  # TOTAL DEFENSORES#
    todos_los_medios = db.session.query(Jugadores).filter_by(posicion="Mediocampista").count()  # TOTAL MEDIOCAMPISTAS#
    todos_los_delanteros = db.session.query(Jugadores).filter_by(posicion="Delantero").count()  # TOTAL DELANTEROS#
    return render_template("sesion.html", todos_los_jugadores=todos_los_jugadores,
                           total_tg=total_tg, todos_los_porteros=todos_los_porteros,
                           todos_los_defensores=todos_los_defensores, todos_los_medios=todos_los_medios,
                           todos_los_delanteros=todos_los_delanteros)
    # Se carga el template index.html


@app.route("/correccion/<id>")
def correccion(id):
    """Método PANEL DE GESTION JUGADORES queda marcado el jugador con corrección pendiente"""
    jugador = db.session.query(Jugadores).filter_by(id=int(id)).first()  # Se obtiene la tarea que se busca
    jugador.correccion = not jugador.correccion  # Guardamos en la variable booleana de la tarea, su contrario
    db.session.commit()  # Ejecutar la operación pendiente de la base de datos
    db.session.close()
    return redirect(url_for("sesion"))  # Esto nos redirecciona a la función home()


@app.route("/felicitar/<id>")
def felicitar(id):
    """Método PANEL DE GESTION JUGADORES queda marcado el jugador para animar o felicitar pendiente"""
    jugador = db.session.query(Jugadores).filter_by(id=int(id)).first()  # Se obtiene la tarea que se busca
    jugador.animar = not jugador.animar  # Guardamos en la variable booleana de la tarea, su contrario
    db.session.commit()  # Ejecutar la operación pendiente de la base de datos
    db.session.close()
    return redirect(url_for("sesion"))  # Esto nos redirecciona a la función home()


@app.route("/no-disponible/<id>")
def no_apto(id):
    """Método PANEL DE GESTION JUGADORES queda marcado el jugador no disponible por alguna razón"""
    jugador = db.session.query(Jugadores).filter_by(id=int(id)).first()  # Se obtiene la tarea que se busca
    jugador.no_disponible = not jugador.no_disponible  # Guardamos en la variable booleana de la tarea, su contrario
    db.session.commit()  # Ejecutar la operación pendiente de la base de datos
    db.session.close()
    return redirect(url_for("sesion"))  # Esto nos redirecciona a la función home()


@app.route("/altas", methods=["POST", "GET"])
def altas():
    """Método para dar de alta jugadores en APP"""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    todos_los_jugadores = db.session.query(Jugadores).order_by(
        Jugadores.apellidos).all()  # Consultamos y almacenamos todas las tareas ordenadas por fecha ascendente
    total_tg = db.session.query(Jugadores).count()  # TOTAL JUGADORES#
    todos_los_porteros = db.session.query(Jugadores).filter_by(posicion="Portero").count()  # TOTAL PORTEROS#
    todos_los_defensores = db.session.query(Jugadores).filter_by(posicion="Defensor").count()  # TOTAL DEFENSORES#
    todos_los_medios = db.session.query(Jugadores).filter_by(posicion="Mediocampista").count()  # TOTAL MEDIOCAMPISTAS#
    todos_los_delanteros = db.session.query(Jugadores).filter_by(posicion="Delantero").count()  # TOTAL DELANTEROS#
    if request.method == "POST":
        jugador = Jugadores(nombres=request.form.get("nombre").upper(),
                            apellidos=request.form.get("apellido").upper(),
                            posicion=request.form.get("posicion"),
                            dorsal=request.form.get("dorsal"))
        db.session.add(jugador)  # Añadir el objeto de Tarea a la base de datos
        db.session.commit()  # Ejecutar la operación pendiente de la base de datos
        db.session.close()
        response = requests.post("http://127.0.0.1:5000/altas")
        print("Response.status_code= ", response.status_code)
        if response.status_code == 500:
            alertas["type"] = "success"
            alertas["mensaje"] = "El jugador se creó con éxito"
            todos_los_jugadores = db.session.query(Jugadores).order_by(
                Jugadores.apellidos).all()  # Consultamos y almacenamos todas las tareas ordenadas por fecha ascendente
            total_tg = db.session.query(Jugadores).count()  # TOTAL JUGADORES#
            todos_los_porteros = db.session.query(Jugadores).filter_by(posicion="Portero").count()  # TOTAL PORTEROS#
            todos_los_defensores = db.session.query(Jugadores).filter_by(
                posicion="Defensor").count()  # TOTAL DEFENSORES#
            todos_los_medios = db.session.query(Jugadores).filter_by(
                posicion="Mediocampista").count()  # TOTAL MEDIOCAMPISTAS#
            todos_los_delanteros = db.session.query(Jugadores).filter_by(
                posicion="Delantero").count()  # TOTAL DELANTEROS#
            return render_template("altas.html", todos_los_jugadores=todos_los_jugadores,
                                   total_tg=total_tg, todos_los_porteros=todos_los_porteros,
                                   todos_los_defensores=todos_los_defensores, todos_los_medios=todos_los_medios,
                                   todos_los_delanteros=todos_los_delanteros, alertas=alertas)
        else:
            alertas["type"] = "danger"
            alertas["mensaje"] = "El jugador no se pudo crear, vuelva a intentarlo"
            return render_template("altas.html", todos_los_jugadores=todos_los_jugadores,
                                   total_tg=total_tg, todos_los_porteros=todos_los_porteros,
                                   todos_los_defensores=todos_los_defensores, todos_los_medios=todos_los_medios,
                                   todos_los_delanteros=todos_los_delanteros, alertas=alertas)

    return render_template("altas.html", todos_los_jugadores=todos_los_jugadores,
                           total_tg=total_tg, todos_los_porteros=todos_los_porteros,
                           todos_los_defensores=todos_los_defensores, todos_los_medios=todos_los_medios,
                           todos_los_delanteros=todos_los_delanteros, alertas=alertas)


@app.route("/editar-jugador/<id>", methods=["POST", "GET"])
def editar(id):
    """Método para editar jugadores dados de alta en APP"""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    jugador = db.session.query(Jugadores).filter_by(id=int(id)).first()
    if request.method == "POST":
        jugador.nombres = request.form["nombre"].upper()
        jugador.apellidos = request.form["apellido"].upper()
        jugador.dorsal = request.form["dorsal"]
        jugador.posicion = request.form["posicion"]
        db.session.query(Jugadores).filter(Jugadores.id == id).update(
            {
                Jugadores.nombres: jugador.nombres,
                Jugadores.apellidos: jugador.apellidos,
                Jugadores.dorsal: jugador.dorsal,
                Jugadores.posicion: jugador.posicion
            }
        )
        db.session.commit()
        response = requests.post("http://127.0.0.1:5000/editar-jugador")
        print("Response.status_code= ", response.status_code)
        if response.status_code == 404:
            alertas["type"] = "success"
            alertas["mensaje"] = "El jugador se editó con éxito."
            return render_template("editar-jugador.html", jugador=jugador, alertas=alertas)
        else:
            alertas["type"] = "danger"
            alertas["mensaje"] = "El jugador no se pudo editar, intente nuevamente."
            return render_template("editar-jugador.html", jugador=jugador, alertas=alertas)
    return render_template("editar-jugador.html", jugador=jugador, alertas=alertas)


@app.route("/eliminar-jugador/<id>")
def eliminar(id):
    """Método para eliminar jugadores dados de alta en APP"""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    db.session.query(Jugadores).filter_by(id=int(id)).delete()
    db.session.commit()
    db.session.close()
    response = requests.post("http://127.0.0.1:5000/eliminar-jugador")
    print("Response.status_code= ", response.status_code)
    if response.status_code == 404:
        alertas["type"] = "success"
        alertas["mensaje"] = "El jugador se eliminó con éxito."
        todos_los_jugadores = db.session.query(Jugadores).order_by(
            Jugadores.apellidos).all()  # Consultamos y almacenamos todas las tareas ordenadas por fecha ascendente
        # Ahora en la variable todas_las_tareas se tienen almacenadas todas las tareas en una lista de objetos.
        # #Vamos a entregar esta variable al template index.html
        total_tg = db.session.query(Jugadores).count()  # TOTAL JUGADORES#
        todos_los_porteros = db.session.query(Jugadores).filter_by(posicion="Portero").count()  # TOTAL PORTEROS#
        todos_los_defensores = db.session.query(Jugadores).filter_by(posicion="Defensor").count()  # TOTAL DEFENSORES#
        todos_los_medios = db.session.query(Jugadores).filter_by(
            posicion="Mediocampista").count()  # TOTAL MEDIOCAMPISTAS#
        todos_los_delanteros = db.session.query(Jugadores).filter_by(posicion="Delantero").count()  # TOTAL DELANTEROS#
        return render_template("altas.html", todos_los_jugadores=todos_los_jugadores,
                               total_tg=total_tg, todos_los_porteros=todos_los_porteros,
                               todos_los_defensores=todos_los_defensores, todos_los_medios=todos_los_medios,
                               todos_los_delanteros=todos_los_delanteros, alertas=alertas)
    else:
        alertas["type"] = "danger"
        alertas["mensaje"] = "El jugador no se pudo eliminar, vuelva a intentarlo."
        todos_los_jugadores = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
        total_tg = db.session.query(Jugadores).count()  # TOTAL JUGADORES#
        todos_los_porteros = db.session.query(Jugadores).filter_by(posicion="Portero").count()  # TOTAL PORTEROS#
        todos_los_defensores = db.session.query(Jugadores).filter_by(posicion="Defensor").count()  # TOTAL DEFENSORES#
        todos_los_medios = db.session.query(Jugadores).filter_by(
            posicion="Mediocampista").count()  # TOTAL MEDIOCAMPISTAS#
        todos_los_delanteros = db.session.query(Jugadores).filter_by(posicion="Delantero").count()  # TOTAL DELANTEROS#
        return render_template("altas.html", todos_los_jugadores=todos_los_jugadores,
                               total_tg=total_tg, todos_los_porteros=todos_los_porteros,
                               todos_los_defensores=todos_los_defensores, todos_los_medios=todos_los_medios,
                               todos_los_delanteros=todos_los_delanteros, alertas=alertas)


@app.route("/entrenamiento", methods=["POST", "GET"])
def entrenamiento():
    """Método para dar de alta sesiones de entrenamientos y tomar asistencia"""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
    todos_los_entrenamientos = db.session.query(Entrenamientos).order_by(Entrenamientos.fecha).all()
    for sesion in todos_los_entrenamientos:
        sesion.fecha_editada = datetime.strptime(sesion.fecha, "%Y-%m-%d")
        sesion.fecha_editada = sesion.fecha_editada.strftime("%d-%m-%Y")
    if request.method == "POST":
        sesion = Entrenamientos(fecha=request.form.get("fecha"), tipo=request.form.get("tipo").upper(),
                                responsable=request.form.get("responsable").upper(),
                                asistieron=len(request.form.getlist("asistentes")))
        jugadores_asistentes = request.form.getlist("asistentes")
        cant_asist = len(jugadores_asistentes)
        print("Cantidad de asistentes: ", cant_asist)
        print("Variable jugadores_asistentes:")
        for j in jugadores_asistentes:
            print(j)
        db.session.add(sesion)
        db.session.commit()  # Ejecutar la operación pendiente de la base de datos
        sesion_id = db.session.query(Entrenamientos).order_by(Entrenamientos.id.desc()).first()
        sesion_numero = sesion_id.id
        print("Sesion de entrenamiento N°", sesion_numero)
        for j in jugadores_asistentes:
            asistentes = Asistencia()
            asistentes.id_jugador = j
            asistentes.id_sesion = sesion_numero
            db.session.add(asistentes)
            db.session.commit()  # Ejecutar la operación pendiente de la base de datos
            # total_asistencia_sesion = db.session.query(Asistencia).order_by(Asistencia.id_sesion.desc()).first()
            db.session.close()
        response = requests.post("http://127.0.0.1:5000/entrenamiento")
        print("Response.status_code= ", response.status_code)
        if response.status_code == 500:
            alertas["type"] = "success"
            alertas["mensaje"] = "La sesión de entrenamiento se creó con éxito"
            asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
            todos_los_entrenamientos = db.session.query(Entrenamientos).order_by(Entrenamientos.fecha).all()
            for sesion in todos_los_entrenamientos:
                sesion.fecha_editada = datetime.strptime(sesion.fecha, "%Y-%m-%d")
                sesion.fecha_editada = sesion.fecha_editada.strftime("%d-%m-%Y")
            return render_template("entrenamiento.html", todos_los_entrenamientos=todos_los_entrenamientos,
                                   asist=asist, alertas=alertas)  # Se carga el template de los entrenamientos.
        else:
            alertas["type"] = "danger"
            alertas["mensaje"] = "La sesión de entrenamiento no se pudo crear, vuelva a intentarlo."
            return render_template("entrenamiento.html", todos_los_entrenamientos=todos_los_entrenamientos,
                                   asist=asist, alertas=alertas)  # Se carga el template de los entrenamientos.

    return render_template("entrenamiento.html", todos_los_entrenamientos=todos_los_entrenamientos,
                           asist=asist, alertas=alertas)  # Se carga el template de los entrenamientos.


@app.route("/ver-sesion/<id>", methods=["GET"])
def ver_sesion(id):
    """Método para ver una sesión de entrenamiento creada con los jugadores asistentes"""
    entrenamiento = db.session.query(Entrenamientos).filter_by(id=int(id)).first()
    jugadores_entrenamiento = db.session.query(Jugadores).join(Asistencia, Jugadores.id == Asistencia.id_jugador) \
        .filter_by(id_sesion=int(id)).all()
    db.session.close()
    return render_template("ver-sesion.html", entrenamiento=entrenamiento,
                           jugadores_entrenamiento=jugadores_entrenamiento)


@app.route("/editar-sesion/<id>", methods=["POST", "GET"])
def editar_sesion(id):
    """Método para editar una sesión de entrenamiento creada con los jugadores asistentes."""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
    sesion = db.session.query(Entrenamientos).filter_by(id=int(id)).first()
    db.session.query(Asistencia).filter_by(id_sesion=int(id)).delete()
    if request.method == "POST":
        sesion.fecha = request.form["fecha"]
        sesion.tipo = request.form["tipo"].upper()
        sesion.responsable = request.form["responsable"]
        sesion.asistieron = len(request.form.getlist("asistentes"))
        db.session.query(Entrenamientos).filter(Entrenamientos.id == id).update(
            {
                Entrenamientos.fecha: sesion.fecha,
                Entrenamientos.tipo: sesion.tipo,
                Entrenamientos.responsable: sesion.responsable,
                Entrenamientos.asistieron: sesion.asistieron
            }
        )
        jugadores_asistentes = request.form.getlist("asistentes")
        db.session.commit()
        for j in jugadores_asistentes:
            asistentes = Asistencia()
            asistentes.id_jugador = j
            asistentes.id_sesion = sesion.id
            db.session.add(asistentes)
            db.session.commit()  # Ejecutar la operación pendiente de la base de datos
            print("Jugadores asistentes editados:", j)
        response = requests.post("http://127.0.0.1:5000/editar-sesion")
        print("Response.status_code= ", response.status_code)
        if response.status_code == 404:
            alertas["type"] = "success"
            alertas["mensaje"] = "La sesión de entrenamiento se editó con éxito."
            return render_template("editar-sesion.html", asist=asist, sesion=sesion, alertas=alertas)
        else:
            alertas["type"] = "danger"
            alertas["mensaje"] = "La sesión de entrenamiento no se pudo editar, intente nuevamente."
            return render_template("editar-sesion.html", asist=asist, sesion=sesion, alertas=alertas)
    return render_template("editar-sesion.html", asist=asist, sesion=sesion, alertas=alertas)


@app.route("/eliminar-sesion/<id>")
def eliminar_sesion(id):
    """Método para dar eliminar una sesión de entrenamiento creada con los jugadores asistentes"""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    db.session.query(Entrenamientos).filter_by(id=int(id)).delete()
    db.session.query(Asistencia).filter_by(id_sesion=int(id)).delete()
    db.session.commit()
    db.session.close()
    response = requests.post("http://127.0.0.1:5000/eliminar-sesion")
    print("Response.status_code= ", response.status_code)
    if response.status_code == 404:
        alertas["type"] = "success"
        alertas["mensaje"] = "La sesión de entrenamiento se elimino con éxito."
        asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
        todos_los_entrenamientos = db.session.query(Entrenamientos).order_by(Entrenamientos.fecha).all()
        for sesion in todos_los_entrenamientos:
            sesion.fecha_editada = datetime.strptime(sesion.fecha, "%Y-%m-%d")
            sesion.fecha_editada = sesion.fecha_editada.strftime("%d-%m-%Y")
        return render_template("entrenamiento.html", todos_los_entrenamientos=todos_los_entrenamientos,
                               asist=asist, alertas=alertas)  # Se carga el template de los entrenamientos.
    else:
        alertas["type"] = "danger"
        alertas["mensaje"] = "La sesión de entrenamiento no se pudo eliminar"
        asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
        todos_los_entrenamientos = db.session.query(Entrenamientos).order_by(Entrenamientos.fecha).all()
        for sesion in todos_los_entrenamientos:
            sesion.fecha_editada = datetime.strptime(sesion.fecha, "%Y-%m-%d")
            sesion.fecha_editada = sesion.fecha_editada.strftime("%d-%m-%Y")
        return render_template("entrenamiento.html", todos_los_entrenamientos=todos_los_entrenamientos,
                               asist=asist, alertas=alertas)  # Se carga el template de los entrenamientos.


@app.route("/reporte-entrenamiento", methods=["GET"])
def reporte_entrenamiento():
    """Esta función permite visualizar un reporte de las asistencias de los jugadores (contiene también gráficos)."""
    entrenamiento = db.session.query(Entrenamientos).count()
    print("Total de sesiones de entrenamiento: ", entrenamiento)
    # Query que arroja el total de asistencias por jugador y el porcentaje.
    total_asistencia = db.session.query(Jugadores.apellidos, Jugadores.nombres, func.count(Asistencia.id_jugador),
                                        func.count(Asistencia.id_jugador) * 100 / entrenamiento) \
        .join(Asistencia, Jugadores.id == Asistencia.id_jugador) \
        .group_by(Asistencia.id_jugador).order_by(func.count(Asistencia.id_jugador).desc()).all()
    print(total_asistencia)
    db.session.close()

    # GRÁFICOS MATPLOTLIB: JUGADORES POR PUESTO
    fig, ax = plt.subplots()

    porteros = db.session.query(Jugadores.posicion).filter_by(posicion="Portero").count()
    defensores = db.session.query(Jugadores.posicion).filter_by(posicion="Defensor").count()
    mediocampistas = db.session.query(Jugadores.posicion).filter_by(posicion="Mediocampista").count()
    delanteros = db.session.query(Jugadores.posicion).filter_by(posicion="Delantero").count()
    lista_totales = [porteros, defensores, mediocampistas, delanteros]
    for puesto in lista_totales:
        print(puesto)

    plt.style.use('dark_background')
    ax.set_title("JUGADORES POR POSICIÓN")
    y = lista_totales
    mylabels = ["Porteros", "Defensores", "Mediocampistas", "Delanteros"]

    plt.pie(y, labels=mylabels, autopct="%1.1f %%", shadow=True)
    plt.savefig(".\static\images\jugadores_por_posicion.jpg",
                bbox_inches="tight")
    #plt.show()
    #plt.close()

    # GRÁFICOS MATPLOTLIB: ASISTENCIA POR SESIÓN DE ENTRENAMIENTO

    plt.style.use('dark_background')
    fig, ax = plt.subplots()

    x_query = []

    y_query = []

    sesiones = db.session.query(Entrenamientos.id).all()
    print("Entrenamientos Id:")
    for e in sesiones:
        e = str(e)
        e = e.replace("(", "")
        e = e.replace(",", "")
        e = e.replace(")", "")
        x_query.append(e)
        print(e)
    print(x_query)

    print("Entrenamientos Asistieron:")
    cantidad_asistentes = db.session.query(Entrenamientos.asistieron).order_by(Entrenamientos.id).all()
    for e in cantidad_asistentes:
        e = str(e)
        e = e.replace("(", "")
        e = e.replace(",", "")
        e = e.replace(")", "")
        y_query.append(e)
        print(e)
    print(y_query)

    x = []
    y = []

    for i in x_query:
        e = int(i)
        x.append(e)

    for i in y_query:
        e = int(i)
        y.append(e)

    ax.plot(x, y)
    ax.set_title("ASISTENCIA POR SESIÓN DE ENTRENAMIENTO")
    ax.set_ylabel("Cantidad de jugadores")
    ax.set_xlabel("Sesiones de entrenamiento")
    ax.set_xticks(x)
    #plt.grid(True)
    ax.stem(x, y)

    plt.savefig(".\static\images\jugadores_por_entrenamiento.jpg", bbox_inches="tight")
    # plt.show()
    # plt.close()

    return render_template("reporte-entrenamiento.html", entrenamiento=entrenamiento, total_asistencia=total_asistencia)


@app.route("/convocatoria")
def convocatoria():
    """Método para el PANEL DE GESTION JUGADORES muestra los jugadores cargados y las acciones sobre ellos.
    Se accede a los sub menus 'crear convocatoria' y 'reporte convocatoria"""
    todos_los_jugadores = db.session.query(Jugadores).order_by(
        Jugadores.apellidos).all()  # Consultamos y almacenamos todas las tareas ordenadas por fecha ascendente
    # Ahora en la variable todas_las_tareas se tienen almacenadas todas las tareas en una lista de objetos.
    # #Vamos a entregar esta variable al template index.html
    total_tg = db.session.query(Jugadores).count()  # TOTAL JUGADORES#
    todos_los_porteros = db.session.query(Jugadores).filter_by(posicion="Portero").count()  # TOTAL PORTEROS#
    todos_los_defensores = db.session.query(Jugadores).filter_by(posicion="Defensor").count()  # TOTAL DEFENSORES#
    todos_los_medios = db.session.query(Jugadores).filter_by(posicion="Mediocampista").count()  # TOTAL MEDIOCAMPISTAS#
    todos_los_delanteros = db.session.query(Jugadores).filter_by(posicion="Delantero").count()  # TOTAL DELANTEROS#
    return render_template("convocatoria.html", todos_los_jugadores=todos_los_jugadores,
                           total_tg=total_tg, todos_los_porteros=todos_los_porteros,
                           todos_los_defensores=todos_los_defensores, todos_los_medios=todos_los_medios,
                           todos_los_delanteros=todos_los_delanteros)


@app.route("/crear-convocatoria", methods=["POST", "GET"])
def crear_convocatoria():
    """Método para dar de alta una convocatoria a partido y registrar los jugadores seleccionados."""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
    todas_las_convocatorias = db.session.query(Convocatorias).order_by(Convocatorias.fecha).all()
    for convocatoria in todas_las_convocatorias:
        convocatoria.fecha_editada = datetime.strptime(convocatoria.fecha, "%Y-%m-%d")
        convocatoria.fecha_editada = convocatoria.fecha_editada.strftime("%d-%m-%Y")
    if request.method == "POST":
        convocatoria = Convocatorias(fecha=request.form.get("fecha"), rival=request.form.get("rival").upper(),
                                     condicion=request.form.get("condicion"),
                                     convocados=len(request.form.getlist("convocados")))
        jugadores_convocados = request.form.getlist("convocados")
        cant_convocados = len(jugadores_convocados)
        print("Cantidad de convocados: ", cant_convocados)
        print("Variable jugadores_convocados:")
        for j in jugadores_convocados:
            print(j)
        db.session.add(convocatoria)
        db.session.commit()  # Ejecutar la operación pendiente de la base de datos
        convocatoria_id = db.session.query(Convocatorias).order_by(Convocatorias.id.desc()).first()
        convocatoria_numero = convocatoria_id.id
        print("Convocatoria N°", convocatoria_numero)
        for j in jugadores_convocados:
            convocados = Jugadores_Convocados()
            convocados.id_jugador = j
            convocados.id_convocatoria = convocatoria_numero
            db.session.add(convocados)
            db.session.commit()  # Ejecutar la operación pendiente de la base de datos
            db.session.close()
        response = requests.post("http://127.0.0.1:5000/crear-convocatoria")
        print("Response.status_code= ", response.status_code)
        if response.status_code == 500:
            alertas["type"] = "success"
            alertas["mensaje"] = "La convocatoria al próximo partido fue creada con éxito"
            asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
            todas_las_convocatorias = db.session.query(Convocatorias).order_by(Convocatorias.fecha).all()
            for convocatoria in todas_las_convocatorias:
                convocatoria.fecha_editada = datetime.strptime(convocatoria.fecha, "%Y-%m-%d")
                convocatoria.fecha_editada = convocatoria.fecha_editada.strftime("%d-%m-%Y")
            return render_template("crear-convocatoria.html", todas_las_convocatorias=todas_las_convocatorias,
                                   asist=asist, alertas=alertas)  # Se carga el template de los entrenamientos.
        else:
            alertas["type"] = "danger"
            alertas["mensaje"] = "La convocatoria al próximo partido no se pudo crear."
            return render_template("crear-convocatoria.html", todas_las_convocatorias=todas_las_convocatorias,
                                   asist=asist, alertas=alertas)  # Se carga el template de los entrenamientos.

    return render_template("crear-convocatoria.html", todas_las_convocatorias=todas_las_convocatorias,
                           asist=asist, alertas=alertas)


@app.route("/ver-convocatoria/<id>", methods=["GET"])
def ver_convocatoria(id):
    """Método para ver una convocatoria a partido creada con los jugadores elegidos."""
    convocatoria = db.session.query(Convocatorias).filter_by(id=int(id)).first()
    jugadores_convocatoria = db.session.query(Jugadores).join(Jugadores_Convocados,
                                                              Jugadores.id == Jugadores_Convocados.id_jugador) \
        .filter_by(id_convocatoria=int(id)).all()
    db.session.close()
    return render_template("ver-convocatoria.html", convocatoria=convocatoria,
                           jugadores_convocatoria=jugadores_convocatoria)


@app.route("/editar-convocatoria/<id>", methods=["POST", "GET"])
def editar_convocatoria(id):
    """Método para editar convocatoria a partido."""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
    convocatoria = db.session.query(Convocatorias).filter_by(id=int(id)).first()
    db.session.query(Jugadores_Convocados).filter_by(id_convocatoria=int(id)).delete()
    if request.method == "POST":
        convocatoria.fecha = request.form["fecha"]
        convocatoria.rival = request.form["rival"].upper()
        convocatoria.condicion = request.form["condicion"]
        convocatoria.convocados = len(request.form.getlist("convocados"))

        db.session.query(Convocatorias).filter(Convocatorias.id == id).update(
            {
                Convocatorias.fecha: convocatoria.fecha,
                Convocatorias.rival: convocatoria.rival,
                Convocatorias.condicion: convocatoria.condicion,
                Convocatorias.convocados: convocatoria.convocados
            }
        )
        db.session.commit()
        jugadores_convocados = request.form.getlist("convocados")
        db.session.commit()
        for j in jugadores_convocados:
            convocados = Jugadores_Convocados()
            convocados.id_jugador = j
            convocados.id_convocatoria = convocatoria.id
            db.session.add(convocados)
            db.session.commit()  # Ejecutar la operación pendiente de la base de datos
            print("Jugadores convocados editados:", j)
        response = requests.post("http://127.0.0.1:5000/editar-sesion")
        print("Response.status_code= ", response.status_code)
        if response.status_code == 404:
            alertas["type"] = "success"
            alertas["mensaje"] = "La convocatoria para este partido se editó con éxito."
            return render_template("editar-convocatoria.html", asist=asist, convocatoria=convocatoria, alertas=alertas)
        else:
            alertas["type"] = "danger"
            alertas["mensaje"] = "La convocatoria para este partido no se pudo editar, intente nuevamente."
            return render_template("editar-convocatoria.html", asist=asist, convocatoria=convocatoria, alertas=alertas)
    return render_template("editar-convocatoria.html", asist=asist, convocatoria=convocatoria, alertas=alertas)


@app.route("/eliminar-convocatoria/<id>")
def eliminar_convocatoria(id):
    """Método para eliminar una convocatoria a partido creada con los jugadores seleccionados."""
    alertas = {
        "type": "",
        "mensaje": ""
    }
    db.session.query(Convocatorias).filter_by(id=int(id)).delete()
    db.session.query(Jugadores_Convocados).filter_by(id_convocatoria=int(id)).delete()
    db.session.commit()
    db.session.close()
    response = requests.post("http://127.0.0.1:5000/eliminar-convocatoria")
    print("Response.status_code= ", response.status_code)
    if response.status_code == 404:
        alertas["type"] = "success"
        alertas["mensaje"] = "La convocatoria se eliminó con éxito"
        asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
        todas_las_convocatorias = db.session.query(Convocatorias).order_by(Convocatorias.fecha).all()
        for convocatoria in todas_las_convocatorias:
            convocatoria.fecha_editada = datetime.strptime(convocatoria.fecha, "%Y-%m-%d")
            convocatoria.fecha_editada = convocatoria.fecha_editada.strftime("%d-%m-%Y")
        return render_template("crear-convocatoria.html", todas_las_convocatorias=todas_las_convocatorias,
                               asist=asist, alertas=alertas)  # Se carga el template de los entrenamientos.
    else:
        alertas["type"] = "danger"
        alertas["mensaje"] = "La convocatoria no se pudo eliminar, vuelva a intentarlo."
        asist = db.session.query(Jugadores).order_by(Jugadores.apellidos).all()
        todas_las_convocatorias = db.session.query(Convocatorias).order_by(Convocatorias.fecha).all()
        for convocatoria in todas_las_convocatorias:
            convocatoria.fecha_editada = datetime.strptime(convocatoria.fecha, "%Y-%m-%d")
            convocatoria.fecha_editada = convocatoria.fecha_editada.strftime("%d-%m-%Y")
        return render_template("crear-convocatoria.html", todas_las_convocatorias=todas_las_convocatorias,
                               asist=asist, alertas=alertas)  # Se carga el template de los entrenamientos.


@app.route("/reporte-convocatoria", methods=["GET"])
def reporte_convocatoria():
    """Esta función perminte visualizar un reporte de las asitencias de los jugadores (contiene gráficos también)."""
    total_convocatoria = db.session.query(Convocatorias).count()
    print("Total de convocatorias: ", total_convocatoria)
    # Query que arroja el total de convocatorias por jugador y el porcentaje.
    convocatorias_por_jugador = db.session.query(Jugadores.apellidos, Jugadores.nombres,
                                                 func.count(Jugadores_Convocados.id_jugador),
                                                 func.count(Jugadores_Convocados.id_jugador) * 100 / total_convocatoria) \
        .join(Jugadores_Convocados, Jugadores.id == Jugadores_Convocados.id_jugador) \
        .group_by(Jugadores_Convocados.id_jugador) \
        .order_by(func.count(Jugadores_Convocados.id_jugador).desc()).all()
    print(convocatorias_por_jugador)
    db.session.close()
    return render_template("reporte-convocatoria.html", total_convocatoria=total_convocatoria,
                           convocatorias_por_jugador=convocatorias_por_jugador)


if __name__ == '__main__':
    app.run(debug=True)
