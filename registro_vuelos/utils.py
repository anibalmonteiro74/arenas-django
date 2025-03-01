def actualizar_horas_empleado(empleado):
    """
    Actualiza el saldo pendiente de un empleado basado en sus horas acumuladas.
    """
    # Importar de forma diferida para evitar importaciones circulares
    from registro_vuelos.models.empleados import SaldoEmpleado
    
    # Obtener o crear saldo
    saldo, created = SaldoEmpleado.objects.get_or_create(empleado=empleado)
    
    # Calcular horas pendientes
    saldo.horas_pendientes_por_hora = empleado.horas_por_hora - saldo.total_horas_pagadas_por_hora
    saldo.horas_pendientes_por_destino = empleado.horas_por_destino - saldo.total_horas_pagadas_por_destino
    saldo.horas_pendientes_colaboracion = empleado.horas_colaboracion - saldo.total_horas_pagadas_colaboracion
    saldo.costo_pendiente_por_destino = empleado.total_costo_por_destino - saldo.total_costo_pagado_por_destino
    
    saldo.save()