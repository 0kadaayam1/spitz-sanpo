"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  
from base import views
from django.conf import settings
from django.conf.urls.static import static  

urlpatterns = [
    path('admin/', admin.site.urls),

    path('shop-post/<int:pk>/like/', views.toggle_shop_post_like, name='toggle_shop_post_like'),
    path('shop-post/<int:pk>/comment/', views.add_shop_post_comment, name='add_shop_post_comment'),

    path('shop-post/<int:pk>/edit/', views.ShopPostEditView.as_view(), name='shop_post_edit'),
    path('shop-post/<int:pk>/delete/', views.ShopPostDeleteView.as_view(), name='shop_post_delete'),

    path('shop/profile/edit/', views.ShopProfileEditView.as_view(), name='shop_profile_edit'),

    path('shop/add/', views.ShopPostCreateView.as_view(), name='shop_post_add'),

    path('shop/my-posts/', views.ShopMyPostListView.as_view(), name='shop_my_posts'),

    path('shop/', views.ShopTimelineView.as_view(), name='shop_timeline'),

    path('comment/<int:pk>/like/', views.toggle_comment_like, name='toggle_comment_like'),

    path('notifications/', views.notification_list, name='notification_list'),

    path('walk-log/<int:pk>/comment/', views.add_comment, name='add_comment'),

    path('walk-log/<int:pk>/like/', views.toggle_like, name='toggle_like'),

    path('shop/<int:user_id>/follow/', views.toggle_shop_follow, name='toggle_shop_follow'),

    path('user/<str:username>/follow/', views.toggle_follow, name='toggle_follow'),

    path('shop/<int:user_id>/', views.ShopAgentTimelineView.as_view(), name='shop_agent_timeline'),

    path('user/<str:username>/', views.UserTimelineView.as_view(), name='user_timeline'),

    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html', email_template_name='registration/password_reset_email.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    path('walk-log/add/', views.WalkLogCreateView.as_view(), name='walk_log_add'),

    path('walk-log/<int:pk>/edit/', views.WalkLogUpdateView.as_view(), name='walk_log_edit'),
    path('walk-log/<int:pk>/delete/', views.WalkLogDeleteView.as_view(), name='walk_log_delete'),

    path('walk-log/', views.WalkLogListView.as_view(), name='walk_log_list'),

    path('', views.TopView.as_view(), name='top'),

    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('account/', views.AccountUpdateView.as_view(), name='account'),
    path('profile/', views.ProfileUpdateView.as_view(), name='profile'), # 👈これが今回作ったスピッツ用画面！

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)