from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile, WalkLog

# 1. ユーザー（ログイン情報）登録用のフォーム
class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email') # ログインに必要な項目

    def __init__(self, *value, **kwargs):
        super().__init__(*value, **kwargs)
        # 各入力欄にBootstrapなどの装飾用クラスを当てる（Vegeketのコードを踏襲）
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


# 2. プロフィール（スピッツ＆飼い主情報）登録・編集用のフォーム
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        # 画面に入力欄として出したい項目を指定（性別と写真を追加！）
        fields = ('name', 'dog_name', 'dog_birthday', 'dog_gender', 'dog_image')
        
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