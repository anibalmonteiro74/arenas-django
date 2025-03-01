from django.db import models

class Moneda(models.Model):
    nombre = models.CharField(max_length=50, verbose_name="Nombre de la Moneda")
    simbolo = models.CharField(max_length=10, verbose_name="Símbolo", help_text="Ejemplo: USD, EUR")

    def __str__(self):
        return f"{self.nombre} ({self.simbolo})" 