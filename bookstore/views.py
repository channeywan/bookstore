from decimal import Decimal

from django.contrib import messages
from django.db import transaction
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
            address = form.cleaned_data['address']
            user.set_password(password)  # 加密存储
            user.save()

            # 2) 在Customers表中写一条记录, name=User.username
            #    password字段仅占位(不用于真实登录)
            Customers.objects.create(
                name=user.username,
                password=user.password,  # 仅占位
                address=address,
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
    查看所有书目 (任意登录/未登录用户都可访问)
    """
    query = request.GET.get('q', '').strip()
    field = request.GET.get('field', 'title')  # 默认按书名搜索

    # 定义允许的搜索字段
    allowed_fields = ['title', 'author', 'publisher']

    if field not in allowed_fields:
        field = 'title'  # 如果传入的field不合法，默认按书名搜索

    books = Books.objects.all()

    if query:
        # 动态构造过滤条件
        filter_kwargs = {f"{field}__icontains": query}
        books = books.filter(**filter_kwargs)

    context = {
        'books': books,
        'query': query,
        'field': field,
        'allowed_fields': allowed_fields,
    }

    return render(request, 'books/book_list.html', context)

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
    backorders = Backorders.objects.exclude(purchaseorders__status='Arrival')
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
        book_obj = get_object_or_404(Books, pk=book_id)
        bo = Backorders.objects.create(
            book_id_id = book_id,
            title = book_obj.title,
            publisher = book_obj.publisher,
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
def purchase_bulk_create(request):
    """
    一键生成采购单: 管理员可复制所有Backorders到Purchaseorders
    """
    if not request.user.is_staff:
        return HttpResponse("无权限执行此操作", status=403)

    from datetime import date
    backorders = Backorders.objects.all()
    for bo in backorders:
        # 如果想避免重复，则先检查 Purchaseorders 是否已存在
        if not Purchaseorders.objects.filter(backorder_id=bo).exists():
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
    bo = purchase.backorder_id
    book = bo.book_id
    book.stock_quantity += bo.quantity
    book.save()
    return redirect('purchase_list')



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
def customer_delete(request, pk):
    """
    仅管理员可删除用户，并同步删除对应的 Django User
    """
    if not request.user.is_staff:
        return HttpResponse("无权限访问该页面，仅管理员可操作。", status=403)

    # 1. 获取要删除的 Customers 对象
    customer_obj = get_object_or_404(Customers, pk=pk)

    # 2. 根据 Customers.name(与 User.username 对应) 去找 Django User
    try:
        user_obj = User.objects.get(username=customer_obj.name)
        # 3. 先删除 Django User
        user_obj.delete()
    except User.DoesNotExist:
        # 如果没有对应的 Django User，也可忽略或提示
        pass

    # 4. 删除 Customers 记录
    customer_obj.delete()

    return redirect('customer_list')



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
    列出当前登录用户的订单 (普通用户只能查看自己的; 管理员看全部)
    """
    if request.user.is_staff:
        # 如果是管理员 => 查询所有订单
        orders = Orders.objects.all()
    else:
        # 普通用户 => 只看自己的
        try:
            cust = Customers.objects.get(name=request.user.username)
            orders = Orders.objects.filter(customer_id=cust)
        except Customers.DoesNotExist:
            orders = []
    return render(request, 'orders/order_list.html', {'orders': orders})


# views.py
@login_required
def order_detail(request, pk):
    """
    显示订单详情：包含 Order + Orderdetails
    """
    order = get_object_or_404(Orders, pk=pk)
    details = Orderdetails.objects.filter(order=order)

    # 计算每个订单明细的小计
    details_with_subtotal = []
    for detail in details:
        subtotal = detail.quantity * detail.price
        details_with_subtotal.append({
            'book_id': detail.book.book_id,
            'title': detail.book.title,
            'price': detail.price,
            'quantity': detail.quantity,
            'subtotal': subtotal,
        })

    context = {
        'order': order,
        'details': details_with_subtotal,
    }
    return render(request, 'orders/order_detail.html', context)

@login_required
def order_delete(request, pk):
    """
    删除订单 - 如果是管理员, 或订单所属人(未支付? 看你的需求)
    """
    order = get_object_or_404(Orders, pk=pk)

    # 校验权限：管理员 or 本人
    if not request.user.is_staff:
        cust = Customers.objects.get(name=request.user.username)
        if order.customer_id_id != cust.customer_id:
            return HttpResponse("无权限删除此订单", status=403)

    # 可能还要判断 order_status != 'payed' 才能删除, 看你业务需求
    order.delete()
    return redirect('order_list')


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
        default_address = cust.address
        user_balance = cust.account_balance
    except Customers.DoesNotExist:
        user_balance = 0
        default_address = ''

    books = Books.objects.all()
    return render(request, 'orders/order_create.html', {
        'books': books,
        'default_address': default_address,
        'user_balance': user_balance,  # 传用户余额给模板
    })



@login_required
def order_pay(request, pk):
    order = get_object_or_404(Orders, pk=pk)
    # 检查当前用户是否=该订单所有者 or is_staff
    # ...
    # 先拿到订单金额
    base_amount = order.total_amount  # 订单原价

    # 找到Customers
    cust = Customers.objects.get(name=request.user.username)
    credit_level = cust.credit_level
    # 确定折扣 & 是否允许透支
    # level 1 => 10%折扣, 不可透支
    # level 2 => 15%折扣, 不可透支
    # level 3 => 15%折扣, 可先发书再付款, 透支有限
    # ...
    discount_map = {
        1: Decimal('0.10'),
        2: Decimal('0.15'),
        3: Decimal('0.15'),
        4: Decimal('0.20'),
        5: Decimal('0.25'),
    }
    discount_rate = discount_map.get(credit_level, Decimal('0'))
    pay_amount = base_amount * (Decimal('1') - discount_rate)

    # 根据级别确定“是否可透支”与“额度”
    # 仅示例，具体透支额度你可存 Customers 表或写死
    can_overdraft = (credit_level >= 3)
    overdraft_limit = 50  # 比如: 3级用户透支上限 50元,4级100,5级无限
    if credit_level == 3:
        overdraft_limit = 50
    elif credit_level == 4:
        overdraft_limit = 100
    elif credit_level == 5:
        overdraft_limit = 99999999  # practically unlimited

    # 计算“可用资金” = 余额 + (可透支？=> overdraft_limit : 0)
    available_funds = cust.account_balance + (overdraft_limit if can_overdraft else 0)

    if pay_amount > available_funds:
        # 余额不足
        return HttpResponse("支付失败：余额或透支额度不足。")

    # 如果够，就扣钱
    # 优先用余额
    cust.cumulative_amount +=pay_amount
    cost_from_balance = min(cust.account_balance, pay_amount)
    cust.account_balance -= cost_from_balance
    # 如果还剩 amt = pay_amount - cost_from_balance
    # 就表示进入透支
    leftover = pay_amount - cost_from_balance
    # 这 leftover 不一定要存, 具体透支如何记账看你业务需求
    # 这里只是演示

    # 扣完余额后，更新订单状态
    order.order_status = 'payed'
    order.save()
    cust.save()

    # 触发器 PayedOrder 也会更新库存 & 累计消费
    return redirect('order_list')


