from django.db import models
from registro_vuelos.models.inventarios import InventarioOro

class Barra(models.Model):
    codigo = models.CharField(max_length=20, unique=True, verbose_name="Código de la Barra")
    peso = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Peso en Gramos")
    ley = models.DecimalField(max_digits=5, decimal_places=3, verbose_name="Ley (Pureza)")
    gramos_puros = models.DecimalField(max_digits=10, decimal_places=2, editable=False, verbose_name="Gramos Puros")
    fecha_generacion = models.DateField(auto_now_add=True, verbose_name="Fecha de Generación")
    inventario = models.ForeignKey(InventarioOro, on_delete=models.CASCADE, related_name="barras", verbose_name="Inventario Asociado")
    vendida = models.BooleanField(default=False, verbose_name="¿Vendida?")
    precio_venta_usd = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name="Precio de Venta (USD)")

    def calcular_gramos_puros(self):
        """Calcula los gramos puros basados en la ley."""
        self.gramos_puros = (self.peso * self.ley) / 1000
        self.save()

    def __str__(self):
        return f"Barra {self.codigo} - {self.peso}g ({self.ley}‰)"
    
    def vender(self, precio_por_gramo):
        """
        Marca la barra como vendida y calcula el ingreso generado.
        """
        if self.vendida:
            raise ValueError("Esta barra ya ha sido vendida.")

        self.precio_venta_usd = self.gramos_puros * precio_por_gramo
        self.vendida = True
        self.save()

        # Actualizar el inventario asociado
        inventario = self.inventario
        inventario.actualizar_valor_total()
        return self.precio_venta_usd
    
   
