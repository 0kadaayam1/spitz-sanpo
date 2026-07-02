from .models import Notification

def unread_notifications(request):
    # 👤 ユーザーがログインしている場合だけ、未読の通知数をカウントする
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()
        return {
            'unread_notifications_count': count
        }
    # 👥 ログインしていない場合は0件にする
    return {
        'unread_notifications_count': 0
    }