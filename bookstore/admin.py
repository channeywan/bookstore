from django.contrib import admin
from .models import (
    Books, Series, Bookkeywords, Suppliers, Booksuppliers, Supplierbookinfo,
    Customers, Backorders, Purchaseorders, Orders, Orderdetails
)

@admin.register(Books)
class BooksAdmin(admin.ModelAdmin):
    list_display = ('book_id', 'title', 'publisher', 'price', 'stock_quantity')

@admin.register(Customers)
class CustomersAdmin(admin.ModelAdmin):
    list_display = ('customer_id', 'name', 'credit_level', 'account_balance', 'cumulative_amount')

# ... 其它表也可按需注册
admin.site.register(Series)
admin.site.register(Bookkeywords)
admin.site.register(Suppliers)
admin.site.register(Booksuppliers)
admin.site.register(Supplierbookinfo)
admin.site.register(Backorders)
admin.site.register(Purchaseorders)
admin.site.register(Orders)
admin.site.register(Orderdetails)
