from django.db import models
from decimal import Decimal


class InventarioOro(models.Model):
    gramos_disponibles_polvo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Gramos Disponibles (Polvo)")
    gramos_por_cobrar_polvo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Gramos por Cobrar (Polvo)")
    gramos_ajustados_polvo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Gramos Ajustados (Polvo)", editable=False)
    precio_por_gramo = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Precio por Gramo")
    valor_total_usd = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False, verbose_name="Valor Total (USD)")

    def ajustar_polvo(self, ajuste):
        """Ajusta el inventario de polvo antes de fundir."""
        if self.gramos_disponibles_polvo is None:
            self.gramos_disponibles_polvo = Decimal(0)
        if self.gramos_ajustados_polvo is None:
            self.gramos_ajustados_polvo = Decimal(0)

        self.gramos_ajustados_polvo = self.gramos_disponibles_polvo + ajuste
        self.save()
    def actualizar_valor_total(self):
        """Calcula el valor total en USD según el precio por gramo."""
        self.valor_total_usd = self.gramos_disponibles_polvo * self.precio_por_gramo
        self.save()

    def actualizar_valor_total(self):
        """Calcula el valor total en USD según el precio por gramo."""
        if self.gramos_disponibles_polvo is None:
            self.gramos_disponibles_polvo = Decimal(0)

        self.valor_total_usd = self.gramos_disponibles_polvo * self.precio_por_gramo
        self.save()

    def __str__(self):
        return f"Inventario de Oro: {self.gramos_disponibles_polvo}g Polvo, {self.valor_total_usd} USD"
    
    def fundir_a_barra(self, peso_real, ley, ajuste=0):
        """
        Realiza la fundición de los gramos disponibles en polvo, aplicando ajustes,
        y genera una barra con el peso real y la ley especificados.
        """
        # Validar y asignar valores predeterminados si son None
        if self.gramos_disponibles_polvo is None:
            self.gramos_disponibles_polvo = Decimal(0)
        if self.gramos_ajustados_polvo is None:
            self.gramos_ajustados_polvo = Decimal(0)

        # Ajustar gramos disponibles
        gramos_a_fundir = self.gramos_disponibles_polvo + ajuste
        if gramos_a_fundir <= 0 or gramos_a_fundir < peso_real:
            raise ValueError("No hay suficientes gramos disponibles para fundir.")

        # Restar gramos del inventario
        self.gramos_disponibles_polvo -= gramos_a_fundir
        self.gramos_ajustados_polvo = gramos_a_fundir
        self.save()

        # Generar la barra
        codigo_barra = f"ARENA-{self.fecha_codigo()}"
        barra = Barra.objects.create(
            codigo=codigo_barra,
            peso=peso_real,
            ley=ley,
            inventario=self
        )
        barra.calcular_gramos_puros()

        return barra

    def fecha_codigo(self):
        """
        Genera una parte del código basado en la fecha actual (DDMMYY).
        """
        from datetime import datetime
        return datetime.now().strftime("%d%m%y")
    
    def generar_barra(self, gramos_ajustados, peso_barra, ley):
        """
        Genera una nueva barra con los gramos ajustados.
        """
        # Calcular porcentaje de merma
        merma = gramos_ajustados - peso_barra
        porcentaje_merma = (merma / gramos_ajustados) * 100

        # Crear una barra
        codigo_barra = f"ARENA-{self.generar_codigo_barra()}"
        barra = Barra.objects.create(
            codigo=codigo_barra,
            peso=peso_barra,
            ley=ley,
            inventario=self
        )
        barra.calcular_gramos_puros()

        # Actualizar inventario
        self.gramos_disponibles_polvo -= gramos_ajustados
        self.save()

        return barra, porcentaje_merma

    def generar_codigo_barra(self):
        """
        Genera un código único basado en la fecha y un sufijo alfabético.
        """
        from datetime import datetime
        fecha = datetime.now().strftime("%d%m%y")
        contador_barras = Barra.objects.filter(
            fecha_generacion=datetime.now().date()
        ).count() + 1
        sufijo = chr(64 + contador_barras)  # Genera A, B, C...
        return f"{fecha}{sufijo}"
    
