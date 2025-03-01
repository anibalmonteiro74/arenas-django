from django.db import models


# Modelo para los empleados (pilotos y copilotos)
class Empleado(models.Model):
    TIPO_EMPLEADO_CHOICES = [
        ('piloto', 'Piloto'),
        ('copiloto', 'Copiloto'),
        ('otro', 'Otro'),  # Otros tipos de empleados
    ]
    nombre = models.CharField(max_length=100, verbose_name="Nombre completo")
    tipo = models.CharField(max_length=20, choices=TIPO_EMPLEADO_CHOICES, verbose_name="Tipo de empleado")
    fecha_ingreso = models.DateField(verbose_name="Fecha de ingreso")
    activo = models.BooleanField(default=True, verbose_name="¿Está activo?")

    # Horas de vuelo discriminadas
    horas_por_hora = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Horas acumuladas por hora"
    )
    horas_por_destino = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Horas acumuladas por destino"
    )
    horas_colaboracion = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Horas acumuladas por colaboración"
    )
    horas_totales = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Total de horas voladas", editable=False
    )
    total_costo_por_destino = models.DecimalField(
        max_digits=10, decimal_places=2, default=0, verbose_name="Costo acumulado por destino"
    )

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"
    
    class Meta:
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"
    
class PagoEmpleado(models.Model):
    TIPO_PAGO_CHOICES = [
        ('por_hora', 'Pago por Hora'),
        ('por_destino', 'Pago por Destino'),
        ('colaboracion', 'Pago por Colaboración'),
        ]
        
    empleado = models.ForeignKey(Empleado, on_delete=models.CASCADE, related_name='pagos')
    fecha_pago = models.DateField(auto_now_add=True)
    tipo_pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES)
    horas_pagadas = models.DecimalField(max_digits=10, decimal_places=2)
    tarifa_por_hora = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Pago a {self.empleado.nombre} - {self.fecha_pago} - {self.monto_pagado}"
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para actualizar automáticamente el saldo del empleado.
        """
        # Guardar primero el pago
        super().save(*args, **kwargs)
        
        # Actualizar los totales de horas pagadas
        saldo, created = SaldoEmpleado.objects.get_or_create(empleado=self.empleado)
        
        if self.tipo_pago == 'por_hora':
            saldo.total_horas_pagadas_por_hora += self.horas_pagadas
        elif self.tipo_pago == 'por_destino':
            saldo.total_horas_pagadas_por_destino += self.horas_pagadas
        elif self.tipo_pago == 'colaboracion':
            saldo.total_horas_pagadas_colaboracion += self.horas_pagadas
        
        # Recalcular horas pendientes
        saldo.actualizar_saldo()
    
        # Importar la función desde vuelo.py
        from registro_vuelos.utils import actualizar_horas_empleado
        actualizar_horas_empleado(self.empleado)

    class Meta:
        verbose_name = "Pago a Empleado"
        verbose_name_plural = "Pagos a Empleados"

class SaldoEmpleado(models.Model):
    empleado = models.OneToOneField(Empleado, on_delete=models.CASCADE, related_name='saldo')
        
    # Horas pendientes de pago
    horas_pendientes_por_hora = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    horas_pendientes_por_destino = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    horas_pendientes_colaboracion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        
    # Costos pendientes de pago
    costo_pendiente_por_destino = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        
    # Campos para llevar el histórico
    total_horas_pagadas_por_hora = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_horas_pagadas_por_destino = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_horas_pagadas_colaboracion = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_costo_pagado_por_destino = models.DecimalField(max_digits=10, decimal_places=2, default=0)
        
    ultima_actualizacion = models.DateTimeField(auto_now=True)
        
    def actualizar_saldo(self):
        # Obtener total de horas acumuladas
        self.horas_pendientes_por_hora = self.empleado.horas_por_hora - self.total_horas_pagadas_por_hora
        self.horas_pendientes_por_destino = self.empleado.horas_por_destino - self.total_horas_pagadas_por_destino
        self.horas_pendientes_colaboracion = self.empleado.horas_colaboracion - self.total_horas_pagadas_colaboracion
        self.costo_pendiente_por_destino = self.empleado.total_costo_por_destino - self.total_costo_pagado_por_destino
        self.save()
        
    def __str__(self):
        return f"Saldo de {self.empleado.nombre}"

    def registrar_pago_por_hora(empleado, horas_a_pagar, tarifa_por_hora, descripcion=None):
        """
        Registra un pago por horas voladas y actualiza el saldo.
        """
        # Obtener el saldo del empleado
        saldo, created = SaldoEmpleado.objects.get_or_create(empleado=empleado)
            
        # Verificar que no se pague más de lo pendiente
        if horas_a_pagar > saldo.horas_pendientes_por_hora:
            raise ValueError(f"No se pueden pagar {horas_a_pagar} horas cuando solo hay {saldo.horas_pendientes_por_hora} pendientes")
            
        # Calcular monto a pagar
        monto = horas_a_pagar * tarifa_por_hora
            
        # Registrar el pago
        pago = PagoEmpleado.objects.create(
            empleado=empleado,
            tipo_pago='por_hora',
            horas_pagadas=horas_a_pagar,
            tarifa_por_hora=tarifa_por_hora,
            monto_pagado=monto,
            descripcion=descripcion
            )
            
        # Actualizar el saldo
        saldo.total_horas_pagadas_por_hora += horas_a_pagar
        saldo.actualizar_saldo()
            
        return pago
            
    class Meta:
        verbose_name = "Empleados - Saldos"
        verbose_name_plural = "Empleados - Saldos"        