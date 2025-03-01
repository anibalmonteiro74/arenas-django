from django.apps import AppConfig

class RegistroVuelosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'registro_vuelos'

    def ready(self):
        import registro_vuelos.signals  # Importa las señales al iniciar la app