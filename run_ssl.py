from django.core.management.commands.runserver import Command as runserver
from django.core.management import execute_from_command_line
import os

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sistema_nuevo.settings")  # Cambia "sistema_nuevo" si tu proyecto tiene otro nombre

    cert_file = os.path.join("certificates", "127.0.0.1+1.pem")  # Ruta al certificado
    key_file = os.path.join("certificates", "127.0.0.1+1-key.pem")  # Ruta a la clave privada

    runserver.default_addr = "0.0.0.0"
    runserver.default_port = "8000"
    runserver.default_cert_file = cert_file
    runserver.default_key_file = key_file

    execute_from_command_line(["manage.py", "runserver_plus", "--cert-file", cert_file, "--key-file", key_file])