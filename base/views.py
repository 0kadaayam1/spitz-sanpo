from django.views.generic import CreateView, UpdateView, TemplateView, ListView, DeleteView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect
from django.urls import reverse_lazy

# 先ほど作成した独自のフォームをインポート（同じフォルダ内を想定）
from .forms import SignUpForm, ProfileForm, WalkLogForm
from .models import Profile, WalkLog

User = get_user_model()


class SignUpView(CreateView):
    # 1. 独自で作ったSignUpFormを指定（メールアドレス等の入力用）
    form_class = SignUpForm
    success_url = '/login/'
    template_name = 'pages/signup.html'

    def form_valid(self, form):
        messages.success(self.request, '新規登録が完了しました。続けてログインしてください。')
        return super().form_valid(form)


class Login(LoginView):
    template_name = 'pages/login.html'

    def form_valid(self, form):
        messages.success(self.request, 'ログインしました。')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'エラーでログインできません。')
        return super().form_invalid(form)


class AccountUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'pages/account.html'
    fields = ('username', 'email')
    success_url = '/account/'

    def get_object(self):
        self.kwargs['pk'] = self.request.user.pk
        return super().get_object()


# ★ここが重要：スピッツ情報を更新できるようにカスタム
class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    template_name = 'pages/profile.html'
    
    # 2. 独自で作ったProfileForm（スピッツ用項目）を指定
    form_class = ProfileForm
    success_url = '/profile/'

    def get_object(self):
        self.kwargs['pk'] = self.request.user.pk
        return super().get_object()

    def form_valid(self, form):
        messages.success(self.request, 'プロフィールを更新しました！')
        return super().form_valid(form)


def custom_logout(request):
    django_logout(request)
    return redirect('/login/')

class TopView(TemplateView):
    template_name = 'pages/top.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # 🔐 ログインしている場合のみ、そのユーザーの過去のお散歩ログを最新順に最大5件取得
        if self.request.user.is_authenticated:
            context['walk_logs'] = WalkLog.objects.filter(
                user=self.request.user
            ).order_by('-date', '-created_at')[:5]  # 最新の5件

        # select_related('user') をつけることで、投稿した飼い主さんの名前も一緒に素早く引っ張ってこれます
        context['timeline_logs'] = WalkLog.objects.all().select_related('user').order_by('-created_at')[:10]
            
        return context 

class WalkLogCreateView(LoginRequiredMixin, CreateView):
    model = WalkLog
    form_class = WalkLogForm
    template_name = 'pages/walk_log_form.html'  # 👈 新しく作るHTMLファイル名
    success_url = '/'  # 👈 保存が成功したらトップページに戻る

    # ✨ ここが重要：ログイン中のユーザーを自動的にお散歩ログに紐付ける
    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'お散歩の記録を保存しました！🐾')
        return super().form_valid(form)

class WalkLogListView(LoginRequiredMixin, ListView):
    model = WalkLog
    template_name = 'pages/walk_log_list.html'  # 👈 次に作る予定のHTMLファイル名
    context_object_name = 'walk_logs'
    paginate_by = 10  # 🐾 1ページに10件ずつ表示（溜まってきても安心！）

    # ✨ ログインしているユーザー自身のログだけを最新順に取得
    def get_queryset(self):
        return WalkLog.objects.filter(user=self.request.user).order_by('-date', '-created_at')

class WalkLogUpdateView(LoginRequiredMixin, UpdateView):
    model = WalkLog
    form_class = WalkLogForm
    template_name = 'pages/walk_log_form.html'  # 🐾 新規登録と同じ入力画面を使い回せます！
    success_url = reverse_lazy('walk_log_list')  # 編集が終わったら一覧ページに戻る

    # 🔐 自分のお散歩ログしか編集できないようにするセキュリティ設定
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'お散歩の記録を更新しました！📝')
        return super().form_valid(form)


class WalkLogDeleteView(LoginRequiredMixin, DeleteView):
    model = WalkLog
    template_name = 'pages/walk_log_confirm_delete.html'  # 👈 後ほど作る「本当に消しますか？」の確認画面
    success_url = reverse_lazy('walk_log_list')  # 削除が終わったら一覧ページに戻る

    # 🔐 自分のお散歩ログしか削除できないようにするセキュリティ設定
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'お散歩の記録を削除しました。')
        return super().delete(request, *args, **kwargs)