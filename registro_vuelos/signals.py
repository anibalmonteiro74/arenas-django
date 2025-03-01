from django.db.models.signals import post_save, pre_delete
from django.db.models.signals import post_delete
from django.db.models.signals import pre_save
from django.dispatch import receiver
from decimal import Decimal
from registro_vuelos.models.tramovuelo import TramoVuelo
from registro_vuelos.models.inventarios import InventarioOro
from registro_vuelos.models.vuelo import Vuelo
from registro_vuelos.models import MovimientoCaja, MovimientoGasto
from registro_vuelos.models.facturas import SerieFactura
import logging


logger = logging.getLogger(__name__)



@receiver(pre_delete, sender=Vuelo)
def manejar_vuelo_eliminado(sender, instance, **kwargs):
    """
    Maneja la lógica antes de eliminar un vuelo.
    - Resta horas al piloto y copiloto.
    """
    instance.actualizar_horas_y_costos(eliminar=True)



@receiver(pre_delete, sender=Vuelo)
def revertir_montos_y_acumulados_al_eliminar(sender, instance, **kwargs):
    """
    Revertir los cambios en el inventario, deudas de clientes y cajas al eliminar un vuelo.
    """
    inventario = InventarioOro.objects.first()
    if not inventario:
        raise ValueError("No se encontró un inventario de oro configurado.")

    # Validar que los valores en el inventario no sean None
    inventario.gramos_disponibles_polvo = inventario.gramos_disponibles_polvo or Decimal(0)
    inventario.gramos_por_cobrar_polvo = inventario.gramos_por_cobrar_polvo or Decimal(0)

    logger.info(f"Inventario inicial: {inventario.gramos_disponibles_polvo} disponibles, {inventario.gramos_por_cobrar_polvo} por cobrar.")

    # Iterar sobre los tramos del vuelo
    for tramo in instance.tramos_vuelo.all():
        # Revertir acumulados en gramos si aplica
        tramo.pago_en_gramos = tramo.pago_en_gramos or Decimal(0)
        tramo.monto_en_dolares = tramo.monto_en_dolares or Decimal(0)
        if tramo.tipo_pago == "contado" and tramo.forma_pago == "gramos":
            inventario.gramos_disponibles_polvo -= tramo.pago_en_gramos
            if tramo.cliente:
                tramo.cliente.total_generado_gramos -= tramo.pago_en_gramos
                tramo.cliente.save()
        if tramo.forma_pago == "moneda" and tramo.tipo_pago == "contado" and tramo.cliente:
           tramo.cliente.total_generado_dolares -= tramo.monto_en_dolares
           tramo.cliente.save()                
        elif tramo.tipo_pago == "credito" and tramo.forma_pago == "gramos" and tramo.cliente:
            tramo.cliente.deuda_gramos_oro = tramo.cliente.deuda_gramos_oro or Decimal(0)
            inventario.gramos_por_cobrar_polvo -= tramo.pago_en_gramos
            tramo.cliente.deuda_gramos_oro -= tramo.pago_en_gramos
            tramo.cliente.save()

        # Revertir acumulados en dólares si aplica
        tramo.monto_en_dolares = tramo.monto_en_dolares or Decimal(0)
        if tramo.forma_pago == "moneda":
            if tramo.forma_pago == "moneda" and tramo.tipo_pago == "contado" and tramo.caja:
                
                    tramo.caja.balance_actual -= Decimal(tramo.monto_en_dolares)
                    tramo.caja.save()
            elif tramo.tipo_pago == "credito" and tramo.cliente:
                tramo.cliente.deuda_total = tramo.cliente.deuda_total or Decimal(0)
                tramo.cliente.deuda_total -= tramo.monto_en_dolares
                tramo.cliente.save()

    # Guardar los cambios en el inventario
    inventario.save()
    logger.info(f"Inventario final: {inventario.gramos_disponibles_polvo} disponibles, {inventario.gramos_por_cobrar_polvo} por cobrar después de eliminar el vuelo.")


@receiver(post_delete, sender=MovimientoCaja)
def actualizar_balance_caja_al_eliminar(sender, instance, **kwargs):
    # Si es un movimiento de ingreso
    if instance.tipo == "ingreso":
        instance.caja.balance_actual -= instance.monto

    # Si es un movimiento de egreso
    elif instance.tipo == "egreso":
        # Devuelve el monto al balance de la caja
        instance.caja.balance_actual += instance.monto

        # Resta el monto del balance de la cuenta de gasto asociada
        if instance.cuenta_gasto:
            instance.cuenta_gasto.balance_total -= instance.monto
            instance.cuenta_gasto.save()

    # Si es un movimiento de transferencia
    elif instance.tipo == "transferencia" and instance.caja_destino:
        # Revertir el impacto en ambas cajas
        instance.caja.balance_actual += instance.monto
        instance.caja_destino.balance_actual -= instance.monto
        instance.caja_destino.save()

    # Guarda el balance actualizado de la caja
    instance.caja.save()


@receiver(post_delete, sender=MovimientoGasto)
def actualizar_balance_gasto_al_eliminar(sender, instance, **kwargs):
    # Resta el monto del balance total de la cuenta de gasto al eliminar el movimiento
    if instance.cuenta:
        instance.cuenta.balance_total -= instance.monto
        instance.cuenta.save()

@receiver(post_save, sender=Vuelo)
def manejar_vuelo_creado(sender, instance, created, **kwargs):
    if created:
        # Actualizar horas y costos del piloto
        instance.actualizar_horas_y_costos(eliminar=False)

        # Verificar inventario
        inventario = InventarioOro.objects.select_for_update().first()
        if not inventario:
            raise ValueError("No se encontró un inventario de oro configurado.")

        inventario.gramos_disponibles_polvo = inventario.gramos_disponibles_polvo or Decimal(0)
        inventario.gramos_por_cobrar_polvo = inventario.gramos_por_cobrar_polvo or Decimal(0)

        # Obtener la primera serie de facturación disponible
        serie = SerieFactura.objects.first()
        if not serie:
            raise ValueError("No existe ninguna serie configurada. Crea una serie en el sistema.")

        # Generar el número de factura
        numero_factura_vuelo = serie.generar_numero_factura()
        instance.numero_factura = f"{numero_factura_vuelo}-0"
        instance.save()

        # Procesar los tramos del vuelo
        for index, tramo in enumerate(instance.tramos_vuelo.all(), start=1):
            tramo.pago_en_gramos = tramo.pago_en_gramos or Decimal(0)
            tramo.monto_en_dolares = tramo.monto_en_dolares or Decimal(0)
            
            # Acumular pagos en gramos
            if tramo.forma_pago == "gramos":
                if tramo.tipo_pago == "contado":
                    # Actualizar inventario
                    inventario.gramos_disponibles_polvo += tramo.pago_en_gramos
                    
                    # Acumular al total generado del cliente si existe
                    if tramo.cliente:
                        cliente_actual = tramo.cliente
                        cliente_actual.total_generado_gramos += tramo.pago_en_gramos
                        cliente_actual.save()

                elif tramo.tipo_pago == "credito" and tramo.cliente:
                    # Actualizar inventario por cobrar
                    inventario.gramos_por_cobrar_polvo += tramo.pago_en_gramos
                    
                    # Acumular a la deuda del cliente
                    cliente_actual = tramo.cliente
                    cliente_actual.deuda_gramos_oro += tramo.pago_en_gramos
                    cliente_actual.save()

            # Acumular pagos en moneda
            elif tramo.forma_pago == "moneda":
                if tramo.tipo_pago == "contado" and tramo.caja:
                    # Actualizar caja
                    tramo.caja.balance_actual += tramo.monto_en_dolares
                    tramo.caja.save()
                    
                    # Acumular al total generado del cliente si existe
                    if tramo.cliente:
                        cliente_actual = tramo.cliente
                        cliente_actual.total_generado_dolares += tramo.monto_en_dolares
                        cliente_actual.save()
                        
                elif tramo.tipo_pago == "credito" and tramo.cliente:
                    # Acumular a la deuda del cliente
                    cliente_actual = tramo.cliente
                    cliente_actual.deuda_total += tramo.monto_en_dolares
                    cliente_actual.save()

            # Generar factura para cada tramo
            tramo.numero_factura = f"{numero_factura_vuelo}-{index}"
            tramo.save()

        # Guardar cambios en el inventario
        inventario.save()

@receiver(pre_save, sender=TramoVuelo)
def eliminar_valores_anteriores(sender, instance, **kwargs):
    """
    Antes de guardar un TramoVuelo, restamos el valor anterior 
    en clientes, caja chica e inventario de oro para evitar duplicaciones.
    """
    if instance.pk:  # Solo si el TramoVuelo ya existía antes
        tramo_anterior = TramoVuelo.objects.filter(pk=instance.pk).first()
        if tramo_anterior:
            # ✅ RESTAR LOS VALORES ANTERIORES ANTES DE GUARDAR
            if tramo_anterior.forma_pago == "Gramos":
                if tramo_anterior.cliente:
                    tramo_anterior.cliente.gramos -= tramo_anterior.pago_en_gramos
                    tramo_anterior.cliente.save(update_fields=['gramos'])
                
                if tramo_anterior.inventario_oro:
                    tramo_anterior.inventario_oro.gramos_disponibles += tramo_anterior.pago_en_gramos
                    tramo_anterior.inventario_oro.save(update_fields=['gramos_disponibles'])

            elif tramo_anterior.forma_pago == "Moneda":
                if tramo_anterior.cliente:
                    tramo_anterior.cliente.deuda_total -= tramo_anterior.monto_en_dolares
                    tramo_anterior.cliente.save(update_fields=['deuda_total'])

                if tramo_anterior.caja:
                    tramo_anterior.caja.balance_actual -= tramo_anterior.monto_en_dolares
                    tramo_anterior.caja.save(update_fields=['balance_actual'])

#@receiver(post_save, sender=TramoVuelo)
#def agregar_nuevos_valores(sender, instance, created, **kwargs):
    #"""
    #Después de guardar un TramoVuelo, agregamos los nuevos valores
    #en clientes, caja chica e inventario de oro.
    #"""
    #if created:  # Solo suma si el tramo es nuevo
        #if instance.forma_pago == "Gramos":
            #if instance.cliente:
                #instance.cliente.gramos += instance.pago_en_gramos
                #instance.cliente.save(update_fields=['gramos'])

            #if instance.inventario_oro:
                #instance.inventario_oro.gramos_disponibles -= instance.pago_en_gramos
                #instance.inventario_oro.save(update_fields=['gramos_disponibles'])

        #elif instance.forma_pago == "Moneda":
            #if instance.cliente:
                #instance.cliente.deuda_total += instance.monto_en_dolares
                #instance.cliente.save(update_fields=['deuda_total'])

            #if instance.caja:
                #instance.caja.balance_actual += instance.monto_en_dolares
                #instance.caja.save(update_fields=['balance_actual'])        

        

