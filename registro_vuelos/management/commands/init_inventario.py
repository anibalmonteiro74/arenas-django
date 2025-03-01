from django.core.management.base import BaseCommand
from registro_vuelos.models.inventarios import InventarioOro

class Command(BaseCommand):
    help = 'Inicializa el inventario de oro'

    def handle(self, *args, **kwargs):
        if not InventarioOro.objects.exists():
            InventarioOro.objects.create(
                gramos_disponibles=0,
                gramos_por_cobrar=0,
                precio_por_gramo=60.00,
            )
            self.stdout.write(self.style.SUCCESS('Inventario inicial creado con éxito.'))
        else:
            self.stdout.write(self.style.WARNING('Ya existe un inventario. No se creó uno nuevo.'))