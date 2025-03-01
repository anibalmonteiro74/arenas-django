import pytest
from django.db.utils import IntegrityError
from decimal import Decimal
from app.models import (
    Avion, Destino, Empleado, TrayectoCosto, Vuelo, TramoVuelo, Cliente, InventarioOro, Barra, Moneda
)

@pytest.mark.django_db
class TestSystem:

    def test_avion_creation(self):
        avion = Avion.objects.create(matricula="ABC123", modelo="Boeing 737", fabricante="Boeing")
        assert avion.matricula == "ABC123"
        assert avion.modelo == "Boeing 737"

    def test_destino_unique(self):
        destino = Destino.objects.create(nombre="Paris", activo=True)
        with pytest.raises(IntegrityError):
            Destino.objects.create(nombre="Paris")

    def test_empleado_horas_acumuladas(self):
        piloto = Empleado.objects.create(
            nombre="John Doe",
            tipo="piloto",
            fecha_ingreso="2023-01-01"
        )
        copiloto = Empleado.objects.create(
            nombre="Jane Smith",
            tipo="copiloto",
            fecha_ingreso="2023-01-01"
        )
        assert piloto.horas_totales == 0
        assert copiloto.horas_totales == 0

    def test_inventario_ajuste(self):
        inventario = InventarioOro.objects.create(gramos_disponibles_polvo=100)
        inventario.ajustar_polvo(10)
        assert inventario.gramos_ajustados_polvo == 110

    def test_trayecto_costo(self):
        destino_origen = Destino.objects.create(nombre="Origen")
        destino_destino = Destino.objects.create(nombre="Destino")
        empleado = Empleado.objects.create(
            nombre="Piloto",
            tipo="piloto",
            fecha_ingreso="2023-01-01"
        )
        costo = TrayectoCosto.objects.create(
            empleado=empleado,
            origen=destino_origen,
            destino=destino_destino,
            costo_trayecto=Decimal("150.50")
        )
        assert costo.costo_trayecto == Decimal("150.50")

    def test_flujo_vuelo_y_inventario(self):
        avion = Avion.objects.create(matricula="XYZ789", modelo="Airbus A320", fabricante="Airbus")
        destino1 = Destino.objects.create(nombre="New York")
        destino2 = Destino.objects.create(nombre="Los Angeles")
        piloto = Empleado.objects.create(
            nombre="Captain Marvel",
            tipo="piloto",
            fecha_ingreso="2023-01-01"
        )
        inventario = InventarioOro.objects.create(gramos_disponibles_polvo=500)

        vuelo = Vuelo.objects.create(
            avion=avion,
            piloto=piloto,
            tipo_cobro="por_hora",
            horas_totales=Decimal("2.5"),
            fecha="2025-01-01",
            bitacora="VUELO001"
        )
        tramo = TramoVuelo.objects.create(
            vuelo=vuelo,
            origen=destino1,
            destino=destino2,
            horometro_inicio=Decimal("100"),
            horometro_fin=Decimal("105"),
            tipo_pago="contado",
            pago_en_gramos=Decimal("50"),
            forma_pago="gramos"
        )

        vuelo.actualizar_horas_y_costos()
        inventario.actualizar_valor_total()

        assert vuelo.horas_totales == Decimal("2.5")
        assert piloto.horas_totales == Decimal("2.5")
        assert inventario.gramos_disponibles_polvo == Decimal("550")