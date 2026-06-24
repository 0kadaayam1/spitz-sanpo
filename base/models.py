from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth import get_user_model



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
    objects = UserManager()
    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email', ]

    def __str__(self):
        return self.email

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

    def __html__(self):
        return f"{self.date} ({self.get_time_of_day_display()}) - {self.user.username}"