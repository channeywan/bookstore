from django import forms
from django.contrib.auth.models import User
from .models import Books,Customers

class BookForm(forms.ModelForm):
    class Meta:
        model = Books
        fields = [
            'book_id', 'title', 'publisher', 'price',
            'stock_quantity', 'stock_place',
            'author1st', 'author2nd', 'author3rd',
        ]
        # 如果 BookID 是自增，或者你不想手动输入，可改为 exclude=['book_id']
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customers
        # 你想允许编辑哪些字段，就写进来
        fields = [
            'name',
            'address',
            'account_balance',
            'credit_level',
            'cumulative_amount'
        ]
class ProfileUpdateForm(forms.Form):
    """
    编辑个人信息（地址 + 邮箱）
    """
    email = forms.EmailField(label='邮箱', required=False)
    address = forms.CharField(label='地址', required=False, max_length=255)
    account_balance = forms.DecimalField(label='账户余额', required=False, disabled=True,decimal_places=2)
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)  # 用于保存时识别是谁
        super().__init__(*args, **kwargs)

        if self.user:
            # 初始值
            self.fields['email'].initial = self.user.email
            # 在Customers里查找
            try:
                cust = Customers.objects.get(name=self.user.username)
                self.fields['address'].initial = cust.address
                self.fields['account_balance'].initial = cust.account_balance
            except Customers.DoesNotExist:
                pass

    def save(self):
        if not self.user:
            return
        # 更新User.email
        email_val = self.cleaned_data['email']
        self.user.email = email_val
        self.user.save()

        # 更新Customers.address
        address_val = self.cleaned_data['address']
        try:
            cust = Customers.objects.get(name=self.user.username)
            cust.address = address_val
            cust.save()
        except Customers.DoesNotExist:
            pass
class RegisterForm(forms.ModelForm):
    """
    用户注册表单:
    - username
    - email (可选)
    - password + password2(确认)
    """
    password = forms.CharField(label='密码', widget=forms.PasswordInput)
    password2 = forms.CharField(label='确认密码', widget=forms.PasswordInput)
    address = forms.CharField(label='地址', max_length=255, required=True)
    class Meta:
        model = User
        fields = ['username', 'email' ]  # 用户名, 邮箱

    def clean(self):
        cleaned_data = super().clean()
        pwd1 = cleaned_data.get("password")
        pwd2 = cleaned_data.get("password2")
        if pwd1 and pwd2 and pwd1 != pwd2:
            self.add_error('password2', '两次输入的密码不一致')
        return cleaned_data
