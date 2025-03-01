from django import forms
from registro_vuelos.models.barras import Barra  # Importación actualizada
from registro_vuelos.models import Cliente, CajaChica
from registro_vuelos.models import TramoVuelo
from registro_vuelos.models.empleados import PagoEmpleado



class TramoVueloForm(forms.ModelForm):
    class Meta:
        model = TramoVuelo
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Si hay un vuelo asociado y no es un formulario para un objeto existente
        if self.instance and self.instance.vuelo and self.instance.vuelo.avion and not self.instance.pk:
            self.fields["horometro_inicio"].initial = self.instance.vuelo.avion.obtener_ultimo_horometro()
            
        # Siempre añadir el placeholder con el último horómetro
        if self.instance and self.instance.vuelo and self.instance.vuelo.avion:
            ultimo_horometro = self.instance.vuelo.avion.obtener_ultimo_horometro()
            self.fields["horometro_inicio"].widget.attrs["placeholder"] = f"Último: {ultimo_horometro}"

class FundirBarraForm(forms.Form):
    peso_real = forms.DecimalField(
        max_digits=10, decimal_places=2, label="Peso Real (g)",
        required=True, min_value=0.01
    )
    ley = forms.DecimalField(
        max_digits=5, decimal_places=3, label="Ley (Pureza %)",
        required=True, min_value=0.001, max_value=999.999
    )
    ajuste = forms.DecimalField(
        max_digits=10, decimal_places=2, label="Ajuste (Opcional)",
        required=False, initial=0
    )

class VenderBarraForm(forms.Form):
    precio_por_gramo = forms.DecimalField(
        max_digits=10, decimal_places=2, label="Precio por Gramo (USD)",
        required=True, min_value=0.01
    )

class AbonoForm(forms.Form):
    cliente = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        label="Cliente",
        help_text="Seleccione el cliente al que desea realizar el abono.",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    tipo_abono = forms.ChoiceField(
        choices=[('moneda', 'Moneda'), ('gramos', 'Gramos')],
        label="Tipo de Abono",
        help_text="Seleccione si el abono será en moneda o en gramos de oro.",
        widget=forms.Select(attrs={'class': 'form-select'}),
    )
    monto = forms.DecimalField(
        max_digits=15,
        decimal_places=2,
        label="Monto",
        min_value=0.01,
        help_text="Ingrese el monto a abonar. Debe ser positivo.",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    tasa_conversion = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Tasa de Conversión",
        help_text="Ingrese la tasa de conversión si el abono es en moneda.",
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
    )
    caja_chica = forms.ModelChoiceField(
        queryset=CajaChica.objects.all(),
        label="Caja Chica",
        help_text="Seleccione la caja chica donde se registrará el abono.",
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'}),
    )


    def clean_tipo_abono(self):
        tipo_abono = self.cleaned_data.get("tipo_abono")
        if not tipo_abono:
            raise forms.ValidationError("Debe seleccionar un tipo de abono.")
        return tipo_abono

    def clean_tasa_conversion(self):
        tipo_abono = self.cleaned_data.get("tipo_abono")
        tasa_conversion = self.cleaned_data.get("tasa_conversion")

        if tipo_abono == "moneda" and (not tasa_conversion or tasa_conversion <= 0):
            raise forms.ValidationError("Debe ingresar una tasa de conversión válida para abonos en moneda.")
        return tasa_conversion

    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get("cliente")
        tipo_abono = cleaned_data.get("tipo_abono")
        monto = cleaned_data.get("monto")
        tasa_conversion = cleaned_data.get("tasa_conversion")

        # Validar el cliente
        if not cliente:
            raise forms.ValidationError("Debe seleccionar un cliente válido.")

        # Validar abono en moneda
        if tipo_abono == "moneda":
            abono = monto / tasa_conversion
            if cliente.deuda_total < abono:
                raise forms.ValidationError(
                    f"El abono en moneda ({abono:.2f}) excede la deuda del cliente (${cliente.deuda_total:.2f})."
                )

        # Validar abono en gramos
        elif tipo_abono == "gramos":
            if cliente.deuda_gramos_oro < monto:
                raise forms.ValidationError(
                    f"El abono en gramos ({monto:.2f}g) excede la deuda del cliente ({cliente.deuda_gramos_oro:.2f}g)."
                )

        return cleaned_data
    
class RegistrarPagoForm(forms.Form):
    horas_a_pagar = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    tarifa_por_hora = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)
    tipo_pago = forms.ChoiceField(choices=PagoEmpleado.TIPO_PAGO_CHOICES)
    descripcion = forms.CharField(widget=forms.Textarea, required=False)    