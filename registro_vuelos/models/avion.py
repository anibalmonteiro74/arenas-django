from django.db import models
from django.db.models import Sum
from datetime import date
from django.apps import apps  # 🔥 Importación diferida

# Modelo para los aviones
class Avion(models.Model):
    matricula = models.CharField(max_length=50, unique=True)  # Matrícula única para cada avión
    modelo = models.CharField(max_length=100, blank=True, null=True)  # Opcional: Modelo del avión
    fabricante = models.CharField(max_length=100, blank=True, null=True)  # Opcional: Fabricante
    capacidad_pasajeros = models.PositiveIntegerField(blank=True, null=True)  # Opcional: Capacidad de pasajeros
    capacidad_carga = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Capacidad de carga en kg
    fecha_registro = models.DateTimeField(auto_now_add=True)  # Fecha de registro del avión

    # 🚀 NUEVO CAMPO: Horómetro inicial del avión
    horometro_inicial = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.0,
        verbose_name="Horómetro Inicial",
        help_text="Introduce el horómetro del avión al momento de su registro."
    )

    def obtener_ultimo_horometro(self):
        """Devuelve el último horómetro registrado en los tramos de vuelo o el inicial si no hay vuelos."""
        TramoVuelo = apps.get_model("registro_vuelos", "TramoVuelo")
        ultimo_tramo = TramoVuelo.objects.filter(vuelo__avion=self).order_by("-horometro_fin").first()
        return ultimo_tramo.horometro_fin if ultimo_tramo else self.horometro_inicial

    def total_horometro_en_periodo(self, fecha_inicio, fecha_fin):
        """Calcula el total de incremento del horómetro en un rango de fechas."""
        TramoVuelo = apps.get_model("registro_vuelos", "TramoVuelo")  # 🔥 Llamamos el modelo solo cuando se usa
        total = TramoVuelo.objects.filter(
            vuelo__avion=self,
            vuelo__fecha__range=[fecha_inicio, fecha_fin]
        ).aggregate(Sum("incremento_horometro"))["incremento_horometro__sum"] or 0

        return total

    def __str__(self):
        return f"{self.matricula} - {self.modelo or 'Sin modelo'}"

    class Meta:
        verbose_name = "Avión"
        verbose_name_plural = "Aviones"