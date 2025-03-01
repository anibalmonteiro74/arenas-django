from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from registro_vuelos.models.inventarios import InventarioOro
from registro_vuelos.models.barras import Barra
from registro_vuelos.models import Cliente, HistorialTransacciones, CajaChica, MovimientoCaja
from registro_vuelos.forms import AbonoForm
from decimal import Decimal
from .forms import FundirBarraForm, VenderBarraForm
from django.db.models import Prefetch
from django.http import JsonResponse
from registro_vuelos.models.avion import Avion
from datetime import datetime
from .models import Vuelo
from registro_vuelos.models.tramovuelo import TramoVuelo
from registro_vuelos.forms import TramoVueloForm
from registro_vuelos.models.empleados import Empleado, PagoEmpleado, SaldoEmpleado
from registro_vuelos.forms import RegistrarPagoForm

def fundir_barras(request):
    inventario = InventarioOro.objects.first()
    if not inventario:
        messages.error(request, "No se encontró un inventario configurado.")
        return redirect("inventario_list")

    if request.method == "POST":
        form = FundirBarraForm(request.POST)
        if form.is_valid():
            peso_real = form.cleaned_data["peso_real"]
            ley = form.cleaned_data["ley"]
            ajuste = form.cleaned_data["ajuste"]

            try:
                barra = inventario.fundir_a_barra(peso_real=peso_real, ley=ley, ajuste=ajuste)
                messages.success(request, f"Barra {barra.codigo} generada exitosamente.")
                return redirect("inventario_list")
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = FundirBarraForm()

    return render(request, "fundir_barras.html", {"form": form, "inventario": inventario})

def vender_barra(request, barra_id):
    barra = get_object_or_404(Barra, id=barra_id)

    if request.method == "POST":
        form = VenderBarraForm(request.POST)
        if form.is_valid():
            precio_por_gramo = form.cleaned_data["precio_por_gramo"]

            try:
                ingreso = barra.vender(precio_por_gramo=precio_por_gramo)
                messages.success(request, f"Barra {barra.codigo} vendida por ${ingreso:.2f}.")
                return redirect("inventario_list")
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = VenderBarraForm()

    return render(request, "vender_barra.html", {"form": form, "barra": barra})

def registrar_abono(request):
    if request.method == 'POST':
        form = AbonoForm(request.POST)
        if form.is_valid():
            # Asegúrate de obtener el ID del cliente
            cliente = form.cleaned_data['cliente']  # Ya devuelve un objeto Cliente
            tipo_abono = form.cleaned_data['tipo_abono']
            monto = form.cleaned_data['monto']
            tasa_conversion = form.cleaned_data.get('tasa_conversion')
            caja_id = form.cleaned_data.get('caja_chica')  # Nueva lógica para caja chica
            print(f"ID de la caja seleccionada: {caja_id}")

            try:
                # Lógica para validar el abono según el tipo seleccionado
                if tipo_abono == 'gramos':
                    if monto > cliente.deuda_gramos_oro:
                        messages.error(request, "El abono no puede exceder la deuda total en gramos de oro.")
                        return redirect('admin:registro_vuelos_cliente_changelist')

                    # Actualizar deuda en gramos y el inventario
                    cliente.deuda_gramos_oro -= monto
                    cliente.total_generado_gramos += monto

                    # Actualizar inventario de oro
                    inventario = InventarioOro.objects.first()
                    if not inventario:
                        messages.error(request, "No se encontró un inventario configurado. Abono no procesado.")
                        return redirect('admin:registro_vuelos_cliente_changelist')

                    inventario.gramos_por_cobrar_polvo -= monto
                    inventario.gramos_disponibles_polvo += monto
                    inventario.save()

                    # Registrar en el historial
                    HistorialTransacciones.objects.create(
                        cliente=cliente,
                        tipo='abono_gramos',
                        monto=monto,
                        descripcion="Abono en gramos de oro"
                    )

                elif tipo_abono == 'moneda':
                    # Validar que la tasa de conversión sea válida
                    if not tasa_conversion or Decimal(tasa_conversion) <= 0:
                        messages.error(request, "Debe ingresar una tasa de conversión válida.")
                        return redirect('admin:registro_vuelos_cliente_changelist')

                    # Realizar el cálculo del monto convertido
                    abono_dolares = monto / Decimal(tasa_conversion)

                    # Validar que el abono no exceda la deuda
                    if abono_dolares > cliente.deuda_total:
                        messages.error(request, "El abono no puede exceder la deuda total en dólares.")
                        return redirect('admin:registro_vuelos_cliente_changelist')

                    # Actualizar valores del cliente
                    cliente.deuda_total -= abono_dolares
                    cliente.total_generado_dolares += abono_dolares
                    cliente.save()

                    # Actualizar caja chica
                    caja = get_object_or_404(CajaChica, id=caja_id.id if isinstance(caja_id, CajaChica) else caja_id)
                    

                    MovimientoCaja.objects.create(
                        caja=caja,  # Pasamos el objeto completo de la caja chica
                        tipo='ingreso',  # El tipo de movimiento es ingreso
                        monto=abono_dolares,  # Monto del abono en dólares
                        motivo="Abono registrado",  # Motivo genérico para el movimiento
                        nota=f"Abono registrado para {cliente.nombre}"  # Nota personalizada
                    )    

                    # Registrar en el historial
                    HistorialTransacciones.objects.create(
                        cliente=cliente,
                        tipo='abono_moneda',
                        monto=abono_dolares,
                        descripcion=f"Abono en moneda: {monto} (Tasa: {tasa_conversion or 'N/A'})"
                    )

                # Guardar los cambios en el cliente
                cliente.save()
                messages.success(request, "Abono registrado exitosamente.")
                return redirect('admin:registro_vuelos_cliente_changelist')  # Redirige al listado de clientes

            except Exception as e:
                messages.error(request, f"Error al procesar el abono: {str(e)}")
                return redirect('admin:registro_vuelos_cliente_changelist')
        else:
            messages.error(request, "Formulario inválido. Por favor, verifica los datos ingresados.")

    else:
        form = AbonoForm()

    return render(request, 'registro_vuelos/registrar_abono.html', {'form': form})

def cliente_detalle(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    historial = HistorialTransacciones.objects.filter(cliente=cliente).order_by("-fecha")
    transacciones = cliente.transacciones.order_by('-fecha')  # Historial de transacciones

    return render(request, 'registro_vuelos/cliente_detalle.html', {'cliente': cliente, 'transacciones': transacciones})

def clientes(request):
    """
    Vista para listar todos los clientes junto con su historial de transacciones.
    """
    clientes = Cliente.objects.prefetch_related(
        Prefetch('historialtransacciones_set', to_attr='transacciones')
    )

    return render(request, 'registro_vuelos/clientes.html', {'clientes': clientes})

def total_horometro_por_avion(request, avion_id):
    """Devuelve cuánto ha volado un avión en un rango de fechas."""
    try:
        avion = Avion.objects.get(id=avion_id)
        fecha_inicio = request.GET.get("fecha_inicio", "2000-01-01")
        fecha_fin = request.GET.get("fecha_fin", datetime.today().strftime("%Y-%m-%d"))

        total = avion.total_horometro_en_periodo(fecha_inicio, fecha_fin)

        return JsonResponse({"avion": avion.matricula, "total_horometro": float(total)})
    except Avion.DoesNotExist:
        return JsonResponse({"error": "Avión no encontrado"}, status=404)
    
def get_horometro(request):
    avion_id = request.GET.get("avion_id")
    if avion_id:
        try:
            avion = Avion.objects.get(id=avion_id)
            return JsonResponse({"horometro": avion.obtener_ultimo_horometro()})
        except Avion.DoesNotExist:
            return JsonResponse({"error": "Avión no encontrado"}, status=404)
    return JsonResponse({"error": "No se proporcionó avion_id"}, status=400)

def obtener_horometro(request):
    avion_id = request.GET.get('avion_id')

    if not avion_id:
        return JsonResponse({'error': 'No se proporcionó un ID de avión'}, status=400)

    try:
        avion = Avion.objects.get(id=avion_id)
        return JsonResponse({'horometro': avion.obtener_ultimo_horometro()})
    except Avion.DoesNotExist:
        return JsonResponse({'error': 'Avión no encontrado'}, status=404)

def historial_horometro(request, matricula):
    matricula = matricula.replace("%20", " ")  

    vuelos = Vuelo.objects.filter(avion__matricula=matricula).order_by("fecha", "id")

    print("Matrícula recibida:", matricula)
    print("Total de vuelos enviados a la plantilla:", vuelos.count())

    horometro = 0
    historial = []

    for vuelo in vuelos:
        # Obtener los tramos de vuelo asociados
        tramos = TramoVuelo.objects.filter(vuelo=vuelo)

        # Sumar el incremento del horómetro de cada tramo
        incremento_horometro = sum(tramo.horometro_fin - tramo.horometro_inicio for tramo in tramos)

        horometro += incremento_horometro  # Acumular el horómetro total

        historial.append({
            "vuelo": vuelo,
            "numero_factura": vuelo.numero_factura,  # Número de factura
            "incremento_horometro": round(incremento_horometro, 2),  # Incremento en este vuelo
            "horometro_acumulado": round(horometro, 2)  # Horómetro acumulado
        })

        print(f"Vuelo {vuelo.id} - Factura: {vuelo.numero_factura} - Fecha: {vuelo.fecha} - Incremento Horómetro: {round(incremento_horometro, 2)} - Horómetro Acumulado: {round(horometro, 2)}")

    return render(request, "registro_vuelos/historial_horometro.html", {"historial": historial})

def editar_tramo(request, tramo_id):
    tramo = get_object_or_404(TramoVuelo, pk=tramo_id)

    if request.method == 'POST':
        form = TramoVueloForm(request.POST, instance=tramo)
        if form.is_valid():
            tramo_anterior = TramoVuelo.objects.get(pk=tramo.pk)  # Obtener datos antes del cambio
            
            # ✅ 1. RESTAR VALORES ANTERIORES
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

            # ✅ 2. GUARDAR EL NUEVO VALOR
            form.save()

            # ✅ 3. APLICAR LOS NUEVOS VALORES
            if tramo.forma_pago == "Gramos":
                if tramo.cliente:
                    tramo.cliente.gramos += tramo.pago_en_gramos
                    tramo.cliente.save(update_fields=['gramos'])

                if tramo.inventario_oro:
                    tramo.inventario_oro.gramos_disponibles -= tramo.pago_en_gramos
                    tramo.inventario_oro.save(update_fields=['gramos_disponibles'])

            elif tramo.forma_pago == "Moneda":
                if tramo.cliente:
                    tramo.cliente.deuda_total += tramo.monto_en_dolares
                    tramo.cliente.save(update_fields=['deuda_total'])

                if tramo.caja:
                    tramo.caja.balance_actual += tramo.monto_en_dolares
                    tramo.caja.save(update_fields=['balance_actual'])

            return redirect('detalle_vuelo', vuelo_id=tramo.vuelo.id)
    
    else:
        form = TramoVueloForm(instance=tramo)

    return render(request, 'editar_tramo.html', {'form': form, 'tramo': tramo})

def registrar_pago(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    if request.method == 'POST':
        form = RegistrarPagoForm(request.POST)
        if form.is_valid():
            horas_a_pagar = form.cleaned_data['horas_a_pagar']
            tarifa_por_hora = form.cleaned_data['tarifa_por_hora']
            tipo_pago = form.cleaned_data['tipo_pago']
            descripcion = form.cleaned_data['descripcion']
            
            # Obtener o crear saldo para el empleado
            saldo, created = SaldoEmpleado.objects.get_or_create(empleado=empleado)
            
            # Validar horas disponibles según tipo de pago
            horas_disponibles = 0
            if tipo_pago == 'por_hora':
                horas_disponibles = saldo.horas_pendientes_por_hora
            elif tipo_pago == 'por_destino':
                horas_disponibles = saldo.horas_pendientes_por_destino
            elif tipo_pago == 'colaboracion':
                horas_disponibles = saldo.horas_pendientes_colaboracion
            
            if horas_a_pagar > horas_disponibles:
                messages.error(request, f"No se pueden pagar {horas_a_pagar} horas cuando solo hay {horas_disponibles} pendientes")
                return redirect('registrar_pago', empleado_id=empleado_id)
            
            # Calcular monto total
            monto = horas_a_pagar * tarifa_por_hora
            
            # Registrar el pago
            pago = PagoEmpleado.objects.create(
                empleado=empleado,
                tipo_pago=tipo_pago,
                horas_pagadas=horas_a_pagar,
                tarifa_por_hora=tarifa_por_hora,
                monto_pagado=monto,
                descripcion=descripcion
            )
            
            # Actualizar saldo según tipo de pago
            if tipo_pago == 'por_hora':
                saldo.total_horas_pagadas_por_hora += horas_a_pagar
            elif tipo_pago == 'por_destino':
                saldo.total_horas_pagadas_por_destino += horas_a_pagar
            elif tipo_pago == 'colaboracion':
                saldo.total_horas_pagadas_colaboracion += horas_a_pagar
                
            saldo.actualizar_saldo()  # Llamar al método que recalcula los valores pendientes
            
            messages.success(request, f"Pago registrado exitosamente: ${monto} por {horas_a_pagar} horas")
            return redirect('detalle_empleado', empleado_id=empleado_id)
    else:
        form = RegistrarPagoForm()
    
    context = {
        'empleado': empleado,
        'form': form,
        'saldo': SaldoEmpleado.objects.filter(empleado=empleado).first(),
    }
    
    return render(request, 'registro_vuelos/registrar_pago.html', context)

def detalle_empleado(request, empleado_id):
    empleado = get_object_or_404(Empleado, id=empleado_id)
    
    # Obtener todos los vuelos donde ha participado
    vuelos_piloto = Vuelo.objects.filter(piloto=empleado)
    vuelos_copiloto = Vuelo.objects.filter(copiloto=empleado)
    
    # Obtener historial de pagos
    pagos = PagoEmpleado.objects.filter(empleado=empleado).order_by('-fecha_pago')
    
    # Obtener saldo actual
    saldo = SaldoEmpleado.objects.filter(empleado=empleado).first()
    
    context = {
        'empleado': empleado,
        'vuelos_piloto': vuelos_piloto,
        'vuelos_copiloto': vuelos_copiloto,
        'pagos': pagos,
        'saldo': saldo,
        'total_vuelos': vuelos_piloto.count() + vuelos_copiloto.count()
    }
    
    return render(request, 'registro_vuelos/detalle_empleado.html', context)