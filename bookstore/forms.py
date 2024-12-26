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
class RegisterForm(forms.ModelForm):
    """
    用户注册表单:
    - username
    - email (可选)
    - password + password2(确认)
    """
    password = forms.CharField(label='密码', widget=forms.PasswordInput)
    password2 = forms.CharField(label='确认密码', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email']  # 用户名, 邮箱

    def clean(self):
        cleaned_data = super().clean()
        pwd1 = cleaned_data.get("password")
        pwd2 = cleaned_data.get("password2")
        if pwd1 and pwd2 and pwd1 != pwd2:
            self.add_error('password2', '两次输入的密码不一致')
        return cleaned_data
