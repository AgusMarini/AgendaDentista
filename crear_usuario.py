from app import app, db
from models import User, Dentist
from werkzeug.security import generate_password_hash

with app.app_context():
    # Crear usuario administrador si no existe
    if not User.query.filter_by(email="admin@example.com").first():
        admin = User(
            email="admin@example.com",
            password=generate_password_hash("123456"),
            name="Administrador",  
            affiliate_number="00001",  
            phone="123456789",  
            is_admin=True  
        )
        db.session.add(admin)
        print("Usuario administrador creado correctamente.")
    else:
        print("El usuario administrador ya existe.")

    # Actualizar o agregar dentista Marcelo Binetti
    dentist1 = Dentist.query.filter_by(name="Dr. Marcelo Binetti").first()
    if dentist1:
        dentist1.availability = {
            "monday": ["16:00-20:00"],
            "tuesday": ["16:00-20:00"],
            "wednesday": ["08:00-12:00"],
            "thursday": ["16:00-20:00"],
            "friday": ["16:00-20:00"]
        }
        print("Horarios de Dr. Marcelo Binetti actualizados.")
    else:
        dentist1 = Dentist(
            name="Dr. Marcelo Binetti",
            photo="marce.jpg",
            availability={
                "monday": ["16:00-20:00"],
                "tuesday": ["16:00-20:00"],
                "wednesday": ["08:00-12:00"],
                "thursday": ["16:00-20:00"],
                "friday": ["16:00-20:00"]
            }
        )
        db.session.add(dentist1)
        print("Dr. Marcelo Binetti agregado.")

    # Actualizar o agregar dentista Verónica Borelli
    dentist2 = Dentist.query.filter_by(name="Dr. Verónica Borelli").first()
    if dentist2:
        dentist2.availability = {
            "monday": ["08:00-12:00"],
            "tuesday": ["08:00-12:00"],
            "wednesday": ["16:00-20:00"],
            "thursday": ["08:00-12:00"],
            "friday": ["08:00-12:00"]
        }
        print("Horarios de Dr. Verónica Borelli actualizados.")
    else:
        dentist2 = Dentist(
            name="Dr. Verónica Borelli",
            photo="veronica_borelli.jpg",
            availability={
                "monday": ["08:00-12:00"],
                "tuesday": ["08:00-12:00"],
                "wednesday": ["16:00-20:00"],
                "thursday": ["08:00-12:00"],
                "friday": ["08:00-12:00"]
            }
        )
        db.session.add(dentist2)
        print("Dr. Verónica Borelli agregado.")

    # Guardar cambios en la base de datos
    db.session.commit()
    print("Dentistas actualizados correctamente.")
