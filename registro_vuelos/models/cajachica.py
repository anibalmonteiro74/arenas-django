from django.db import models
import logging
logger = logging.getLogger('arenas')

class CajaChica(models.Model):
    nombre = models.CharField(max_length=255, unique=True)  # Ejemplo: "SEU" o "CCS"
    balance_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return self.nombre


class CuentaGasto(models.Model):
    nombre = models.CharField(max_length=255, unique=True)  # Ejemplo: "Pago Pilotos", "Combustible"
    descripcion = models.TextField(null=True, blank=True)  # Detalles adicionales
    balance_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Balance acumulado de gastos

    def __str__(self):
        return self.nombre


class MovimientoGasto(models.Model):
    cuenta = models.ForeignKey(CuentaGasto, on_delete=models.CASCADE, related_name="movimientos")
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    motivo = models.CharField(max_length=255, null=True, blank=True)
    nota = models.TextField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        logger.info(f"🏦 ACTUALIZANDO CAJA {self.pk}, Balance antes: {self.balance_actual}")
        super().save(*args, **kwargs)
        logger.info(f"✅ Caja {self.pk} guardada, nuevo balance: {self.balance_actual}")

        if self.pk:  # Si el movimiento ya existe, calculamos la diferencia
            movimiento_original = MovimientoCaja.objects.get(pk=self.pk)
            diferencia = self.monto - movimiento_original.monto
        else:
            diferencia = self.monto  # Es un nuevo movimiento, tomamos el monto completo

        # Lógica para ingreso
        if self.tipo == "ingreso":
            self.caja.balance_actual += diferencia

        # Lógica para egreso (gasto)
        elif self.tipo == "egreso" and self.cuenta_gasto:
            self.caja.balance_actual -= diferencia
            self.cuenta_gasto.balance_total += diferencia
            self.cuenta_gasto.save()

        # Lógica para transferencia
        elif self.tipo == "transferencia" and self.caja_destino:
            self.caja.balance_actual -= diferencia
            self.caja_destino.balance_actual += diferencia
            self.caja_destino.save()

        # Guarda el balance actualizado de la caja
        self.caja.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.cuenta.nombre} - {self.monto} ({self.fecha.strftime('%Y-%m-%d')})"


class MovimientoCaja(models.Model):
    TIPO_MOVIMIENTO = [
        ('ingreso', 'Ingreso'),
        ('egreso', 'Gasto'),
        ('transferencia', 'Transferencia'),
    ]

    caja = models.ForeignKey(CajaChica, on_delete=models.CASCADE, related_name="movimientos")
    tipo = models.CharField(max_length=50, choices=TIPO_MOVIMIENTO)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    motivo = models.CharField(max_length=255, null=True, blank=True)
    nota = models.TextField(null=True, blank=True)
    caja_destino = models.ForeignKey(
        CajaChica, on_delete=models.CASCADE, null=True, blank=True, related_name="transferencias"
    )  # Solo aplica a transferencias
    cuenta_gasto = models.ForeignKey(
        CuentaGasto, on_delete=models.SET_NULL, null=True, blank=True, related_name="gastos"
    )  # Solo aplica a gastos
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            # Lógica para ingreso
            if self.tipo == "ingreso":
                self.caja.balance_actual += self.monto

            # Lógica para egreso (gasto)
            elif self.tipo == "egreso" and self.cuenta_gasto:
                self.caja.balance_actual -= self.monto
                self.cuenta_gasto.balance_total += self.monto
                self.cuenta_gasto.save()

            # Lógica para transferencia
            elif self.tipo == "transferencia" and self.caja_destino:
                self.caja.balance_actual -= self.monto
                self.caja_destino.balance_actual += self.monto
                self.caja_destino.save()

            # Guarda el balance actualizado de la caja
            self.caja.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tipo.capitalize()} - {self.monto} ({self.caja.nombre})"