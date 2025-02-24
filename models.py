from db import db
from flask_login import UserMixin
from sqlalchemy import PickleType
from sqlalchemy.orm import relationship


# Modelo User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    affiliate_number = db.Column(db.String(50), nullable=True)
    health_insurance = db.Column(db.String(100), nullable=True)  # Campo adicional
    is_admin = db.Column(db.Boolean, default=False)  # Administrador o paciente

    # Relación con citas (un usuario puede tener muchas citas)
    appointments = relationship("Appointment", back_populates="user")


# Modelo Dentist
class Dentist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.String(100), nullable=False)
    availability = db.Column(PickleType, nullable=False)

    # Relación con citas (un dentista puede tener muchas citas)
    appointments = relationship("Appointment", back_populates="dentist")


# Modelo Appointment
class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)  # Referencia al modelo User
    dentist_id = db.Column(db.Integer, db.ForeignKey("dentist.id"), nullable=False)  # Referencia al modelo Dentist
    date = db.Column(db.String(10), nullable=False)
    time = db.Column(db.String(5), nullable=False)

    # Relación con el modelo User (Paciente)
    user = relationship("User", back_populates="appointments")

    # Relación con el modelo Dentist
    dentist = relationship("Dentist", back_populates="appointments")
