from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index_view, name='index'),
    path('accounts/login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/public/', views.register_public, name='register_public'),
    path('register/politician/', views.register_politician, name='register_politician'),
    path('home/public/', views.public_home, name='public_home'),
    path('home/politician/', views.politician_home, name='politician_home'),
    path('home/admin/', views.admin_home, name='admin_home'),
    path('approve/<int:user_id>/', views.approve_politician, name='approve_politician'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
