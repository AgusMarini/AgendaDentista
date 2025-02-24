import os
import re
import smtplib
from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from models import User, Dentist, Appointment
from itsdangerous import URLSafeTimedSerializer
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for
from datetime import datetime
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash
from threading import Thread
from flask import Response
import pandas as pd
from xhtml2pdf import pisa
import io
from models import User, Appointment, Dentist
from flask_apscheduler import APScheduler
# Cargar variables de entorno desde .env
load_dotenv()

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "dentistafunes@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "qkizextbdddhbsjv")

# Crear la aplicación Flask
app = Flask(__name__)
app.config["SECRET_KEY"] = "una_clave_secreta_segura"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar la base de datos con la aplicación Flask
db.init_app(app)

# Inicializar LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Inicializar Scheduler
scheduler = APScheduler()

# Configuración del correo (GMAIL SMTP)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "dentistafunes@gmail.com"
EMAIL_PASSWORD = "qkizextbdddhbsjv"
# Probar conexión SMTP al iniciar la aplicación
try:
    server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    server.starttls()
    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
    print("✅ Conexión SMTP exitosa. Puedes enviar correos.")
    server.quit()
except Exception as e:
    print(f"❌ Error al conectar con el servidor SMTP: {e}")


def create_admin_user():
    with app.app_context():
        admin = User.query.filter_by(email="dentistafunes@gmail.com").first()
        if not admin:
            print("🔹 Creando usuario administrador...")
            admin = User(
                email="dentistafunes@gmail.com",
                password=generate_password_hash("admin123", method='pbkdf2:sha256'),
                name="Administrador",
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Administrador creado con éxito.")
        else:
            print("⚠️ El usuario administrador ya existe.")

# Ejecutar la creación del admin al iniciar la app
with app.app_context():
    db.create_all()
    create_admin_user()
# Funciones de token
serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])

def generate_reset_token(email):
    """Genera un token seguro para recuperación de contraseña."""
    return serializer.dumps(email, salt="password-reset-salt")
def enviar_correo_en_segundo_plano(destinatario, paciente_nombre, dentista_nombre, fecha, hora):
    """Ejecuta el envío de correo en un hilo separado."""
    thread = Thread(target=enviar_correo_turno, args=(destinatario, paciente_nombre, dentista_nombre, fecha, hora))
    thread.start()

def enviar_correo_cancelacion(destinatario, paciente_nombre, dentista_nombre, fecha, hora):
    """Envía un correo al paciente notificando la cancelación de su turno."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = destinatario
    msg['Subject'] = "Cancelación de Turno - Clínica Dental"
    msg['Reply-To'] = EMAIL_ADDRESS  # Permite respuestas
    msg['Return-Path'] = EMAIL_ADDRESS  # Evita detección como spam

    # Formato del correo en HTML
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; text-align: center;">
        <h2 style="color: #c0392b;">Cancelación de Turno</h2>
        <p>Hola <strong>{paciente_nombre}</strong>,</p>
        <p>Tu turno con el <strong>{dentista_nombre}</strong> ha sido <strong style="color: red;">cancelado</strong>.</p>
        <p><strong>Fecha:</strong> {fecha}</p>
        <p><strong>Hora:</strong> {hora}</p>
        <hr>
        <p style="font-size: 12px; color: #777;">Si crees que esto es un error, por favor comunícate con la clínica.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"✅ Correo de cancelación enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error al enviar el correo de cancelación: {e}")

def enviar_correo_turno(destinatario, paciente_nombre, dentista_nombre, fecha, hora):
    """Envía un correo con la confirmación del turno al paciente, evitando spam."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = destinatario
    msg['Subject'] = "Confirmación de Turno - Clínica Dental"
    msg['Reply-To'] = EMAIL_ADDRESS  # Permite respuestas
    msg['Return-Path'] = EMAIL_ADDRESS  # Evita detección como spam

    # Formato del correo en HTML
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; text-align: center;">
        <h2 style="color: #2c3e50;">Confirmación de Turno</h2>
        <p>Hola <strong>{paciente_nombre}</strong>,</p>
        <p>Tu turno ha sido reservado con el <strong>{dentista_nombre}</strong>.</p>
        <p><strong>Fecha:</strong> {fecha}</p>
        <p><strong>Hora:</strong> {hora}</p>
        <hr>
        <p style="font-size: 12px; color: #777;">Si necesitas cancelar tu turno, puedes hacerlo desde tu cuenta.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"✅ Correo de confirmación enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")

def verify_reset_token(token, expiration=3600):
    """Verifica si el token es válido y retorna el email asociado."""
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=expiration)
        return email
    except Exception as e:
        print(f"❌ Error al verificar el token: {e}")
        return None


def enviar_recordatorio(destinatario, paciente_nombre, dentista_nombre, fecha, hora):
    """Envía un recordatorio de turno por correo electrónico."""
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = destinatario
    msg['Subject'] = "🔔 Recordatorio de Turno - Clínica Dental"

    # Cuerpo del correo en HTML
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; text-align: center;">
        <h2 style="color: #0984e3;">📅 Recordatorio de Turno</h2>
        <p>Hola <strong>{paciente_nombre}</strong>,</p>
        <p>Te recordamos que tienes un turno programado con el <strong>{dentista_nombre}</strong>.</p>
        <p><strong>📅 Fecha:</strong> {fecha}</p>
        <p><strong>🕒 Hora:</strong> {hora}</p>
        <hr>
        <p style="font-size: 12px; color: #777;">Si necesitas cancelar o modificar tu turno, contáctanos.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"✅ Correo de recordatorio enviado a {destinatario}")
    except Exception as e:
        print(f"❌ Error al enviar el correo de recordatorio: {e}")
        
# Buscar turnos dentro de 3 días y enviar recordatorios
def enviar_recordatorios_turnos():
    with app.app_context():
        fecha_recordatorio = (datetime.today() + timedelta(days=3)).strftime("%Y-%m-%d")
        turnos = Appointment.query.filter_by(date=fecha_recordatorio).all()

        for turno in turnos:
            paciente = User.query.get(turno.user_id)
            dentista = Dentist.query.get(turno.dentist_id)
            if paciente and dentista:
                enviar_recordatorio(paciente.email, paciente.name, dentista.name, turno.date, turno.time)

# Tarea programada para enviar recordatorios a las 8:00 AM
@scheduler.task('cron', id='recordatorio_turnos', hour=8, minute=0)
def tarea_diaria_recordatorios():
    enviar_recordatorios_turnos()

def enviar_correo(destinatario, subject, reset_url):
    """Función para enviar un correo con HTML."""
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = destinatario
    msg['Subject'] = subject

    # Cuerpo del correo en formato HTML
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; text-align: center;">
        <h2 style="color: #2c3e50;">Recuperación de Contraseña</h2>
        <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
        <p>
            <a href="{reset_url}" style="display: inline-block; padding: 10px 15px; 
            font-size: 16px; color: white; background-color: #007BFF; 
            text-decoration: none; border-radius: 5px;">
            Restablecer Contraseña
            </a>
        </p>
        <p>Si no solicitaste este cambio, ignora este correo.</p>
        <hr>
        <p style="font-size: 12px; color: #777;">Este correo ha sido enviado automáticamente.</p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            print("✅ Correo enviado con éxito a:", destinatario)
    except Exception as e:
        print(f"❌ Error al enviar el correo: {e}")




def generar_horarios(intervalo):
    """Genera horarios individuales a partir de un rango"""
    horarios = []
    inicio, fin = intervalo.split('-')
    hora_actual = datetime.strptime(inicio, "%H:%M")
    hora_fin = datetime.strptime(fin, "%H:%M")

    while hora_actual < hora_fin:
        horarios.append(hora_actual.strftime("%H:%M"))
        hora_actual += timedelta(minutes=30)  # Intervalo de 30 min

    return horarios

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            
            if user.email == "dentistafunes@gmail.com":
                return redirect(url_for("admin"))  
            else:
                return redirect(url_for("dashboard"))  

        flash("⚠️ Credenciales incorrectas. Verifica tu email y contraseña.", "danger")  # 🔹 Flash message
    return render_template("login.html")

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Genera un token y envía un correo con el enlace para restablecer la contraseña en HTML."""
    if request.method == "POST":
        email = request.form.get("email")
        user = User.query.filter_by(email=email).first()

        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('reset_password', token=token, _external=True)

            # 📩 Enviar correo con el enlace de recuperación
            enviar_correo(user.email, "Recuperar Contraseña", reset_url)

            flash("📧 Se ha enviado un correo con instrucciones para restablecer tu contraseña. Revisa tu bandeja de entrada y spam.", "info")

        else:
            flash("⚠️ No se encontró una cuenta con ese correo electrónico.", "danger")

    return render_template("forgot_password.html") 
@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        return "El enlace de restablecimiento es inválido o ha expirado.", 400

    if request.method == "POST":
        new_password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            return redirect(url_for("login"))
        return "El usuario no existe.", 404

    return render_template("reset_password.html", token=token)
@app.route("/register", methods=["GET", "POST"])
def register():
    """Registro de usuario con validaciones de contraseña segura."""
    if request.method == "POST":
        email = request.form.get("email")
        name = request.form.get("name")
        last_name = request.form.get("last_name")  
        password = request.form.get("password")
        phone = request.form.get("phone")
        obra_social = request.form.get("obraSocial")

        # Validación de campos vacíos
        if not email or not name or not last_name or not password or not phone or not obra_social:
            flash("Todos los campos son obligatorios.", "danger")
            return render_template("register.html")

        # Validación del formato de la contraseña
        password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_regex, password):
            flash("⚠️ La contraseña debe contener al menos 8 caracteres, una mayúscula, una minúscula, un número y un carácter especial.", "danger")
            return render_template("register.html")

        # Verificar si el usuario ya existe
        if User.query.filter_by(email=email).first():
            flash("⚠️ El email ya está registrado.", "danger")
            return render_template("register.html")

        # Hashear la contraseña antes de guardarla
        hashed_password = generate_password_hash(password)

        # Crear el usuario
        user = User(email=email, password=hashed_password, name=name, phone=phone)
        db.session.add(user)
        db.session.commit()

        flash("✅ Registro exitoso. Ahora puedes iniciar sesión.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/dashboard")
@login_required
def dashboard():
    """Renderiza el panel según el tipo de usuario."""
    user = current_user

    # Si el usuario es administrador, muestra los turnos de todos
    if user.email == "dentistafunes@gmail.com":
        appointments = Appointment.query.all()
        dentists = Dentist.query.all()
        return render_template("admin_dashboard.html", user=user, appointments=appointments, dentists=dentists)

    # Si el usuario es un paciente, ve sus turnos y la lista de dentistas
    else:
        appointments = Appointment.query.filter_by(user_id=user.id).all()
        dentists = Dentist.query.all()  # Asegurarse de obtener los dentistas
        return render_template("patient_dashboard.html", user=user, appointments=appointments, dentists=dentists)

@app.route("/api/horarios_disponibles", methods=["GET"])
def obtener_horarios_disponibles():
    dentista_id = request.args.get("dentista_id")
    fecha = request.args.get("fecha")

    if not dentista_id or not fecha:
        return jsonify({"error": "Faltan parámetros"}), 400

    dentista = Dentist.query.get(dentista_id)
    if not dentista:
        return jsonify({"error": "Dentista no encontrado"}), 404

    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
    dia_semana = fecha_obj.strftime("%A").lower()

    if not isinstance(dentista.availability, dict):
        return jsonify({"error": "Los horarios no están correctamente almacenados"}), 500

    horarios_rango = dentista.availability.get(dia_semana, [])

    # Convertir rango de tiempo a lista de horas individuales
    horarios_disponibles = []
    for intervalo in horarios_rango:
        horarios_disponibles.extend(generar_horarios(intervalo))

    # Obtener turnos ocupados
    turnos_ocupados = Appointment.query.filter_by(dentist_id=dentista.id, date=fecha).all()
    horas_ocupadas = {turno.time for turno in turnos_ocupados}

    # Filtrar horarios ocupados
    horarios_finales = [{"hora": hora, "disponible": hora not in horas_ocupadas} for hora in horarios_disponibles]

    return jsonify({"horarios": horarios_finales})
@app.route("/admin")
@login_required
def admin():
    if current_user.email != "dentistafunes@gmail.com":
        return redirect(url_for("dashboard"))  # Redirige a pacientes si no es admin

    # Obtener los turnos con datos de pacientes y dentistas
    appointments = Appointment.query.join(User, Appointment.user_id == User.id)\
                                    .join(Dentist, Appointment.dentist_id == Dentist.id)\
                                    .add_columns(User.name.label("user_name"), 
                                                 Dentist.name.label("dentist_name"),
                                                 Appointment.date, Appointment.time, Appointment.id)\
                                    .all()

    return render_template("admin_dashboard.html", appointments=appointments)
@app.route("/admin/cancelar/<int:turno_id>", methods=["POST"])
@login_required
def cancelar_turno_admin(turno_id):
    """Permite al administrador cancelar un turno y notificar al paciente por correo."""
    if current_user.email != "dentistafunes@gmail.com":
        return redirect(url_for("dashboard"))  # Evita que otros usuarios accedan

    turno = Appointment.query.get(turno_id)
    
    if not turno:
        flash("Turno no encontrado", "danger")
        return redirect(url_for("admin"))

    # Corregi el acceso al paciente y al dentista
    paciente = User.query.get(turno.user_id)
    dentista = Dentist.query.get(turno.dentist_id)

    if not paciente or not dentista:
        flash("Error al obtener datos del paciente o dentista.", "danger")
        return redirect(url_for("admin"))

    fecha = turno.date
    hora = turno.time

    # Eliminar el turno de la base de datos
    db.session.delete(turno)
    db.session.commit()

    # Enviar correo al paciente notificando la cancelación
    enviar_correo_cancelacion(paciente.email, paciente.name, dentista.name, fecha, hora)

    flash("El turno ha sido cancelado con éxito y se ha notificado al paciente", "success")

    return redirect(url_for("admin"))


@app.route("/reservar", methods=["POST"])
@login_required
def reservar():
    dentista_id = request.form["dentista_id"]
    fecha = request.form["fecha"]
    hora = request.form["hora"]

    if not dentista_id or not fecha or not hora:
        flash("Todos los campos son obligatorios.", "danger")
        return redirect(url_for("dashboard")) 

    dentist = Dentist.query.get(dentista_id)
    if not dentist:
        flash("Dentista no encontrado.", "danger")
        return redirect(url_for("dashboard"))  

    # Crear el turno en la base de datos
    nuevo_turno = Appointment(user_id=current_user.id, dentist_id=dentista_id, date=fecha, time=hora)
    db.session.add(nuevo_turno)
    db.session.commit()

    flash("Tu turno ha sido reservado y recibirás un correo de confirmación.", "success")
    
    # Redirigir al dashboard
    return redirect(url_for("dashboard"))  

@app.route("/cancelar/<int:turno_id>", methods=["GET"])
@login_required
def cancelar(turno_id):
    turno = Appointment.query.get(turno_id)

    if not turno:
        flash("El turno no existe.", "danger")
        return redirect(url_for("dashboard"))  

    db.session.delete(turno)
    db.session.commit()
    
    flash("Turno cancelado con éxito.", "success")
    return redirect(url_for("dashboard"))  

@app.route("/admin/exportar/excel")
@login_required
def exportar_excel():
    """Exporta los turnos agendados en formato Excel."""
    if current_user.email != "dentistafunes@gmail.com":
        return redirect(url_for("dashboard"))

    appointments = Appointment.query.join(User, Appointment.user_id == User.id)\
                                    .join(Dentist, Appointment.dentist_id == Dentist.id)\
                                    .add_columns(User.name.label("Paciente"), 
                                                 Dentist.name.label("Dentista"),
                                                 Appointment.date.label("Fecha"),
                                                 Appointment.time.label("Hora"))\
                                    .all()

    # Convertir a DataFrame de pandas
    df = pd.DataFrame([(t.Paciente, t.Dentista, t.Fecha, t.Hora) for t in appointments],
                      columns=["Paciente", "Dentista", "Fecha", "Hora"])

    # Guardar en BytesIO
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Turnos")

    output.seek(0)

    return Response(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": "attachment;filename=turnos.xlsx"})

@app.route("/admin/exportar/pdf")
@login_required
def exportar_pdf():
    """Exporta los turnos agendados en formato PDF."""
    if current_user.email != "dentistafunes@gmail.com":
        return redirect(url_for("dashboard"))

    appointments = Appointment.query.join(User, Appointment.user_id == User.id)\
                                    .join(Dentist, Appointment.dentist_id == Dentist.id)\
                                    .add_columns(User.name.label("Paciente"), 
                                                 Dentist.name.label("Dentista"),
                                                 Appointment.date.label("Fecha"),
                                                 Appointment.time.label("Hora"))\
                                    .all()

    # Crear HTML para el PDF
    html_content = f"""
    <html>
    <head><style>
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid black; padding: 8px; text-align: center; }}
        th {{ background-color: #f2f2f2; }}
    </style></head>
    <body>
        <h2 style="text-align: center;">Turnos Agendados</h2>
        <table>
            <tr><th>Paciente</th><th>Dentista</th><th>Fecha</th><th>Hora</th></tr>
    """

    for t in appointments:
        html_content += f"<tr><td>{t.Paciente}</td><td>{t.Dentista}</td><td>{t.Fecha}</td><td>{t.Hora}</td></tr>"

    html_content += "</table></body></html>"

    # Generar PDF en BytesIO
    output = io.BytesIO()
    pisa.CreatePDF(io.StringIO(html_content), dest=output)
    output.seek(0)

    return Response(output, mimetype="application/pdf",
                    headers={"Content-Disposition": "attachment;filename=turnos.pdf"})

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

if __name__ == "__main__":

    app.config["SECRET_KEY"] = "una_clave_secreta_segura"
    with app.app_context():
        db.create_all()
    app.run(debug=True)