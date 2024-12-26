from django import forms
from .models import Books

class BookForm(forms.ModelForm):
    class Meta:
        model = Books
        fields = [
            'book_id', 'title', 'publisher', 'price',
            'stock_quantity', 'stock_place',
            'author1st', 'author2nd', 'author3rd',
        ]
        # 如果 BookID 是自增，或者你不想手动输入，可改为 exclude=['book_id']
