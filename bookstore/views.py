from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from datetime import date

from .models import Books, Suppliers, Backorders, Purchaseorders, Customers, Orders, Orderdetails
from .forms import BookForm, RegisterForm, CustomerForm,ProfileUpdateForm


def index(request):
    """
    网站首页 (任何人都可访问)
    """
    return render(request, 'index.html')

def register_view(request):
    """
    注册新用户（普通或管理员都可在此注册，但仅能分配 staff 权限在admin后台或shell中）
    """
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            # 1) 创建Django User
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)  # 加密存储
            user.save()

            # 2) 在Customers表中写一条记录, name=User.username
            #    password字段仅占位(不用于真实登录)
            Customers.objects.create(
                name=user.username,
                password=user.password,  # 仅占位
                address='',
            )

            # 3) 自动登录(可选)
            user = authenticate(username=user.username, password=password)
            if user is not None:
                login(request, user)

            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    """
    自定义登录 (也可用内置 LoginView)
    """
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    """
    注销
    """
    logout(request)
    return redirect('login')


# ------------------------------
# 书目管理
# ------------------------------

def book_list(request):
    """
    查看所有书目 (任意登录/未登录用户都可访问? 如果要限制“必须登录”可加@login_required)
    """
    query = request.GET.get('q', '')  # 从GET中取搜索关键字
    if query:
        # 这里以 title 模糊查询为例，也可加 publisher 等
        books = Books.objects.filter(title__icontains=query)
    else:
        books = Books.objects.all()

    return render(request, 'books/book_list.html', {
        'books': books,
        'query': query,
    })

@login_required
def book_create(request):
    """
    新书入库（创建书目） - 仅管理员可访问
    """
    if not request.user.is_staff:
        return HttpResponse("无权限访问该页面，仅管理员可操作。", status=403)

    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()  # BookID 作为主键, 由前端决定或DB自增
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'books/book_create.html', {'form': form})


@login_required
def book_edit(request, pk):
    """
    编辑现有书目信息 - 仅管理员可访问
    """
    if not request.user.is_staff:
        return HttpResponse("无权限访问该页面，仅管理员可操作。", status=403)

    book = get_object_or_404(Books, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_create.html', {'form': form})


# ------------------------------
# 缺书登记
# ------------------------------

def backorder_list(request):
    """
    列出所有缺书记录(可让所有已登录用户查看, 也可仅登录可查看)
    """
    backorders = Backorders.objects.all()
    return render(request, 'backorders/backorder_list.html', {'backorders': backorders})


@login_required
def backorder_create(request):
    """
    直接进行缺书登记 (普通用户也可访问)
    """
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        supplier_id = request.POST.get('supplier_id')
        quantity = int(request.POST.get('quantity', '1'))

        bo = Backorders.objects.create(
            book_id_id = book_id,
            title = '临时标题',
            publisher = '临时出版社',
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


# ------------------------------
# 采购单管理 - 仅管理员可操作
# ------------------------------

@login_required
def purchase_list(request):
    """
    列出所有采购单 - 仅管理员可访问
    """
    if not request.user.is_staff:
        return HttpResponse("无权限访问该页面，仅管理员可操作。", status=403)

    purchases = Purchaseorders.objects.all()
    return render(request, 'purchase/purchase_list.html', {'purchases': purchases})

@login_required
def purchase_create(request, backorder_id):
    """
    根据缺书记录生成采购单 - 仅管理员可访问
    """
    if not request.user.is_staff:
        return HttpResponse("无权限访问该页面，仅管理员可操作。", status=403)

    bo = get_object_or_404(Backorders, pk=backorder_id)
    Purchaseorders.objects.create(
        backorder_id=bo,
        order_date=date.today(),
        status='Pending'
    )
    return redirect('purchase_list')

@login_required
def purchase_arrival(request, pk):
    """
    当采购单到货 -> 仅管理员可访问
    """
    if not request.user.is_staff:
        return HttpResponse("无权限访问该页面，仅管理员可操作。", status=403)

    purchase = get_object_or_404(Purchaseorders, pk=pk)
    purchase.status = 'Arrival'
    purchase.save()
    return redirect('purchase_list')


# ------------------------------
# 客户管理 - 仅管理员可访问
# ------------------------------

@login_required
def customer_list(request):
    if not request.user.is_staff:
        return HttpResponse("无权限访问该页面，仅管理员可操作。", status=403)

    customers = Customers.objects.all()
    return render(request, 'customers/customer_list.html', {'customers': customers})


@login_required
def customer_edit(request, pk):
    """
    管理员可编辑客户信息
    """
    if not request.user.is_staff:
        return HttpResponse("无权限访问该页面，仅管理员可操作。", status=403)

    # 根据主键 pk(其实就是 CustomerID) 获取对应的Customers
    customer_obj = get_object_or_404(Customers, pk=pk)

    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer_obj)
        if form.is_valid():
            form.save()
            return redirect('customer_list')
    else:
        form = CustomerForm(instance=customer_obj)

    return render(request, 'customers/customer_edit.html', {'form': form, 'customer_id': pk})

@login_required
def profile_update(request):
    """
    用户管理自己的邮箱、地址
    """
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('index')  # 或跳回个人中心
    else:
        form = ProfileUpdateForm(user=request.user)
    return render(request, 'customers/profile_update.html', {'form': form})


# ------------------------------
# 订单管理
# ------------------------------

@login_required
def order_list(request):
    """
    列出当前登录用户的订单 (普通用户只能查看自己的订单; 管理员也只能查看以自己username对应的客户？)
    """
    username = request.user.username
    try:
        cust = Customers.objects.get(name=username)
    except Customers.DoesNotExist:
        return render(request, 'orders/order_list.html', {'orders': []})

    orders = Orders.objects.filter(customer_id=cust)
    return render(request, 'orders/order_list.html', {'orders': orders})

@login_required
def order_create(request):
    if request.method == 'POST':
        # 不再从表单取 'customer_id'
        try:
            cust = Customers.objects.get(name=request.user.username)
        except Customers.DoesNotExist:
            # 如果当前用户在Customers里没有记录
            return HttpResponse("您没有客户信息，无法下单", status=400)

        shipping_addr = request.POST.get('shipping_address', '')
        book_id = request.POST.get('book_id')
        quantity = int(request.POST.get('quantity', '1'))

        # 创建 Orders，强制customer_id为当前登录用户的 Customers对象
        new_order = Orders.objects.create(
            customer_id=cust,
            order_date=date.today(),
            shipping_address=shipping_addr,
            order_status='unpayed'
        )

        # 继续创建 Orderdetails
        book_obj = Books.objects.get(pk=book_id)
        detail_price = book_obj.price
        Orderdetails.objects.create(
            order=new_order,  # 不能写 order_id=new_order
            book=book_obj,    # 同理
            quantity=quantity,
            price=detail_price
        )

        return redirect('order_list')

    # GET 请求，显示下单表单
    # 不再让用户选择 customer_id
    try:
        cust = Customers.objects.get(name=request.user.username)
        user_balance = cust.account_balance
    except Customers.DoesNotExist:
        user_balance = 0

    books = Books.objects.all()
    return render(request, 'orders/order_create.html', {
        'books': books,
        'user_balance': user_balance,  # 传用户余额给模板
    })



@login_required
def order_pay(request, pk):
    """
    模拟顾客支付订单 -> 触发器 PayedOrder
    """
    order = get_object_or_404(Orders, pk=pk)
    # 如果你想限制: 只有订单所属人 or 管理员 才能支付:
    username = request.user.username
    cust = None
    try:
        cust = Customers.objects.get(name=username)
    except Customers.DoesNotExist:
        pass

    if cust and order.customer_id_id != cust.customer_id and not request.user.is_staff:
        return HttpResponse("无权限支付该订单", status=403)

    order.order_status = 'payed'
    order.save()
    return redirect('order_list')
