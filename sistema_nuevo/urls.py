
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include
from django.http import HttpResponse

# Vista simple para la página de inicio
def home(request):
    return HttpResponse("¡Bienvenido a mi proyecto Django!")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', home, name='home'),  # Ruta para la página principal
    path('registro_vuelos/', include('registro_vuelos.urls')),
]