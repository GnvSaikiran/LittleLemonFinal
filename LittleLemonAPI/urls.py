from django.urls import path, include
from . import views
from rest_framework.routers import SimpleRouter


router = SimpleRouter(trailing_slash=False)
router.register('menu-items', views.MenuItemViewSet)
router.register('categories', views.CategoryViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('groups/<str:role>/users', views.roles, name='roles'),
    path('groups/<str:role>/users/<int:pk>', views.remove_role, name='remove_role'),
    path('cart/menu-items', views.cart, name='cart'),
    path('orders', views.OrderView.as_view(), name='orders'),
    path('orders/<int:pk>', views.SingleOrderView.as_view(), name='single_order'),
]