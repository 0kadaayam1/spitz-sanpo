from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile, WalkLog, Comment, ShopPost

# 1. ユーザー（ログイン情報）登録用のフォーム
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'is_shop') # ログインに必要な項目

    def __init__(self, *value, **kwargs):
        super().__init__(*value, **kwargs)
        # 各入力欄にBootstrapなどの装飾用クラスを当てる（Vegeketのコードを踏襲）
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-control'


# 2. プロフィール（スピッツ＆飼い主情報）登録・編集用のフォーム
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        # 画面に入力欄として出したい項目を指定（性別と写真を追加！）
        fields = ('name', 'dog_name', 'dog_birthday', 'dog_gender', 'dog_image', 'is_private')
        
        # 生年月日の入力欄をカレンダー選択（日付選択ウィジェット）にする
        widgets = {
            'dog_birthday': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *value, **kwargs):
        super().__init__(*value, **kwargs)
        # プロフィール側の入力欄にも一括でスタイル用のクラスを当てる
        for field in self.fields.values():
            # 画像アップロード欄（FileField）以外に form-control を当てる（見た目が崩れないようにするため）
            if not isinstance(field.widget, forms.ClearableFileInput):
                field.widget.attrs['class'] = 'form-control'

# 3. お散歩記録用フォーム
class WalkLogForm(forms.ModelForm):
    class Meta:
        model = WalkLog
        # 画面に入力させる項目を指定（userやcreated_atは自動で入るので除外します）
        fields = ('date', 'time_of_day', 'note', 'walk_image')
        
        # 📅 日付の入力欄をカレンダー選択（カレンダーピッカー）にするための設定
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time_of_day': forms.Select(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': '今日のお散歩はどうでしたか？'}),
            'walk_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

# 4. コメント用フォーム
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
        widgets = {
            'text': forms.TextInput(attrs={
                'class': 'form-control form-control-sm rounded-pill border-secondary-subtle px-3',
                'placeholder': 'コメントを残す...🐾',
                'rows': 1,
            }),
        }

from .models import ShopProfile

# 5. 店舗プロフィール用フォーム
class ShopProfileForm(forms.ModelForm):
    class Meta:
        model = ShopProfile
        # 🎯 古い 'hours' を削除し、新しい時間と定休日のフィールド（計9個）を追加しました！
        fields = (
            'shop_name', 'shop_image', 'description', 
            'open_time', 'close_time',
            'is_closed_mon', 'is_closed_tue', 'is_closed_wed', 'is_closed_thu', 'is_closed_fri', 'is_closed_sat', 'is_closed_sun',
            'website_url', 'location', 'map_iframe',
            'has_dog_run', 'allows_large_dogs', 'has_parking', 'pets_allowed'
        )
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'お店の雰囲気や、看板犬の紹介などを自由に書いてください🐾'}),
            'map_iframe': forms.Textarea(attrs={'rows': 3, 'placeholder': '<iframe src="..." ...></iframe>'}),
            'shop_image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            # 🕒 開店・閉店時間をブラウザ標準の「時間選択プルダウン（または時計入力）」にします
            'open_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'close_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs) :
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # 画像フィールドだけBootstrapのform-control除外（レイアウト崩れ防止）
            if field_name == 'shop_image':
                field.widget.attrs['class'] = 'form-control-file'
            # 🏷️ 特徴タグや定休日のチェックボックス（BooleanField）は、綺麗に横並びにするため共通のクラスをあてます
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'

# 6. 店舗お知らせ投稿用フォーム（ここをカチッと定義します）
class ShopPostForm(forms.ModelForm):
    class Meta:
        model = ShopPost
        # 🎯 fields に 'category' を追加しました！
        fields = ('title', 'category', 'content', 'image')
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'タイトルを入力'}),
            # 🏷️ カテゴリをプルダウン（セレクトボックス）形式で表示します
            'category': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'お知らせの本文を入力してください🐾'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }