from app import db


class Jugadores(db.Model):
    __tablename__ = "jugadores"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombres = db.Column(db.String(200), nullable=False)
    apellidos = db.Column(db.String(200), nullable=False)
    posicion = db.Column(db.String(200), nullable=False)
    dorsal = db.Column(db.Integer)
    no_disponible = db.Column(db.Boolean, nullable=False)
    correccion = db.Column(db.Boolean, nullable=False)
    animar = db.Column(db.Boolean, nullable=False)
    entrenamiento = db.relationship("Asistencia")
    convocatoria = db.relationship("Jugadores_Convocados")

    def __init__(self, nombres, apellidos, posicion, dorsal,
                 no_disponible=False, correccion=False, animar=False):
        self.nombres = nombres
        self.apellidos = apellidos
        self.posicion = posicion
        self.dorsal = dorsal
        self.no_disponible = no_disponible
        self.correccion = correccion
        self.animar = animar

    def __repr__(self):
        return "Jugador/a {}: {} {} Posición:{} Dorsal: {}".format(self.id, self.nombres, self.apellidos, self.posicion,
                                                                   self.dorsal)

    def __str__(self):
        return "Jugador/a {}: {} {} Posición:{} Dorsal: {}".format(self.id, self.nombres, self.apellidos, self.posicion,
                                                                   self.dorsal)


class Entrenamientos(db.Model):
    __tablename__ = "entrenamientos"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha = db.Column(db.Integer)  # nullable al poner falso fuerza que el campo debe rellenarse obligatoriamente.
    tipo = db.Column(db.String(200), nullable=False)
    responsable = db.Column(db.String(200), nullable=False)
    asistieron = db.Column(db.Integer)
    asistencia = db.relationship("Asistencia")

    def __init__(self, fecha, tipo, responsable, asistieron):
        self.fecha = fecha
        self.tipo = tipo
        self.responsable = responsable
        self.asistieron = asistieron

    @property
    def __repr__(self):
        return "Entrenamiento {}:\nFecha: {}\nTipo: {}\nResponsable:{}".format(self.id, self.fecha, self.tipo,
                                                                               self.responsable)

    def __str__(self):
        return "Entrenamiento {}:\nFecha: {}\nTipo: {}\nResponsable:{}".format(self.id, self.fecha, self.tipo,
                                                                               self.responsable)


class Asistencia(db.Model):
    __tablename__ = "asistencia"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_jugador = db.Column(db.Integer, db.ForeignKey("jugadores.id"))
    id_sesion = db.Column(db.Integer, db.ForeignKey("entrenamientos.id"))


class Convocatorias(db.Model):
    __tablename__ = "convocatorias"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fecha = db.Column(db.Integer)
    rival = db.Column(db.String(200), nullable=False)
    condicion = db.Column(db.String(200), nullable=False)
    convocados = db.Column(db.Integer)
    jugadores_convocados = db.relationship("Jugadores_Convocados")

    def __init__(self, fecha, rival, condicion, convocados):
        self.fecha = fecha
        self.rival = rival
        self.condicion = condicion
        self.convocados = convocados

    @property
    def __repr__(self):
        return "Convocatoria {}:\nFecha: {}\nRival: {}\nCondición:{}".format(self.id, self.fecha, self.rival,
                                                                             self.condicion)

    def __str__(self):
        return "Convocatoria {}:\nFecha: {}\nRival: {}\nCondición:{}".format(self.id, self.fecha, self.rival,
                                                                             self.condicion)


class Jugadores_Convocados(db.Model):
    __tablename__ = "jugadores_convocados"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_jugador = db.Column(db.Integer, db.ForeignKey(
        "jugadores.id"))  # nullable al poner falso fuerza que el campo debe rellenarse obligatoriamente.
    id_convocatoria = db.Column(db.Integer, db.ForeignKey("convocatorias.id"))
