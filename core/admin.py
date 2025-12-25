from django.contrib import admin
from .models import BlogPost, ForumPost, SuccessStory

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'published')
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ('title', 'summary', 'content')
    list_filter = ('published', 'date')

@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    search_fields = ('title', 'content', 'user__username', 'user__email')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'

@admin.register(SuccessStory)
class SuccessStoryAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_name', 'contact_email', 'approved', 'submitted_at')
    search_fields = ('company_name', 'contact_name', 'contact_email', 'story')
    list_filter = ('approved', 'submitted_at')
    list_editable = ('approved',)
    readonly_fields = ('submitted_at',)
    date_hierarchy = 'submitted_at'
