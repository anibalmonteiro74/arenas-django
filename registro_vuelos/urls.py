from django.urls import path
from . import views
from .views import registrar_abono, cliente_detalle
from registro_vuelos.views import total_horometro_por_avion
from registro_vuelos.views import get_horometro
from .views import obtener_horometro  # Importamos la vista que crearemos
from .views import historial_horometro


urlpatterns = [
    path("fundir_barras/", views.fundir_barras, name="fundir_barras"),
    path("vender_barra/<int:barra_id>/", views.vender_barra, name="vender_barra"),
    path('registrar-abono/', registrar_abono, name='registrar_abono'),
    path("clientes/", views.clientes, name="clientes"),
    path("aviones/<int:avion_id>/horometro/", total_horometro_por_avion, name="total_horometro_por_avion"),
    path("api/get_horometro/", get_horometro, name="get_horometro"),
    path('api/get_horometro/', obtener_horometro, name='get_horometro'),
    path("historial_horometro/<str:matricula>/", historial_horometro, name="historial_horometro"),
    path('empleados/detalle/<int:empleado_id>/', views.detalle_empleado, name='detalle_empleado'),
    path('empleados/registrar-pago/<int:empleado_id>/', views.registrar_pago, name='registrar_pago'),
]
