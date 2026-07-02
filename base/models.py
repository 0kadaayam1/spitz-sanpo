from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth import get_user_model
from django.conf import settings



class UserManager(BaseUserManager):

    def create_user(self, username, email, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None):
        user = self.create_user(
            username,
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    username = models.CharField(
        max_length=50, unique=True, blank=True, default='匿名')
    email = models.EmailField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_shop = models.BooleanField(default=False, verbose_name="お店ユーザー")
    objects = UserManager()
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', ]

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

class Profile(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE)
    # 飼い主さんの情報（元々の name をニックネームとして活用）
    name = models.CharField(default='', blank=True, max_length=50, verbose_name="飼い主のニックネーム")
    # ★スピッツ専用のオリジナル項目
    dog_name = models.CharField(default='', blank=True, max_length=50, verbose_name="愛犬の名前")
    dog_birthday = models.DateField(null=True, blank=True, verbose_name="愛犬の誕生日")

    # ★追加：性別の選択肢（男の子・女の子・不明など）
    GENDER_CHOICES = [
        ('male', '男の子'),
        ('female', '女の子'),
        ('unknown', '内緒 / 不明'),
    ]
    dog_gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        default='unknown', 
        blank=True, 
        verbose_name="ワンちゃんの性別"
    )

    # ★追加：プロフィール写真（画像が未登録のときのために blank=True, null=True にします）
    # upload_to='dog_profiles/' と書くことで、メディアフォルダの中の「dog_profiles」というフォルダに自動保存されます
    dog_image = models.ImageField(
        upload_to='dog_profiles/', 
        blank=True, 
        null=True, 
        verbose_name="ワンちゃんの写真"
    )

    following = models.ManyToManyField(
        'self', 
        symmetrical=False,  # 自分がフォローしても相手から自動でフォローし返されない関係を作るためのDjangoフレームワーク
        related_name='followers', 
        blank=True, 
        verbose_name="フォロー中"
        )

    # BooleanField → True か False の2択のデータを保存する項目。初期値(default)を False にしておくと公開アカウントになる。
    is_private = models.BooleanField(
        default=False, 
        verbose_name="アカウントを非公開にする（鍵垢）"
        )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # 愛犬の名前があれば「〇〇の飼い主」、なければニックネームを表示
        if self.dog_name:
            return f"{self.dog_name} の飼い主: {self.name}"
        return self.name

#OneToOneFieldを同時に作成
@receiver(post_save, sender=User)
def create_onetoone(sender, **kwargs):
    if kwargs['created']:
        Profile.objects.create(user=kwargs['instance'])

class WalkLog(models.Model):
    # 時間帯の選択肢
    TIME_CHOICES = [
        ('morning', '朝'),
        ('noon', '昼'),
        ('evening', '夕方'),
        ('night', '夜'),
    ]

    # 誰のお散歩か（ユーザーが削除されたら、そのお散歩記録も一緒に消える設定）
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="飼い主")
    
    # お散歩した日付
    date = models.DateField(verbose_name="お散歩日")
    
    # 時間帯（朝・昼・夕方・夜から選択）
    time_of_day = models.CharField(max_length=10, choices=TIME_CHOICES, default='morning', verbose_name="時間帯")
    
    # お散歩のメモ・日記
    note = models.TextField(blank=True, null=True, verbose_name="お散歩メモ")
    
    # お散歩中の写真（プロフィール写真とは別フォルダ「walk_logs/」に保存します）
    walk_image = models.ImageField(upload_to='walk_logs/', blank=True, null=True, verbose_name="お散歩写真")
    
    # データが作成された日時を自動記録
    created_at = models.DateTimeField(auto_now_add=True)

    # 誰がこの投稿にいいねしたかを記録する項目
    likes = models.ManyToManyField(User, related_name='liked_logs', blank=True, verbose_name="いいねしたユーザー")

    def __html__(self):
        return f"{self.date} ({self.get_time_of_day_display()}) - {self.user.username}"

class Comment(models.Model):
    # 📝 1. どのお散歩ログに対するコメントか（お散歩ログが消えたら、コメントも連動して消える）
    walk_log = models.ForeignKey(WalkLog, on_delete=models.CASCADE, related_name='comments', verbose_name="対象のお散歩ログ")
    
    # 👤 2. 誰がコメントしたか（ユーザーが消えたら、その人のコメントも消える）
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="コメントした人")
    
    # 💬 3. コメント本文
    text = models.TextField(verbose_name="コメント内容")
    
    # 📅 4. 書き込まれた日時（新しい順に並べるため自動記録）
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="書き込み日時")

    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True, verbose_name="コメントへのいいね")

    class Meta:
        ordering = ['created_at']  # コメントは古い順（会話が流れる順番）で並ぶようにします

    def __str__(self):
        return f"{self.user.username} - {self.text[:10]}"

class Notification(models.Model):
    # 通知の種類を定義（コメント、返信、いいね などに拡張できるようにします）
    NOTIFICATION_CHOICES = [
        ('comment', 'コメント'),
        ('like', 'いいね'),
    ]

    # 👤 1. 誰宛ての通知か（投稿の持ち主）
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="通知を受け取るユーザー")
    
    # 👤 2. 誰がアクションしたか（コメントした人）
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', verbose_name="アクションしたユーザー")
    
    # 🐾 3. どのお散歩ログに対するアクションか
    walk_log = models.ForeignKey(WalkLog, on_delete=models.CASCADE, blank=True, null=True, verbose_name="対象のお散歩ログ")
    
    # 📝 4. コメントそのものへの紐付け（どのコメントか特定するため）
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, blank=True, null=True, verbose_name="対象のコメント")
    
    # 🏷️ 5. 通知の種類（デフォルトはコメント）
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_CHOICES)
    
    # 👀 6. 読んだかどうか（Xの通知タブを開いたら既読にする用）
    is_read = models.BooleanField(default=False, verbose_name="既読フラグ")
    
    # 📅 7. 通知が届いた日時
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="通知日時")

    class Meta:
        ordering = ['-created_at']  # 新しい通知が一番上にくるようにします

    def __str__(self):
        return f"{self.sender.username} から {self.user.username} への通知 ({self.get_notification_type_display()})"

class ShopPost(models.Model):
    """お店のアカウントからの投稿・お知らせモデル"""
    # 🎯 'User' 直指定から 'settings.AUTH_USER_MODEL' に変更します
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shop_posts', verbose_name="お店ユーザー")
    title = models.CharField(max_length=100, verbose_name="タイトル")
    content = models.TextField(verbose_name="内容")
    image = models.ImageField(upload_to='shop_posts/', blank=True, null=True, verbose_name="画像")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="投稿日時")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

class ShopProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shop_profile')
    shop_name = models.CharField(max_length=100, verbose_name="店舗名")
    # 📷 お店のプロフィール写真を追加（犬と同様にデフォルト画像を設定しておくと便利です）
    shop_image = models.ImageField(upload_to='shop_images/', blank=True, null=True, verbose_name="店舗画像", default='shop_images/default_shop.png')
    description = models.TextField(verbose_name="お店の紹介文", blank=True, null=True)
    hours = models.CharField(max_length=100, verbose_name="営業時間")
    website_url = models.URLField(verbose_name="ホームページURL", blank=True, null=True)
    location = models.CharField(max_length=255, verbose_name="場所・住所")
    
    # 🗺️ Googleマップの埋め込みコード（<iframe>タグ）をそのまま保存できる欄
    map_iframe = models.TextField(verbose_name="Googleマップ埋め込みコード", blank=True, null=True, 
                                   help_text="Googleマップの『地図を埋め込む』から取得した<iframe>タグをそのまま貼り付けてください。")

    def __str__(self):
        return self.name

class ShopPostLike(models.Model):
    """お店のお知らせに対するいいねモデル"""
    shop_post = models.ForeignKey(ShopPost, on_delete=models.CASCADE, related_name='likes_received', verbose_name="対象のお知らせ")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="いいねしたユーザー")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('shop_post', 'user') # 同じ人が1つの投稿に何度もいいねできないようにする


class ShopPostComment(models.Model):
    """お店のお知らせに対するコメントモデル"""
    shop_post = models.ForeignKey(ShopPost, on_delete=models.CASCADE, related_name='comments_received', verbose_name="対象のお知らせ")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="コメントしたユーザー")
    text = models.TextField(verbose_name="コメント内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="書き込み日時")

    class Meta:
        ordering = ['created_at'] # コメントは古い順（会話の流れ順）

    def __str__(self):
        return f"{self.user.username} - {self.text[:10]}"