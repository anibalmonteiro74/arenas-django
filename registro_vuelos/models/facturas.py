from django.db import models

class SerieFactura(models.Model):
    """
    Modelo para gestionar las series de facturación.
    """
    nombre = models.CharField(max_length=2, unique=True)  # Ejemplo: AO, BT, PZ
    numero_actual = models.PositiveIntegerField(default=0)  # Número actual en la serie

    def __str__(self):
        return f"{self.nombre} (Siguiente: {self.nombre}{str(self.numero_actual + 1).zfill(5)})"

    def generar_numero_factura(self):
        """
        Genera el siguiente número de factura en la serie.
        """
        self.numero_actual += 1
        self.save()
        return f"{self.nombre}{str(self.numero_actual).zfill(5)}"