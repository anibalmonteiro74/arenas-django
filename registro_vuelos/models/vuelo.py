from django.db import models
from decimal import Decimal  # Para manejar valores decimales
import logging
logger = logging.getLogger('arenas')
from django.apps import apps
from registro_vuelos.models.avion import Avion
from registro_vuelos.models.trayectocosto import TrayectoCosto
from registro_vuelos.models.clientes import Cliente
from registro_vuelos.models.inventarios import InventarioOro  # Importar InventarioOro
from registro_vuelos.models.facturas import SerieFactura
from registro_vuelos.models.tramovuelo import TramoVuelo
from registro_vuelos.models.empleados import Empleado


# Modelo para los vuelos
class Vuelo(models.Model):
    serie_factura = models.ForeignKey(SerieFactura, on_delete=models.PROTECT, null=True, blank=False)
    numero_factura = models.CharField(max_length=15, blank=True, null=True)  # Ejemplo: AO00001-0

    TIPO_COBRO_CHOICES = [
        ('por_hora', 'Por Hora'),
        ('por_destino', 'Por Destino'),
        ('colaboracion', 'Colaboración'),
    ]

    avion = models.ForeignKey(Avion, on_delete=models.CASCADE, related_name="vuelos", verbose_name="Avión")
    piloto = models.ForeignKey(
        Empleado, on_delete=models.CASCADE, related_name="vuelos_piloto", limit_choices_to={'tipo': 'piloto'}
    )
    copiloto = models.ForeignKey(
        Empleado, on_delete=models.SET_NULL, related_name="vuelos_copiloto", blank=True, null=True,
        limit_choices_to={'tipo': 'copiloto'}
    )
    tipo_cobro = models.CharField(
        max_length=15,
        choices=TIPO_COBRO_CHOICES,
        default='por_hora',
        verbose_name="Tipo de cobro del vuelo"
    )
    horas_totales = models.DecimalField(
        max_digits=6, decimal_places=2, default=0.0, verbose_name="Horas totales de vuelo"
    )
    fecha = models.DateField(verbose_name="Fecha del vuelo")

    # Nuevo campo: Bitácora
    bitacora = models.CharField(
        max_length=20, unique=True, verbose_name="Número de Bitácora",
        help_text="Número alfanumérico único para identificar este vuelo.",
        default="SIN_BITACORA"  # Valor predeterminado
    )

    def __str__(self):
        return f"Vuelo en {self.avion.matricula} - {self.fecha} - Bitácora: {self.bitacora}"

    def actualizar_horas_y_costos(self, eliminar=False):
        """
        Actualiza las horas acumuladas y costos por trayecto para piloto y copiloto.
        Si `eliminar` es True, resta los valores; de lo contrario, los suma.
        """
        # Aseguramos que el multiplicador sea un Decimal desde el inicio
        multiplicador = Decimal(-1 if eliminar else 1)

        # Depuración inicial
        print(f"Antes -> multiplicador: {multiplicador} ({type(multiplicador)}), horas_totales: {self.horas_totales} ({type(self.horas_totales)})")

        # Forzar conversión de horas_totales a Decimal si es float
        if isinstance(self.horas_totales, float):
            self.horas_totales = Decimal(str(self.horas_totales))

        # Depuración para validar tipos después de conversión
        print(f"Después -> multiplicador: {multiplicador} ({type(multiplicador)}), horas_totales: {self.horas_totales} ({type(self.horas_totales)})")

        # Actualiza horas del piloto
        if self.piloto and self.piloto.tipo == 'piloto':
            if self.tipo_cobro == 'por_hora':
                self.piloto.horas_por_hora += multiplicador * self.horas_totales
            elif self.tipo_cobro == 'por_destino':
                self.piloto.horas_por_destino += multiplicador * self.horas_totales
                total_costo_piloto = self.piloto.total_costo_por_destino or 0
                for tramo in self.tramos_vuelo.all():
                    trayecto_costo = TrayectoCosto.objects.filter(
                        empleado=self.piloto, origen=tramo.origen, destino=tramo.destino
                    ).first()
                    if trayecto_costo:
                        total_costo_piloto += multiplicador * trayecto_costo.costo_trayecto

                self.piloto.total_costo_por_destino = total_costo_piloto
            elif self.tipo_cobro == 'colaboracion':
                self.piloto.horas_colaboracion += multiplicador * self.horas_totales

            self.piloto.horas_totales = (
                self.piloto.horas_por_hora +
                self.piloto.horas_por_destino +
                self.piloto.horas_colaboracion
            )
            self.piloto.save()

        # Actualiza horas del copiloto solo si existe
        if self.copiloto and self.copiloto.tipo == 'copiloto':
            if self.tipo_cobro == 'por_hora':
                self.copiloto.horas_por_hora += multiplicador * self.horas_totales
            elif self.tipo_cobro == 'por_destino':
                self.copiloto.horas_por_destino += multiplicador * self.horas_totales
                total_costo_copiloto = self.copiloto.total_costo_por_destino or 0
                for tramo in self.tramos_vuelo.all():
                    trayecto_costo = TrayectoCosto.objects.filter(
                        empleado=self.copiloto, origen=tramo.origen, destino=tramo.destino
                    ).first()
                    if trayecto_costo:
                        total_costo_copiloto += multiplicador * trayecto_costo.costo_trayecto

                self.copiloto.total_costo_por_destino = total_costo_copiloto
            elif self.tipo_cobro == 'colaboracion':
                self.copiloto.horas_colaboracion += multiplicador * self.horas_totales

            self.copiloto.horas_totales = (
                self.copiloto.horas_por_hora +
                self.copiloto.horas_por_destino +
                self.copiloto.horas_colaboracion
            )
            self.copiloto.save()

    def actualizar_acumulados(self):
        """
        Recalcula las horas totales del vuelo y actualiza acumulados
        """
        # Recalcular horas totales del vuelo
        self.horas_totales = sum(tramo.horas_tramo for tramo in self.tramos_vuelo.all()) or 0
        self.save(update_fields=["horas_totales"])

        # Inicializar acumuladores
        total_costo_piloto = 0
        total_costo_copiloto = 0

        # Inicializar acumuladores para cada caja
        caja_acumulados = {}

        # Primera pasada: recolectar todos los valores por caja
        for tramo in self.tramos_vuelo.all():
            if tramo.forma_pago == "moneda" and tramo.monto_en_dolares and tramo.tipo_pago == "contado" and tramo.caja:
                caja_id = tramo.caja.id
                if caja_id not in caja_acumulados:
                    caja_acumulados[caja_id] = Decimal('0')
                
                caja_acumulados[caja_id] += tramo.monto_en_dolares
        
        # Segunda pasada: actualizar cada caja una sola vez
        for caja_id, monto_total in caja_acumulados.items():
            from registro_vuelos.models.cajachica import CajaChica
            caja = CajaChica.objects.get(id=caja_id)
            
            # Calcular el balance actual
            
            total_caja = sum(
                tramo.monto_en_dolares for tramo in TramoVuelo.objects.filter(
                    caja_id=caja_id, 
                    forma_pago="moneda", 
                    tipo_pago="contado"
                ) if tramo.monto_en_dolares
            )
            
            caja.balance_actual = total_caja
            caja.save()

        # Actualizar acumulados de clientes afectados por este vuelo
        clientes_afectados = set()
        for tramo in self.tramos_vuelo.all():
            if tramo.cliente:
                clientes_afectados.add(tramo.cliente.id)
        
        # Para cada cliente afectado, recalcular sus totales basados en TODO su historial
        for cliente_id in clientes_afectados:
            cliente = Cliente.objects.get(id=cliente_id)
            
            
            # Reiniciar contadores
            total_gramos_contado = Decimal('0')
            total_gramos_credito = Decimal('0')
            total_dolares_contado = Decimal('0')
            total_dolares_credito = Decimal('0')
            
            # Sumar todos los tramos históricos
            for tramo in TramoVuelo.objects.filter(cliente=cliente):
                if tramo.forma_pago == "gramos":
                    if tramo.tipo_pago == "contado":
                        total_gramos_contado += tramo.pago_en_gramos
                    elif tramo.tipo_pago == "credito":
                        total_gramos_credito += tramo.pago_en_gramos
                elif tramo.forma_pago == "moneda" and tramo.monto_en_dolares:
                    if tramo.tipo_pago == "contado":
                        total_dolares_contado += tramo.monto_en_dolares
                    elif tramo.tipo_pago == "credito":
                        total_dolares_credito += tramo.monto_en_dolares
            
            # Actualizar cliente con los totales calculados
            cliente.total_generado_gramos = total_gramos_contado
            cliente.deuda_gramos_oro = total_gramos_credito
            cliente.total_generado_dolares = total_dolares_contado
            cliente.deuda_total = total_dolares_credito
            cliente.save()

        # Actualizar HORAS Y COSTOS del piloto
        if self.piloto:
            self.piloto.horas_por_hora = sum(
                vuelo.horas_totales for vuelo in self.piloto.vuelos_piloto.filter(tipo_cobro="por_hora")
            ) or 0

            self.piloto.horas_por_destino = sum(
                vuelo.horas_totales for vuelo in self.piloto.vuelos_piloto.filter(tipo_cobro="por_destino")
            ) or 0

            self.piloto.horas_colaboracion = sum(
                vuelo.horas_totales for vuelo in self.piloto.vuelos_piloto.filter(tipo_cobro="colaboracion")
            ) or 0

            self.piloto.horas_totales = (
                self.piloto.horas_por_hora +
                self.piloto.horas_por_destino +
                self.piloto.horas_colaboracion
            ) or 0

            # Calcular el costo por destino del piloto
            total_costo_piloto = sum(
                trayecto_costo.costo_trayecto
                for vuelo in self.piloto.vuelos_piloto.filter(tipo_cobro="por_destino")
                for tramo in vuelo.tramos_vuelo.all()
                if (trayecto_costo := TrayectoCosto.objects.filter(
                    empleado=self.piloto, origen=tramo.origen, destino=tramo.destino
                ).first())
            ) or 0

            self.piloto.total_costo_por_destino = total_costo_piloto
            self.piloto.save()

            actualizar_horas_empleado(self.piloto)

            

        # Actualizar HORAS Y COSTOS del copiloto si existe
        if self.copiloto:
            self.copiloto.horas_por_hora = sum(
                vuelo.horas_totales for vuelo in self.copiloto.vuelos_copiloto.filter(tipo_cobro="por_hora")
            ) or 0

            self.copiloto.horas_por_destino = sum(
                vuelo.horas_totales for vuelo in self.copiloto.vuelos_copiloto.filter(tipo_cobro="por_destino")
            ) or 0

            self.copiloto.horas_colaboracion = sum(
                vuelo.horas_totales for vuelo in self.copiloto.vuelos_copiloto.filter(tipo_cobro="colaboracion")
            ) or 0

            self.copiloto.horas_totales = (
                self.copiloto.horas_por_hora +
                self.copiloto.horas_por_destino +
                self.copiloto.horas_colaboracion
            ) or 0

            # Calcular el costo por destino del copiloto
            total_costo_copiloto = sum(
                trayecto_costo.costo_trayecto
                for vuelo in self.copiloto.vuelos_copiloto.filter(tipo_cobro="por_destino")
                for tramo in vuelo.tramos_vuelo.all()
                if (trayecto_costo := TrayectoCosto.objects.filter(
                    empleado=self.copiloto, origen=tramo.origen, destino=tramo.destino
                ).first())
            ) or 0

            self.copiloto.total_costo_por_destino = total_costo_copiloto
            self.copiloto.save()

            actualizar_horas_empleado(self.copiloto)

    def actualizar_inventario_oro(self, revertir=False):
        inventario = InventarioOro.objects.first()
        if not inventario:
            raise ValueError("No existe un inventario de oro configurado.")
        multiplicador = -1 if revertir else 1
        total_gramos_contado = Decimal(0)
        total_gramos_credito = {}

        # Sumar o restar los valores según el estado del tramo
        for tramo in self.tramos_vuelo.all():
            if tramo.pago_en_gramos:
                if tramo.tipo_pago == "contado":
                    total_gramos_contado += multiplicador * Decimal(tramo.pago_en_gramos)
                elif tramo.tipo_pago == "credito" and tramo.cliente:
                    if tramo.cliente.id not in total_gramos_credito:
                        total_gramos_credito[tramo.cliente.id] = Decimal(0)
                    total_gramos_credito[tramo.cliente.id] += multiplicador * Decimal(tramo.pago_en_gramos)

        # Actualizar inventario sin sobrescribir
        inventario.gramos_disponibles_polvo += total_gramos_contado
        inventario.gramos_por_cobrar_polvo += sum(total_gramos_credito.values())
        inventario.save(update_fields=["gramos_disponibles_polvo", "gramos_por_cobrar_polvo"])

        # Actualizar la deuda de los clientes
        for cliente_id, gramos in total_gramos_credito.items():
            cliente = Cliente.objects.get(id=cliente_id)
            cliente.deuda_gramos_oro += gramos
            cliente.save(update_fields=["deuda_gramos_oro"])
            

    def save(self, *args, **kwargs):
        logger.info(f"🛫 Guardando Vuelo ID: {self.pk}")

        super().save(*args, **kwargs)

        logger.info(f"✅ Vuelo ID: {self.pk} guardado correctamente")

        # Validar y generar número de factura
        if not self.numero_factura and self.serie_factura:
            numero_base = self.serie_factura.generar_numero_factura()
            self.numero_factura = f"{numero_base}-0"

           

        super().save(*args, **kwargs)  # Guarda los datos del vuelo

           


    def calcular_horas_totales(self):
        """Calcula las horas totales sumando los tramos asociados."""
        # Este método debe ser llamado después de que la instancia tenga un PK
        return sum(tramo.horas_tramo for tramo in self.tramos_vuelo.all())

    def delete(self, *args, **kwargs):
        """Revertir todos los acumulados antes de eliminar el vuelo"""
        print(f"🔍 Eliminando vuelo: {self.id}")
        
        # Iterar sobre cada tramo y ejecutar su método delete() individualmente
        for tramo in self.tramos_vuelo.all():
            tramo.delete()
        
        # Si aún necesitas revertir acumulados globales (por ejemplo, en el inventario)
        self.actualizar_inventario_oro(revertir=True)
        
        super().delete(*args, **kwargs)

    class Meta:
        verbose_name = "Vuelo"
        verbose_name_plural = "Vuelos"

def actualizar_horas_empleado(empleado):
    """
    Actualiza el saldo pendiente de un empleado basado en sus horas acumuladas.
    """
    
    # Obtener o crear saldo
    from registro_vuelos.models.empleados import SaldoEmpleado
    saldo, created = SaldoEmpleado.objects.get_or_create(empleado=empleado)
    
    # Calcular horas pendientes
    saldo.horas_pendientes_por_hora = empleado.horas_por_hora - saldo.total_horas_pagadas_por_hora
    saldo.horas_pendientes_por_destino = empleado.horas_por_destino - saldo.total_horas_pagadas_por_destino
    saldo.horas_pendientes_colaboracion = empleado.horas_colaboracion - saldo.total_horas_pagadas_colaboracion
    saldo.costo_pendiente_por_destino = empleado.total_costo_por_destino - saldo.total_costo_pagado_por_destino
    
    saldo.save()        