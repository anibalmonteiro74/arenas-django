# admin.py
from django.contrib import admin
from django.urls import reverse
from django.db.models import Sum
from django.utils.html import format_html
from django import forms
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from django.contrib import messages
from registro_vuelos.models.avion import Avion
from registro_vuelos.models.clientes import Cliente, HistorialTransacciones
from registro_vuelos.models.destino import Destino
from registro_vuelos.models.empleados import Empleado, PagoEmpleado, SaldoEmpleado
from registro_vuelos.models.inventarios import InventarioOro
from registro_vuelos.models.tramovuelo import TramoVuelo
from registro_vuelos.models.trayectocosto import TrayectoCosto
from registro_vuelos.models.vuelo import Vuelo
from registro_vuelos.models.barras import Barra
from registro_vuelos.models.monedas import Moneda
from registro_vuelos.models.cajachica import CajaChica, MovimientoCaja, CuentaGasto, MovimientoGasto
from registro_vuelos.models.facturas import SerieFactura
from registro_vuelos.models import TramoVuelo
from registro_vuelos.forms import TramoVueloForm
admin.site.site_header = "Django administration"

class TramoVueloInline(admin.TabularInline):
    model = TramoVuelo
    form = TramoVueloForm  # 🔥 Aseguramos que usa el formulario con el placeholder
    extra = 1
    fields = (
        'origen', 'destino', 'horometro_inicio', 'horometro_fin',
        'horas_tramo', 'facturacion', 'cliente', 'forma_pago', 'moneda', 'caja', 'tasa_cambio',
        'pago_en_gramos', 'cantidad_moneda', 'monto_en_dolares',
        'tipo_pago', 'tipo_carga', 'descripcion_carga'
    )
    readonly_fields = ('horas_tramo', 'monto_en_dolares', 'horometro_info')

    class Media:
        js = ('admin/js/tramo_vuelo_validaciones.js',)

    def ultimo_horometro(self, obj):
        """Muestra el último horómetro registrado."""
        if obj and obj.vuelo and obj.vuelo.avion:
            return mark_safe(f"<strong>Último horómetro: {obj.vuelo.avion.obtener_ultimo_horometro()}</strong>")
        return "Avión no seleccionado"
    
    ultimo_horometro.short_description = "Último Horómetro"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        
        # Si hay un avión seleccionado, pre-rellenar el horómetro inicial
        if obj and obj.avion:
            horometro = obj.avion.obtener_ultimo_horometro()
            
            # Sobreescribir el método __init__ para manipular los datos iniciales
            original_init = formset.form.__init__
            
            def new_init(self, *args, **kwargs):
                initial = kwargs.get('initial', {})
                
                # Solo pre-rellenar si no hay datos existentes
                if not kwargs.get('instance'):
                    initial['horometro_inicio'] = horometro
                    kwargs['initial'] = initial
                
                original_init(self, *args, **kwargs)
            
            formset.form.__init__ = new_init
        
        return formset    

    # 🔥 Aquí agregamos solo la lógica del placeholder sin afectar lo demás
    def formfield_for_dbfield(self, db_field, request, **kwargs):
        formfield = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == "horometro_inicio":
            obj = getattr(request, "obj", None)  # Obtener el objeto actual
            if obj and obj.avion:  # Si el vuelo tiene un avión asignado
                ultimo_horometro = obj.avion.obtener_ultimo_horometro()
                formfield.widget.attrs["placeholder"] = f"Último horómetro: {ultimo_horometro}"
        return formfield

    def horometro_info(self, obj):
        if obj and obj.vuelo and obj.vuelo.avion:
            return mark_safe(f"<strong>Último horómetro: {obj.vuelo.avion.obtener_ultimo_horometro()}</strong>")
        return "Selecciona un avión"
    
    horometro_info.short_description = "Último Horómetro"    

@admin.register(Vuelo)
class VueloAdmin(admin.ModelAdmin):
    class Media:
        js = ("admin/js/horometro_update.js", "admin/js/tramo_vuelo_validaciones.js", "admin/js/horometro_autocomplete.js")
        

    list_display = (
        "id", "avion", "piloto", "copiloto",
        "tipo_cobro", "horas_totales", "fecha", "bitacora", "numero_factura"
    )  # 🚀 Se usa "mostrar_ultimo_horometro"

    search_fields = ("numero_factura", "avion__matricula", "piloto__nombre", "copiloto__nombre")
    list_filter = ("tipo_cobro", "avion")

    inlines = [TramoVueloInline]

    fields = (
        "avion",  
        "piloto", "copiloto", "tipo_cobro", "fecha",
        "bitacora", "serie_factura", "numero_factura", "mostrar_ultimo_horometro"
    )

    readonly_fields = ("numero_factura", "mostrar_ultimo_horometro")  # 🚀 Se mantiene como solo lectura

    def mostrar_ultimo_horometro(self, obj):
        """Muestra el último horómetro registrado del avión seleccionado."""
        if obj and obj.avion:
            return f"{obj.avion.obtener_ultimo_horometro()}"
        return "Selecciona un avión para ver el horómetro."

    mostrar_ultimo_horometro.short_description = "Último Horómetro Registrado"

    def horometro_acumulado(self, obj):
        """Calcula el horómetro acumulado en el momento del vuelo."""
        vuelos = Vuelo.objects.filter(avion=obj.avion, fecha__lte=obj.fecha).order_by("fecha", "id")
        horometro = 0
        for vuelo in vuelos:
            horometro += vuelo.horas_totales
            if vuelo.id == obj.id:
                return round(horometro, 2)  # Devolver solo hasta el vuelo actual
        return "Error"

    horometro_acumulado.short_description = "Horómetro Acumulado"

    def gramos_pagados(self, obj):
        total_gramos = obj.tramos_vuelo.aggregate(Sum("pago_en_gramos"))["pago_en_gramos__sum"]
        return total_gramos or 0
    gramos_pagados.short_description = "Gramos Pagados"

    def total_monedas(self, obj):
        total_monedas = obj.tramos_vuelo.aggregate(Sum("monto_en_dolares"))["monto_en_dolares__sum"]
        return total_monedas or 0
    total_monedas.short_description = "Total en Moneda"

    def save_related(self, request, form, formsets, change):
        """
        Guarda las relaciones (tramos) pero delega cálculos al modelo `Vuelo`.
        """
        super().save_related(request, form, formsets, change)
        form.instance.save()  # Llama al save del modelo para manejar cálculos.

# 🔹 Filtro personalizado para diferenciar Facturas Principales y Subfacturas
class SubfacturaFilter(admin.SimpleListFilter):
    title = _("Tipo de Factura")
    parameter_name = "tipo_factura"

    def lookups(self, request, model_admin):
        return [
            ("principal", _("Facturas Principales")),
            ("subfactura", _("Subfacturas")),
        ]

    def queryset(self, request, queryset):
        if self.value() == "principal":
            return queryset.filter(numero_factura__regex=r"^[A-Z0-9]+$")
        elif self.value() == "subfactura":
            return queryset.filter(numero_factura__regex=r"^[A-Z0-9]+-\d+$")

class TramoVueloForm(forms.ModelForm):
    class Meta:
        model = TramoVuelo
        fields = '__all__'
              


@admin.register(TramoVuelo)
class TramoVueloAdmin(admin.ModelAdmin):
    
    form = TramoVueloForm
    list_display = ("numero_factura", "incremento_horometro", "vuelo", "origen", "destino", "facturacion", "cliente", "tipo_pago", "forma_pago", "pago_en_gramos", 'monto_en_dolares', "caja")
    search_fields = ("numero_factura", "vuelo__numero_factura", "vuelo__bitacora", "cliente__nombre")
    autocomplete_fields = ('vuelo',)

    # 🔹 Agregamos el nuevo filtro sin eliminar los que ya tienes
    list_filter = ("vuelo", "facturacion", "tipo_pago", "forma_pago", "caja", SubfacturaFilter)

    # Mostrar los campos en la interfaz de administración
    fields = (
        "vuelo", "ultimo_horometro_mensaje", "origen", "destino", "horometro_inicio", "horometro_fin", "horas_tramo",
        "facturacion", "cliente", "tipo_pago", "forma_pago", "pago_en_gramos", "moneda",
        'tasa_cambio', 'cantidad_moneda', 'monto_en_dolares', 'caja'
    )
    readonly_fields = ("ultimo_horometro_mensaje", "numero_factura",'horas_tramo', 'monto_en_dolares')

    class Media:
        js = ('admin/js/actions.js','admin/js/tramo_vuelo_validaciones.js')

    def ultimo_horometro_mensaje(self, obj):
        """Muestra el último horómetro registrado del avión seleccionado."""
        if obj.vuelo and obj.vuelo.avion:
            ultimo_horometro = obj.vuelo.avion.obtener_ultimo_horometro()
            return mark_safe(f"<strong>Último horómetro registrado: {ultimo_horometro}</strong>")
        return "No hay registros previos."

    ultimo_horometro_mensaje.short_description = "Último Horómetro Guardado"    

        
    def changelist_view(self, request, extra_context=None):
        """
        Inyectar el script en la lista de objetos.
        """
        extra_context = extra_context or {}
        extra_context['media'] = mark_safe(
            extra_context.get('media', '') +
            '<script src="https://127.0.0.1:8000/static/admin/js/tramo_vuelo_validaciones.js"></script>'
        )
        return super().changelist_view(request, extra_context)

    def add_view(self, request, form_url='', extra_context=None):
        """
        Inyectar el script en la vista de creación.
        """
        extra_context = extra_context or {}
        extra_context['media'] = mark_safe(
            extra_context.get('media', '') +
            '<script src="https://127.0.0.1:8000/static/admin/js/tramo_vuelo_validaciones.js"></script>'
        )
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Inyectar el script en la vista de edición.
        """
        extra_context = extra_context or {}
        extra_context['media'] = mark_safe(
            extra_context.get('media', '') +
            '<script src="https://127.0.0.1:8000/static/admin/js/tramo_vuelo_validaciones.js"></script>'
        )
        return super().change_view(request, object_id, form_url, extra_context)

        

def clean(self):
    cleaned_data = super().clean()
    forma_pago = cleaned_data.get('forma_pago')
    tipo_pago = cleaned_data.get('tipo_pago')
    caja = cleaned_data.get('caja')

    if forma_pago == "moneda" and tipo_pago == "contado" and not caja:
        raise forms.ValidationError("Debes seleccionar una caja cuando el pago es contado en moneda.")

    return cleaned_data

@admin.register(Avion)
class AvionAdmin(admin.ModelAdmin):
    list_display = ('matricula', 'modelo', 'capacidad_pasajeros', 'capacidad_carga', 'fabricante', 'fecha_registro', 'ver_historial_horometro')
    list_filter = ('fabricante',)
    search_fields = ('matricula', 'modelo', 'fabricante')

    def ver_historial_horometro(self, obj):
        """Genera un botón para ver el historial de horómetros de este avión."""
        url = reverse("historial_horometro", args=[obj.matricula])
        return format_html('<a class="button" href="{}" target="_blank">Ver Historial</a>', url)

    ver_historial_horometro.short_description = "Historial Horómetro"

# Crear un grupo para modelos relacionados con empleados
#class EmpleadosGroup(admin.ModelAdmin):
    #class Meta:
        #app_label = 'registro_vuelos'
        #verbose_name = _('Gestión de Empleados')
        #verbose_name_plural = _('Gestión de Empleados')


# Configurar el sitio admin para agrupar estos modelos
#admin.site.index_template = 'admin/custom_index.html'    

# Primero, crea clases inline para los pagos y saldos
class PagoEmpleadoInline(admin.TabularInline):
    model = PagoEmpleado
    extra = 0  # No mostrar formularios extra en blanco
    fields = ('fecha_pago', 'tipo_pago', 'horas_pagadas', 'tarifa_por_hora', 'monto_pagado', 'descripcion')
    readonly_fields = ('fecha_pago',)

class SaldoEmpleadoInline(admin.StackedInline):
    model = SaldoEmpleado
    can_delete = False  # No permitir eliminar el saldo
    fields = (
        ('horas_pendientes_por_hora', 'horas_pendientes_por_destino', 'horas_pendientes_colaboracion'),
        ('total_horas_pagadas_por_hora', 'total_horas_pagadas_por_destino', 'total_horas_pagadas_colaboracion'),
        'costo_pendiente_por_destino',
        'total_costo_pagado_por_destino',
    )
    readonly_fields = (
        'horas_pendientes_por_hora', 'horas_pendientes_por_destino', 'horas_pendientes_colaboracion',
        'total_horas_pagadas_por_hora', 'total_horas_pagadas_por_destino', 'total_horas_pagadas_colaboracion',
        'costo_pendiente_por_destino', 'total_costo_pagado_por_destino',
    )    

@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'fecha_ingreso', 'activo', 'horas_totales')
    list_filter = ('tipo', 'activo')
    search_fields = ('nombre',)

    readonly_fields = ('horas_totales', 'resumen_horas')

    # Agregar los inlines
    inlines = [SaldoEmpleadoInline, PagoEmpleadoInline]

    # Agregar esta línea para usar la plantilla personalizada
    change_form_template = 'admin/registro_vuelos/empleado/change_form.html'
    
    def resumen_horas(self, obj):
        if not obj.pk:  # Si es un objeto nuevo, no mostrar nada
            return ""
        
        html = f"""
        <div style="margin: 10px 0; padding: 10px; background-color: #f8f8f8; border: 1px solid #ddd; border-radius: 4px;">
            <h3 style="margin-top: 0;">Resumen de Horas</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <th style="text-align: left; padding: 8px; border-bottom: 1px solid #ddd;">Categoría</th>
                    <th style="text-align: right; padding: 8px; border-bottom: 1px solid #ddd;">Horas</th>
                </tr>
                <tr>
                    <td style="padding: 8px;">Por hora</td>
                    <td style="text-align: right; padding: 8px;">{obj.horas_por_hora}</td>
                </tr>
                <tr>
                    <td style="padding: 8px;">Por destino</td>
                    <td style="text-align: right; padding: 8px;">{obj.horas_por_destino}</td>
                </tr>
                <tr>
                    <td style="padding: 8px;">Por colaboración</td>
                    <td style="text-align: right; padding: 8px;">{obj.horas_colaboracion}</td>
                </tr>
                <tr style="font-weight: bold; background-color: #eee;">
                    <td style="padding: 8px;">TOTAL</td>
                    <td style="text-align: right; padding: 8px;">{obj.horas_totales}</td>
                </tr>
            </table>
            
            <h3 style="margin-top: 15px;">Información de Costos</h3>
            <p style="margin: 5px 0;">Costo acumulado por destino: ${obj.total_costo_por_destino}</p>
        </div>
        """
        return mark_safe(html)
    
    resumen_horas.short_description = 'Resumen de Horas Voladas'
    
    fieldsets = (
        (None, {
            'fields': ('nombre', 'tipo', 'fecha_ingreso', 'activo')
        }),
        ('Resumen', {
            'fields': ('resumen_horas',),
            'classes': ()  # Sin collapse para que siempre esté visible
        }),
        ('Detalles de Horas', {
            'fields': (
                'horas_por_hora', 
                'horas_por_destino', 
                'horas_colaboracion',
                'horas_totales',
                'total_costo_por_destino'
            ),
            'classes': ('collapse',)
        }),
    )

    def horas_pendientes_por_pagar(self, obj):
        try:
            saldo = obj.saldo
            return saldo.horas_pendientes_por_hora + saldo.horas_pendientes_por_destino + saldo.horas_pendientes_colaboracion
        except SaldoEmpleado.DoesNotExist:
            return "Sin saldo"
    
    def costo_pendiente_por_destino(self, obj):
        try:
            return obj.saldo.costo_pendiente_por_destino
        except SaldoEmpleado.DoesNotExist:
            return "Sin saldo"
    
    actions = ['registrar_pago_por_hora', 'registrar_pago_por_destino']
    
    def registrar_pago_por_hora(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Seleccione un solo empleado', level=messages.ERROR)
            return
        
        return redirect('registrar_pago', empleado_id=queryset.first().id)
    
    registrar_pago_por_hora.short_description = "Registrar pago por hora"

    def registrar_pago_por_destino(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, 'Seleccione un solo empleado', level=messages.ERROR)
            return
        
        return redirect('registrar_pago', empleado_id=queryset.first().id)
    
    registrar_pago_por_destino.short_description = "Registrar pago por destino"

@admin.register(Destino)
class DestinoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)

@admin.register(TrayectoCosto)
class TrayectoCostoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'origen', 'destino', 'costo_trayecto')
    search_fields = ('empleado__nombre', 'origen__nombre', 'destino__nombre')
    list_filter = ('origen', 'destino')

@admin.register(InventarioOro)
class InventarioOroAdmin(admin.ModelAdmin):
    list_display = (
        "gramos_disponibles_polvo",
        "gramos_por_cobrar_polvo",
        "gramos_ajustados_polvo",
        "precio_por_gramo",
        "valor_total_usd",
    )
    readonly_fields = ("gramos_ajustados_polvo", "valor_total_usd")
    search_fields = ("gramos_disponibles_polvo",)
    list_filter = ("precio_por_gramo",)

    actions = ["ajustar_fundicion"]

    def ajustar_fundicion(self, request, queryset):
        for inventario in queryset:
            gramos_ajustados = inventario.gramos_disponibles_polvo - 1  # Ejemplo de ajuste
            inventario.ajustar_polvo(gramos_ajustados)

@admin.register(Barra)
class BarraAdmin(admin.ModelAdmin):
    list_display = ("codigo", "peso", "ley", "gramos_puros", "fecha_generacion", "vendida", "precio_venta_usd")
    readonly_fields = ("gramos_puros",)
    search_fields = ("codigo",)
    list_filter = ("fecha_generacion", "vendida")

    actions = ["vender_barra"]

    def vender_barra(self, request, queryset):
        for barra in queryset:
            if not barra.vendida:
                barra.vender(precio_por_gramo=50)  # Precio por gramo como ejemplo

@admin.register(Moneda)
class MonedaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "simbolo")


@admin.register(CajaChica)
class CajaChicaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'balance_actual')
    actions = ['generar_reporte']

    def generar_reporte(self, request, queryset):
        # Código para generar reporte
        pass


@admin.register(MovimientoCaja)
class MovimientoCajaAdmin(admin.ModelAdmin):
    list_display = ('caja', 'tipo', 'monto', 'motivo', 'nota', 'caja_destino', 'cuenta_gasto', 'fecha')
    list_filter = ('tipo', 'fecha', 'caja', 'cuenta_gasto')  # Filtro adicional por cuenta de gasto
    search_fields = ('motivo', 'nota')


@admin.register(CuentaGasto)
class CuentaGastoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'balance_total', 'descripcion')
    search_fields = ('nombre', 'descripcion')


@admin.register(MovimientoGasto)
class MovimientoGastoAdmin(admin.ModelAdmin):
    list_display = ('cuenta', 'monto', 'motivo', 'nota', 'fecha')
    list_filter = ('cuenta', 'fecha')  # Nuevo filtro por cuenta de gasto
    search_fields = ('motivo', 'nota')

    actions = ['revertir_movimiento']

    def revertir_movimiento(self, request, queryset):
        for movimiento in queryset:
            movimiento.cuenta.balance_total -= movimiento.monto
            movimiento.cuenta.save()
            movimiento.delete()
    revertir_movimiento.short_description = "Revertir movimiento seleccionado"

@admin.register(HistorialTransacciones)
class HistorialTransaccionesAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'tipo', 'monto', 'fecha', 'descripcion')
    search_fields = ('cliente__nombre', 'tipo', 'descripcion')
    list_filter = ('tipo', 'fecha')

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "deuda_total",  # Deuda en dólares
        "deuda_gramos_oro",  # Deuda en gramos de oro
        "total_generado_dolares",  # NUEVO: Total generado en dólares
        "total_generado_gramos",  # NUEVO: Total generado en gramos de oro
    )

    search_fields = ("nombre",)
    list_filter = ("deuda_total", "deuda_gramos_oro")

    def changelist_view(self, request, extra_context=None):
        """
        Modifica la vista de lista de clientes para incluir un botón global.
        """
        extra_context = extra_context or {}
        extra_context['show_register_abono_button'] = True  # Activa el botón
        return super().changelist_view(request, extra_context)
    
@admin.register(SerieFactura)
class SerieFacturaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'numero_actual')

@admin.register(PagoEmpleado)
class PagoEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'fecha_pago', 'tipo_pago', 'horas_pagadas', 'tarifa_por_hora', 'monto_pagado')
    list_filter = ('tipo_pago', 'fecha_pago', 'empleado')
    search_fields = ('empleado__nombre', 'descripcion')
    date_hierarchy = 'fecha_pago'

    def get_model_info(self):
        info = super().get_model_info()
        info['verbose_name'] = "Empleados - Pagos"
        info['verbose_name_plural'] = "Empleados - Pagos"
        return info

@admin.register(SaldoEmpleado)
class SaldoEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('empleado', 'horas_pendientes_por_hora', 'horas_pendientes_por_destino', 
                    'horas_pendientes_colaboracion', 'costo_pendiente_por_destino')
    list_filter = ('empleado',)
    search_fields = ('empleado__nombre',)  

    def get_model_info(self):
        info = super().get_model_info()
        info['verbose_name'] = "Empleados - Saldos"
        info['verbose_name_plural'] = "Empleados - Saldos"
        return info      