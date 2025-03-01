from django.db import models
from registro_vuelos.models.inventarios import InventarioOro


class Cliente(models.Model):
    nombre = models.CharField(max_length=255, unique=True, verbose_name="Nombre del Cliente")
    deuda_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Deuda Total en Dólares")
    deuda_gramos_oro = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Deuda Total en Gramos de Oro")
    total_generado_dolares = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Total Generado en Dólares")
    total_generado_gramos = models.DecimalField(max_digits=15, decimal_places=2, default=0.00, verbose_name="Total Generado en Gramos")

    def registrar_abono_gramos(self, gramos):
        """
        Registra un abono en gramos de oro.
        Actualiza el inventario, la deuda y el total generado.
        """
        if gramos <= 0:
            raise ValueError("El monto de gramos debe ser mayor a cero.")

        if self.deuda_gramos_oro < gramos:
            raise ValueError("El abono excede la deuda en gramos.")

        # Obtener el inventario de oro
        inventario = InventarioOro.objects.first()
        if not inventario:
            raise ValueError("No se encontró un inventario de oro.")

        # Actualizar el inventario
        inventario.gramos_disponibles_polvo += gramos
        inventario.gramos_por_cobrar_polvo -= gramos
        inventario.save()

        # Actualizar la deuda y el total generado
        self.deuda_gramos_oro -= gramos
        self.total_generado_gramos += gramos
        self.save()

    def registrar_transaccion(self, tipo, monto, descripcion=None):
        HistorialTransacciones.objects.create(
            cliente=self,
            tipo=tipo,
            monto=monto,
            descripcion=descripcion or f"Transacción de tipo {tipo}"
        )       

    def registrar_abono_moneda(self, monto, tasa_cambio=None):
        """
        Registra un abono en moneda.
        Si se incluye una tasa de cambio, convierte el monto a la moneda base.
        """
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a cero.")

        if self.deuda_total < monto:
            raise ValueError("El abono excede la deuda en moneda.")

        # Convertir el monto si se proporciona una tasa de cambio
        abono = monto
        if tasa_cambio:
            abono = monto / tasa_cambio

        # Actualizar la deuda y el total generado
        self.deuda_total -= abono
        self.total_generado_dolares += abono
        self.save()

    def registrar_transaccion(self, tipo, monto, descripcion=None):
        HistorialTransacciones.objects.create(
            cliente=self,
            tipo=tipo,
            monto=monto,
            descripcion=descripcion or f"Transacción de tipo {tipo}"
        )    

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"


class HistorialTransacciones(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='transacciones')
    fecha = models.DateTimeField(auto_now_add=True)
    tipo = models.CharField(
        max_length=50,
        choices=[
            ('abono_moneda', 'Abono en Moneda'),
            ('abono_gramos', 'Abono en Gramos'),
            ('vuelo_contado', 'Vuelo Contado'),
        ],
        verbose_name="Tipo de Transacción",
    )
    monto = models.DecimalField(max_digits=15, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transacción {self.id} - {self.cliente.nombre}"

    class Meta:
        verbose_name = "Historial de Transacciones"
        verbose_name_plural = "Historial de Transacciones"   