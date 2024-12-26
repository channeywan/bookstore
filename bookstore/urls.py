from django.urls import path
from .views import (
    index, book_list, book_create, book_edit,
    register_view,login_view,logout_view,
    backorder_list, backorder_create,
    purchase_list, purchase_create, purchase_arrival,
    customer_list, customer_edit,
    order_list, order_create, order_pay
)

urlpatterns = [
    path('', index, name='index'),

    # 书目
    path('books/', book_list, name='book_list'),
    path('books/new/', book_create, name='book_create'),
    path('books/<int:pk>/edit/', book_edit, name='book_edit'),
    # 登录
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    # 缺书登记
    path('backorders/', backorder_list, name='backorder_list'),
    path('backorders/new/', backorder_create, name='backorder_create'),

    # 采购单
    path('purchase/', purchase_list, name='purchase_list'),
    path('purchase/<int:backorder_id>/', purchase_create, name='purchase_create'),
    path('purchase/<int:pk>/arrival/', purchase_arrival, name='purchase_arrival'),

    # 客户
    path('customers/', customer_list, name='customer_list'),
    path('customers/<int:pk>/edit/', customer_edit, name='customer_edit'),

    # 订单
    path('orders/', order_list, name='order_list'),
    path('orders/new/', order_create, name='order_create'),
    path('orders/<int:pk>/pay/', order_pay, name='order_pay'),
]
