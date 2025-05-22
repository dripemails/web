from django.contrib import admin
from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'published')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'summary', 'content')
    list_filter = ('published', 'date') 