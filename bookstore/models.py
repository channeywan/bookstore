from django.db import models

# ---------- 1. 书目相关 ----------

class Books(models.Model):
    book_id = models.IntegerField(db_column='BookID', primary_key=True)
    title = models.CharField(db_column='Title', max_length=255)
    publisher = models.CharField(db_column='Publisher', max_length=255)
    price = models.DecimalField(db_column='Price', max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField(db_column='StockQuantity')
    stock_place = models.CharField(db_column='StockPlace', max_length=255, null=True, blank=True)
    author1st = models.CharField(db_column='Author1st', max_length=100)
    author2nd = models.CharField(db_column='Author2nd', max_length=100, null=True, blank=True)
    author3rd = models.CharField(db_column='Author3rd', max_length=100, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'Books'

    def __str__(self):
        return f"{self.title} (ID: {self.book_id})"


class Series(models.Model):
    id = models.AutoField(primary_key=True)  # Django 主键
    book_id = models.ForeignKey(Books, models.DO_NOTHING, db_column='BookID')
    series_id = models.SmallIntegerField(db_column='SeriesID')

    class Meta:
        managed = False
        db_table = 'Series'
        unique_together = (('book_id', 'series_id'),)


class Bookkeywords(models.Model):
    book_id = models.ForeignKey(Books, models.DO_NOTHING, db_column='BookID', primary_key=True)
    keyword_name = models.CharField(db_column='KeywordName', max_length=50)

    class Meta:
        managed = False
        db_table = 'BookKeywords'
        unique_together = (('book_id', 'keyword_name'),)


# ---------- 2. 供应商相关 ----------

class Suppliers(models.Model):
    supplier_id = models.IntegerField(db_column='SupplierID', primary_key=True)
    supplier_name = models.CharField(db_column='SupplierName', max_length=50)
    phone = models.CharField(db_column='Phone', max_length=11, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'Suppliers'

    def __str__(self):
        return self.supplier_name


class Booksuppliers(models.Model):
    id = models.AutoField(primary_key=True)  # Django 主键

    book_id = models.ForeignKey(Books, models.DO_NOTHING, db_column='BookID')
    supplier_id = models.ForeignKey(Suppliers, models.DO_NOTHING, db_column='SupplierID')

    class Meta:
        managed = False
        db_table = 'BookSuppliers'
        unique_together = (('book_id', 'supplier_id'),)



class Supplierbookinfo(models.Model):
    id = models.AutoField(primary_key=True)  # Django 主键

    supplier = models.ForeignKey(Suppliers, models.DO_NOTHING, db_column='SupplierID')
    book = models.ForeignKey(Books, models.DO_NOTHING, db_column='BookID')
    supply_price = models.DecimalField(db_column='SupplyPrice', max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'SupplierBookInfo'
        unique_together = (('supplier', 'book'),)


# ---------- 3. 客户管理 ----------

class Customers(models.Model):
    customer_id = models.AutoField(db_column='CustomerID', primary_key=True)
    name = models.CharField(db_column='Name', max_length=100)
    password = models.CharField(db_column='Password', max_length=255)
    address = models.CharField(db_column='Address', max_length=255, null=True, blank=True)
    account_balance = models.DecimalField(db_column='AccountBalance', max_digits=10, decimal_places=2, default=0.00)
    credit_level = models.IntegerField(db_column='CreditLevel', default=1)
    cumulative_amount = models.DecimalField(db_column='CumulativeAmount', max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        managed = False
        db_table = 'Customers'

    def __str__(self):
        return f"{self.name} (ID: {self.customer_id})"


# ---------- 4. 采购管理：缺书 & 采购单 ----------

class Backorders(models.Model):
    backorder_id = models.AutoField(db_column='BackOrderID', primary_key=True)
    book_id = models.ForeignKey(Books, models.DO_NOTHING, db_column='BookID')
    title = models.CharField(db_column='Title', max_length=255)
    publisher = models.CharField(db_column='Publisher', max_length=100)
    supplier_id = models.ForeignKey(Suppliers, models.DO_NOTHING, db_column='SupplierID')
    quantity = models.IntegerField(db_column='Quantity')
    registration_date = models.DateField(db_column='RegistrationDate')
    customer_id = models.ForeignKey(Customers, models.DO_NOTHING, db_column='CustomerID', null=True, blank=True)
    notified = models.BooleanField(db_column='Notified', default=False)

    class Meta:
        managed = False
        db_table = 'BackOrders'


class Purchaseorders(models.Model):
    purchase_order_id = models.AutoField(db_column='PurchaseOrderID', primary_key=True)
    backorder_id = models.ForeignKey(Backorders, models.DO_NOTHING, db_column='BackOrderID')
    order_date = models.DateField(db_column='OrderDate')
    status = models.CharField(db_column='Status', max_length=50, default='0')

    class Meta:
        managed = False
        db_table = 'PurchaseOrders'


# ---------- 5. 订单管理 ----------

class Orders(models.Model):
    order_id = models.AutoField(db_column='OrderID', primary_key=True)
    customer_id = models.ForeignKey(Customers, models.DO_NOTHING, db_column='CustomerID')
    order_date = models.DateField(db_column='OrderDate')
    total_amount = models.DecimalField(db_column='TotalAmount', max_digits=10, decimal_places=2, default=0.00)
    shipping_address = models.CharField(db_column='ShippingAddress', max_length=255)
    order_status = models.CharField(db_column='OrderStatus', max_length=50, default='unpayed')

    class Meta:
        managed = False
        db_table = 'Orders'


class Orderdetails(models.Model):
    id = models.AutoField(primary_key=True)  # Django主键

    order = models.ForeignKey(Orders, models.DO_NOTHING, db_column='OrderID')
    book = models.ForeignKey(Books, models.DO_NOTHING, db_column='BookID')
    quantity = models.IntegerField(db_column='Quantity')
    price = models.DecimalField(db_column='Price', max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        managed = False
        db_table = 'OrderDetails'
        unique_together = (('order', 'book'),)

