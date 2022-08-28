from django.contrib import admin
from .models import Post, Group


class PostAdmin(admin.ModelAdmin):
    list_display = ('pk', 'text', 'created', 'author', 'group')
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('created',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = ('pk', 'slug', 'title', 'description')
    search_fields = ('slug', 'title', 'description')
    empty_value_display = '-пусто-'


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
