from django.db import models
from registro_vuelos.models.empleados import Empleado
from registro_vuelos.models.destino import Destino

# Modelo para los costos de los destinos
class TrayectoCosto(models.Model):
    empleado = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name="trayectos_costo",
        verbose_name="Empleado (Piloto o Copiloto)"
    )
    origen = models.ForeignKey(
        Destino, on_delete=models.CASCADE, related_name="trayectos_salida",
        verbose_name="Destino de Origen"
    )
    destino = models.ForeignKey(
        Destino, on_delete=models.CASCADE, related_name="trayectos_llegada",
        verbose_name="Destino de Llegada"
    )
    costo_trayecto = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name="Costo del Trayecto"
    )

    class Meta:
        unique_together = ('empleado', 'origen', 'destino')  # Evita duplicados
        verbose_name = "Trayecto de Costo"
        verbose_name_plural = "Trayectos de Costo"

    def __str__(self):
        return f"{self.empleado.nombre} - {self.origen.nombre} -> {self.destino.nombre}: ${self.costo_trayecto}"