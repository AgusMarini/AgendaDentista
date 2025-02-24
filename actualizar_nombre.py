from app import app, db
from models import Dentist

with app.app_context():
    # Buscar al dentista por el nombre actual
    dentist = Dentist.query.filter_by(name="Dr. Marce").first()
    if dentist:
        # Actualizar el nombre
        dentist.name = "Dr. Marcelo Binetti"
        db.session.commit()
        print("Nombre actualizado correctamente.")
    else:
        print("No se encontró al dentista con ese nombre.")
