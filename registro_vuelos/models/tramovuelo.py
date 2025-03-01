from django.db import models
from decimal import Decimal
from django.db import transaction
from registro_vuelos.models.inventarios import InventarioOro
import logging
logger = logging.getLogger(__name__)
logger = logging.getLogger('arenas')
from registro_vuelos.models.facturas import SerieFactura
from django.core.exceptions import ValidationError

# Modelo para los tramos de un vuelo
class TramoVuelo(models.Model):
    vuelo = models.ForeignKey(
    "Vuelo", on_delete=models.CASCADE, null=True, related_name="tramos_vuelo"
    )
    numero_factura = models.CharField(max_length=15, blank=True, null=True)  # 🔹 Nuevo campo para la factura

    origen = models.ForeignKey(
        "Destino", on_delete=models.CASCADE, related_name="tramos_salida"
    )
    destino = models.ForeignKey(
        "Destino", on_delete=models.CASCADE, related_name="tramos_llegada"
    )
    horometro_inicio = models.DecimalField(max_digits=8, decimal_places=2)
    horometro_fin = models.DecimalField(max_digits=8, decimal_places=2)
    horas_tramo = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(0))

    # Nuevos campos
    OPCIONES_FACTURACION = [
        ('factura', 'Factura'),
        ('no_factura', 'No Factura'),
        ('colaboracion', 'Colaboración')
    ]
    facturacion = models.CharField(
        max_length=20,
        choices=OPCIONES_FACTURACION,
        default='no_factura',
        verbose_name="Opciones de Facturación"
    )
    cliente = models.ForeignKey(
        "Cliente", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Cliente",
        help_text="Selecciona el cliente para este tramo si aplica."
    )

    # Actualización del tipo_pago
    TIPO_PAGO_CHOICES = [
        ('contado', 'Contado'),
        ('credito', 'Crédito'),
        ('no_aplica', 'No Aplica')  # Nueva opción
    ]
    tipo_pago = models.CharField(
        max_length=10,
        choices=TIPO_PAGO_CHOICES,
        default='contado',
        verbose_name="Tipo de Pago"
    )
    pago_en_gramos = models.DecimalField(
    max_digits=10, decimal_places=2, default=Decimal(0), blank=True, null=True, verbose_name="Monto en Gramos"
    )

    tipo_carga = models.CharField(
        max_length=10,
        choices=[('pasajeros', 'Pasajeros'), ('mercancia', 'Mercancía'), ('mixto', 'Mixto')],
        default='pasajeros',
        verbose_name="Tipo de Carga"
    )
    descripcion_carga = models.TextField(
        blank=True,
        null=True,
        verbose_name="Descripción de la Carga",
        help_text="Descripción detallada de la carga transportada en este tramo."  
    )

    FORMA_PAGO_CHOICES = [
        ('moneda', 'Moneda'),
        ('gramos', 'Gramos'),
        ('no_aplica', 'No Aplica')
    ]
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES)
    moneda = models.CharField(max_length=10, blank=True, null=True)
    caja = models.ForeignKey('Caja', on_delete=models.SET_NULL, blank=True, null=True)
    tasa_cambio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cantidad_moneda = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monto_en_gramos = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    moneda = models.ForeignKey(
        "Moneda", on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name="Moneda",
        help_text="Selecciona la moneda utilizada para el pago."
    )
    tasa_cambio = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True,
        verbose_name="Tasa de Cambio",
        help_text="Tasa de cambio para convertir la moneda seleccionada a dólares."
    )
    cantidad_moneda = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Cantidad en Moneda"
    )
    monto_en_dolares = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
        verbose_name="Monto en Dólares",
        help_text="Calculado automáticamente según la tasa de cambio."
    )
    caja = models.ForeignKey(
        "CajaChica",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Caja Asociada",
        help_text="Selecciona la caja a afectar para pagos en moneda (contado)."
    )
    # 📌 Nuevo campo para almacenar el incremento del horómetro
    incremento_horometro = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal(0),
        verbose_name="Incremento del Horómetro"
    )

    def clean(self):
        """Validaciones antes de guardar un TramoVuelo"""

        # 🔥 Validación del horómetro
        if self.vuelo and self.vuelo.avion:
            avion = self.vuelo.avion

            # 🔥 Verificar si este tramo ya ha sido guardado en la base de datos
            if self.pk:  
                # 🔹 Si el tramo YA EXISTE en la base de datos, no validamos el inicio, porque ya fue validado antes.
                return  

            # 🔥 Buscar el último tramo guardado en la base de datos (excluyendo el actual)
            ultimo_tramo = TramoVuelo.objects.filter(
                vuelo__avion=avion
            ).exclude(pk=self.pk).order_by("-horometro_fin").first()

            # ✅ Si hay un tramo previo en la BD, validamos contra él
            if ultimo_tramo:
                if self.horometro_inicio != ultimo_tramo.horometro_fin:
                    raise ValidationError(
                        f"El horómetro de inicio debe ser {ultimo_tramo.horometro_fin}, pero ingresaste {self.horometro_inicio}."
                    )

            # ✅ Si no hay tramos previos, usamos el horómetro inicial del avión
            else:
                if self.horometro_inicio != avion.horometro_inicial:
                    raise ValidationError(
                        f"El primer tramo debe iniciar en {avion.horometro_inicial}, pero ingresaste {self.horometro_inicio}."
                    )

        # 🔥 Validaciones de forma de pago (mantiene la lógica existente)
        if self.forma_pago == "moneda":
            # Moneda, Caja, Tasa de Cambio y Cantidad Moneda son obligatorios
            if not self.moneda or not self.caja or not self.tasa_cambio or not self.cantidad_moneda:
                raise ValidationError("Si seleccionas 'Moneda', debes completar Moneda, Caja, Tasa de Cambio y Cantidad en Moneda.")
            # No se permite ingresar monto en gramos
            if self.monto_en_gramos:
                raise ValidationError("Si seleccionas 'Moneda', no puedes ingresar un monto en gramos.")

        if self.forma_pago == "gramos":
            # No se deben ingresar datos en Moneda, Caja, Tasa de Cambio o Cantidad Moneda
            if self.moneda or self.caja or self.tasa_cambio or self.cantidad_moneda:
                raise ValidationError("Si seleccionas 'Gramos', no puedes ingresar datos en Moneda, Caja, Tasa de Cambio o Cantidad en Moneda.")

        if self.forma_pago == "no_aplica":
            # No debe haber montos en ningún lado
            if self.monto_en_gramos or self.cantidad_moneda:
                raise ValidationError("Si seleccionas 'No Aplica', no puedes ingresar montos en Moneda ni en Gramos.")

        super().clean()
            
    gramos_aplicados = models.BooleanField(default=False)  # 🔥 Nuevo flag para evitar duplicaciones

        

    def save(self, *args, **kwargs):
        """
        Método mejorado de save() para manejar correctamente las actualizaciones de tramos
        y evitar duplicación en inventario y otros acumulados.
        """
        print("\n🔍 INICIO save() de TramoVuelo")
        print(f"   ▶ Tramo ID: {self.pk} | Vuelo: {self.vuelo}")

        # Prevenir recursión
        if hasattr(self, '_guardando'):
            print("⚠️ Evitando recursión en save()")
            return
        self._guardando = True

        try:
            with transaction.atomic():
                # Obtener el inventario con bloqueo
                inventario = InventarioOro.objects.select_for_update().first()
                if not inventario:
                    raise ValueError("No existe un inventario de oro configurado.")

                # Variables para mantener registro de lo que revertimos
                gramos_revertidos_disponibles = Decimal('0')
                gramos_revertidos_por_cobrar = Decimal('0')
                
                # 1. OBTENER Y REVERTIR ESTADO ANTERIOR
                if self.pk:
                    try:
                        tramo_anterior = TramoVuelo.objects.select_for_update().get(pk=self.pk)
                        print(f"📊 Estado anterior - Tramo {self.pk}:")
                        print(f"   Forma pago: {tramo_anterior.forma_pago}")
                        print(f"   Tipo pago: {tramo_anterior.tipo_pago}")
                        print(f"   Gramos: {tramo_anterior.pago_en_gramos}")
                        
                        # Revertir gramos según el tipo de pago anterior
                        if tramo_anterior.forma_pago == "gramos" and tramo_anterior.pago_en_gramos:
                            if tramo_anterior.tipo_pago == "contado":
                                print(f"🔄 Revirtiendo {tramo_anterior.pago_en_gramos} gramos disponibles")
                                inventario.gramos_disponibles_polvo -= tramo_anterior.pago_en_gramos
                                gramos_revertidos_disponibles = tramo_anterior.pago_en_gramos
                                
                                if tramo_anterior.cliente:
                                    tramo_anterior.cliente.total_generado_gramos -= tramo_anterior.pago_en_gramos
                                    tramo_anterior.cliente.save()
                                    
                            elif tramo_anterior.tipo_pago == "credito" and tramo_anterior.cliente:
                                print(f"🔄 Revirtiendo {tramo_anterior.pago_en_gramos} gramos por cobrar")
                                inventario.gramos_por_cobrar_polvo -= tramo_anterior.pago_en_gramos
                                gramos_revertidos_por_cobrar = tramo_anterior.pago_en_gramos
                                
                                tramo_anterior.cliente.deuda_gramos_oro -= tramo_anterior.pago_en_gramos
                                tramo_anterior.cliente.save()
                        
                        # Revertir efectos en moneda
                        if tramo_anterior.forma_pago == "moneda" and tramo_anterior.monto_en_dolares:
                            if tramo_anterior.tipo_pago == "contado" and tramo_anterior.caja:
                                tramo_anterior.caja.balance_actual -= tramo_anterior.monto_en_dolares
                                tramo_anterior.caja.save()
                                
                                if tramo_anterior.cliente:
                                    tramo_anterior.cliente.total_generado_dolares -= tramo_anterior.monto_en_dolares
                                    tramo_anterior.cliente.save()
                                    
                            elif tramo_anterior.tipo_pago == "credito" and tramo_anterior.cliente:
                                tramo_anterior.cliente.deuda_total -= tramo_anterior.monto_en_dolares
                                tramo_anterior.cliente.save()
                        
                        # Revertir horas de vuelo
                        if self.vuelo:
                            if self.vuelo.piloto:
                                self.vuelo.piloto.horas_totales -= tramo_anterior.horas_tramo
                                self.vuelo.piloto.save()
                            if self.vuelo.copiloto:
                                self.vuelo.copiloto.horas_totales -= tramo_anterior.horas_tramo
                                self.vuelo.copiloto.save()
                                
                    except TramoVuelo.DoesNotExist:
                        print("ℹ️ No se encontró estado anterior (nuevo tramo)")

                # 2. CALCULAR NUEVOS VALORES
                # Calcular horas
                if self.horometro_fin and self.horometro_inicio:
                    self.incremento_horometro = self.horometro_fin - self.horometro_inicio
                    self.horas_tramo = round(self.incremento_horometro * 60, 2)
                
                # Calcular monto en dólares
                if self.forma_pago == "moneda" and self.moneda and self.tasa_cambio and self.cantidad_moneda:
                    self.monto_en_dolares = self.cantidad_moneda / self.tasa_cambio
                else:
                    self.monto_en_dolares = None

                # Asignar número de factura si es necesario
                if not self.numero_factura and self.vuelo and self.vuelo.numero_factura:
                    numero_base = self.vuelo.numero_factura.split("-")[0]
                    tramos_existentes = self.vuelo.tramos_vuelo.exclude(pk=self.pk).count()
                    self.numero_factura = f"{numero_base}-{tramos_existentes + 1}"
                    print(f"📄 Subfactura generada: {self.numero_factura}")

                # 3. GUARDAR TRAMO
                super().save(*args, **kwargs)

                # 4. APLICAR NUEVOS EFECTOS
                if self.forma_pago == "gramos" and self.pago_en_gramos:
                    print(f"💰 Procesando pago en gramos: {self.pago_en_gramos}")
                    if self.tipo_pago == "contado":
                        print(f"➕ Sumando a disponibles: {self.pago_en_gramos}")
                        inventario.gramos_disponibles_polvo += self.pago_en_gramos
                        
                        if self.cliente:
                            self.cliente.total_generado_gramos += self.pago_en_gramos
                            self.cliente.save()
                            
                    elif self.tipo_pago == "credito" and self.cliente:
                        print(f"➕ Sumando a por cobrar: {self.pago_en_gramos}")
                        inventario.gramos_por_cobrar_polvo += self.pago_en_gramos
                        self.cliente.deuda_gramos_oro += self.pago_en_gramos
                        self.cliente.save()

                # Guardar inventario
                print(f"📊 Estado final inventario:")
                print(f"   Disponibles: {inventario.gramos_disponibles_polvo}")
                print(f"   Por cobrar: {inventario.gramos_por_cobrar_polvo}")
                inventario.save()

                # 5. APLICAR EFECTOS ADICIONALES
                if self.forma_pago == "moneda" and self.monto_en_dolares:
                    if self.tipo_pago == "contado" and self.caja:
                        self.caja.balance_actual += self.monto_en_dolares
                        self.caja.save()
                        
                        if self.cliente:
                            self.cliente.total_generado_dolares += self.monto_en_dolares
                            self.cliente.save()
                            
                    elif self.tipo_pago == "credito" and self.cliente:
                        self.cliente.deuda_total += self.monto_en_dolares
                        self.cliente.save()

                # Actualizar horas de vuelo
                if self.vuelo:
                    if self.vuelo.piloto:
                        self.vuelo.piloto.horas_totales += self.horas_tramo
                        self.vuelo.piloto.save()
                    if self.vuelo.copiloto:
                        self.vuelo.copiloto.horas_totales += self.horas_tramo
                        self.vuelo.copiloto.save()

                # Actualizar horómetro del avión si es necesario
                if self.vuelo and self.vuelo.avion and self.horometro_fin:
                    ultimo_horometro = self.vuelo.avion.obtener_ultimo_horometro()
                    if self.horometro_fin > ultimo_horometro:
                        print(f"🔄 Actualizando horómetro del avión a {self.horometro_fin}")
                        self.vuelo.avion.horometro_inicial = self.horometro_fin
                        self.vuelo.avion.save()

                # 6. ACTUALIZAR ACUMULADOS DEL VUELO
                if self.vuelo:
                    self.vuelo.actualizar_acumulados()

                print("✅ Tramo guardado exitosamente")

        except Exception as e:
            print(f"❌ Error al guardar tramo: {str(e)}")
            raise

        finally:
            if hasattr(self, '_guardando'):
                del self._guardando

   
    def delete(self, *args, **kwargs):
        # Revertir acumulados antes de eliminar el tramo
        inventario = InventarioOro.objects.first()
        if not inventario:
            raise ValueError("No existe un inventario de oro configurado.")
        

        if self.pago_en_gramos:
            self.pago_en_gramos = self.pago_en_gramos or Decimal(0)
            if self.tipo_pago == "contado":
                inventario.gramos_disponibles_polvo = inventario.gramos_disponibles_polvo or Decimal(0)
                inventario.gramos_disponibles_polvo -= self.pago_en_gramos
            elif self.tipo_pago == "credito" and self.cliente:
                self.cliente.deuda_gramos_oro = self.cliente.deuda_gramos_oro or Decimal(0)
                self.cliente.deuda_gramos_oro -= self.pago_en_gramos
                self.cliente.save()

                

        # Revertir pagos en moneda
        if self.forma_pago == "moneda":
            self.monto_en_dolares = self.monto_en_dolares or Decimal(0)
            if self.tipo_pago == "contado" and self.caja:
                with transaction.atomic():
                    caja_obj = self.caja.__class__.objects.select_for_update().get(pk=self.caja.pk)
                    caja_obj.balance_actual = caja_obj.balance_actual or Decimal(0)
                    caja_obj.balance_actual -= self.monto_en_dolares
                    caja_obj.save()
                    logger.info(f"Balance caja DESPUÉS: {caja_obj.balance_actual}")

                   

                # Revertir el total generado en dólares del cliente
            if self.cliente:
                self.cliente.total_generado_dolares = self.cliente.total_generado_dolares or Decimal(0)
                print(f"Antes de restar total generado: {self.cliente.total_generado_dolares}")
                self.cliente.total_generado_dolares -= self.monto_en_dolares
                print(f"Después de restar total generado: {self.cliente.total_generado_dolares}")
                self.cliente.save()

            if self.tipo_pago == "credito" and self.cliente:
                self.cliente.deuda_total = self.cliente.deuda_total or Decimal(0)
                self.cliente.deuda_total -= self.monto_en_dolares
                self.cliente.save()

        inventario.save()
        super().delete(*args, **kwargs)

    def __str__(self):
            return f"{self.origen} -> {self.destino} ({self.horas_tramo} minutos)"

    class Meta:
            verbose_name = "Tramo de Vuelo"
            verbose_name_plural = "Tramos de Vuelo"