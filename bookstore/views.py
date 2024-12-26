from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from datetime import date
from .models import Books, Suppliers, Backorders, Purchaseorders
from .forms import BookForm

def index(request):
    """
    主页示例
    """
    return render(request, 'index.html')

def book_list(request):
    """
    查看所有书目的列表
    """
    books = Books.objects.all()
    return render(request, 'books/book_list.html', {'books': books})

def book_create(request):
    """
    新书入库（创建书目）
    """
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            # 因为 BookID 是主键，如果不想让用户指定，可在数据库自增或自行处理
            form.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'books/book_create.html', {'form': form})

def book_edit(request, pk):
    """
    编辑现有书目信息
    """
    book = get_object_or_404(Books, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_create.html', {'form': form})
def backorder_list(request):
    """
    列出所有缺书记录
    """
    backorders = Backorders.objects.all()
    return render(request, 'backorders/backorder_list.html', {'backorders': backorders})

def backorder_create(request):
    """
    直接进行缺书登记
    """
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        supplier_id = request.POST.get('supplier_id')
        quantity = int(request.POST.get('quantity', '1'))

        # 获取图书和供应商对象(若不存在需做异常处理)
        # 这里只是示例，实际可能需要先校验
        bo = Backorders.objects.create(
            book_id_id = book_id,
            title = '临时标题',         # 真实情况下应填写表单中数据
            publisher = '临时出版社',  # ditto
            supplier_id_id = supplier_id,
            quantity = quantity,
            registration_date = date.today(),
        )
        bo.save()
        return redirect('backorder_list')

    suppliers = Suppliers.objects.all()
    books = Books.objects.all()
    return render(request, 'backorders/backorder_create.html', {
        'suppliers': suppliers,
        'books': books,
    })
def purchase_list(request):
    """
    列出所有采购单
    """
    purchases = Purchaseorders.objects.all()
    return render(request, 'purchase/purchase_list.html', {'purchases': purchases})

def purchase_create(request, backorder_id):
    """
    根据缺书记录生成采购单
    """
    # 假设点击按钮时，把 backorder_id 带过来
    bo = get_object_or_404(Backorders, pk=backorder_id)
    Purchaseorders.objects.create(
        backorder_id=bo,
        order_date=date.today(),
        status='Pending'
    )
    return redirect('purchase_list')

def purchase_arrival(request, pk):
    """
    当采购单到货 -> 触发器(PurchaseArrival) 会自动更新库存 & 删除缺书记录
    """
    purchase = get_object_or_404(Purchaseorders, pk=pk)
    # 改状态为 "Arrival"
    purchase.status = 'Arrival'
    purchase.save()
    return redirect('purchase_list')
from .models import Customers

def customer_list(request):
    customers = Customers.objects.all()
    return render(request, 'customers/customer_list.html', {'customers': customers})

def customer_create(request):
    """
    客户注册
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        password = request.POST.get('password')
        address = request.POST.get('address', '')

        Customers.objects.create(
            name=name,
            password=password,  # 真实环境中要做加密
            address=address,
            # 其余默认为初始值
        )
        return redirect('customer_list')
    return render(request, 'customers/customer_create.html')
from .models import Orders, Orderdetails

def order_list(request):
    """
    列出所有订单
    """
    orders = Orders.objects.all()
    return render(request, 'orders/order_list.html', {'orders': orders})

def order_create(request):
    """
    顾客下单：可一次订多本书
    """
    if request.method == 'POST':
        customer_id = request.POST.get('customer_id')
        shipping_addr = request.POST.get('shipping_address')
        # 这里简化处理，如有多本书，需要前端提交更多信息
        book_id = request.POST.get('book_id')
        quantity = int(request.POST.get('quantity'))

        # 创建订单
        new_order = Orders.objects.create(
            customer_id_id=customer_id,
            order_date=date.today(),
            shipping_address=shipping_addr,
            order_status='unpayed'
        )

        # 创建订单明细
        # 价格(Price) 可根据 Books 里的price 或折扣计算，这里演示直接取
        book_obj = Books.objects.get(pk=book_id)
        detail_price = book_obj.price
        Orderdetails.objects.create(
            order_id=new_order,
            book_id=book_obj,
            quantity=quantity,
            price=detail_price
        )

        # 由于你有 AFTER INSERT 触发器 `UpdateOrderTotal`，
        # Django 插入 OrderDetails 后，会自动更新 Orders 表中的 TotalAmount

        return redirect('order_list')

    customers = Customers.objects.all()
    books = Books.objects.all()
    return render(request, 'orders/order_create.html', {
        'customers': customers,
        'books': books,
    })

def order_pay(request, pk):
    """
    模拟顾客支付订单 -> 触发器 PayedOrder 执行 扣库存 + 累计消费
    """
    order = get_object_or_404(Orders, pk=pk)
    order.order_status = 'payed'
    order.save()  # 触发器将会自动更新库存 & 客户累计消费
    return redirect('order_list')
