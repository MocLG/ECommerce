from django.urls import path
from . import views 

app_name = 'orders'

urlpatterns = [
    path('', views.payment_method, name='payment_method'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment/', views.payment, name='payment'),
    path('payments/', views.payments, name='payments'),
    path('stripe/checkout/', views.stripe_checkout, name='stripe_checkout'),
    path('stripe/webhook/', views.stripe_webhook, name='stripe_webhook'),
    path('stripe/success/', views.payment_success, name='payment_success'),
    path('stripe/cancel/', views.payment_cancel, name='payment_cancel'),
    path('order_completed/', views.order_completed, name='order_complete'),
]
