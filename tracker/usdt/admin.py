from django.contrib import admin
from .models import Book

class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'publication_date', 'author', 'price', 'book_type']

admin.site.register(Book, BookAdmin)