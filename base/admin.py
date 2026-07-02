from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, ShopProfile

class CustomUserAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('username', 'email', 'is_admin')
    
    # 🎯 ここを追加：エラーの原因になっていた標準のフィルターや検索機能をリセットします
    list_filter = ('is_admin', 'is_active')  # 自作のフィールドだけを指定
    search_fields = ('username', 'email')
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Permissions', {'fields': ('is_admin', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('collapse',),
            'fields': ('username', 'email', 'password'),
        }),
    )
    filter_horizontal = ()

class CustomUserAdmin(admin.ModelAdmin):
    # 管理画面のユーザー一覧に表示する項目（岡田さんのUserモデルにある項目だけに絞ります）
    list_display = ('username', 'email', 'is_shop')
    
    # ユーザー詳細画面で編集できる項目をシンプルに指定します
    fields = ('username', 'email', 'is_shop')

# 登録
admin.site.register(User, CustomUserAdmin)
admin.site.register(Profile)
admin.site.register(ShopProfile)