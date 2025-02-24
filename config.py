import os

class Config:
    SECRET_KEY = "tu_secreto_super_seguro"
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"  # O la URI de tu base de datos
    SQLALCHEMY_TRACK_MODIFICATIONS = False
