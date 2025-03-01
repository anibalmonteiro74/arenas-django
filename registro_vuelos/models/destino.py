from django.db import models

# Modelo para los destinos
class Destino(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del destino", default="Destino sin nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción del destino")
    activo = models.BooleanField(default=True, verbose_name="¿Está activo?")

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Destino"
        verbose_name_plural = "Destinos"