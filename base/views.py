from django.views.generic import CreateView, UpdateView, TemplateView, ListView, DeleteView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse_lazy 
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q

# 先ほど作成した独自のフォームをインポート（同じフォルダ内を想定）
from .forms import SignUpForm, ProfileForm, WalkLogForm, CommentForm, ShopProfileForm, ShopPostForm
from .models import Profile, WalkLog, Comment, Notification, ShopPost, ShopProfile, ShopPostLike, ShopPostComment

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
        
        # 1. まずはDjangoの標準のログイン処理を走らせて、完全にログイン状態にします
        response = super().form_valid(form)
        
        # 2. そのあとで、お店ユーザーかどうかの判定をして行き先を変えます
        if self.request.user.is_shop:
            return redirect('shop_profile_edit')
            
        return response


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
        user = self.request.user
        
        # 🔐 ログインしている場合
        if user.is_authenticated:
            if user.is_shop:
                # 🏪 お店アカウントの場合：自分が投稿したお知らせを最新順に最大5件取得
                context['shop_posts'] = ShopPost.objects.filter(
                    user=user
                ).order_by('-created_at')[:5]
            else:
                # 🐾 一般ユーザーの場合：そのユーザーの過去のお散歩ログを最新順に最大5件取得
                context['walk_logs'] = WalkLog.objects.filter(
                    user=user
                ).order_by('-date', '-created_at')[:5]

        # 📅 タイムラインの取得（鍵垢の制限を含む既存のロジック）
        if user.is_authenticated:
            # 🟢 ログイン中：①公開垢、②自分の投稿、③フォロー中の投稿 のどれかに当てはまるものだけ
            my_profile = user.profile
            context['timeline_logs'] = WalkLog.objects.filter(
                Q(user__profile__is_private=False) |
                Q(user=user) |
                Q(user__profile__in=my_profile.following.all())
            ).select_related('user').distinct().order_by('-created_at')[:10]
            
        else:
            # 🟡 ログアウト中：一般公開（is_private=False）の投稿だけ
            context['timeline_logs'] = WalkLog.objects.filter(
                user__profile__is_private=False
            ).select_related('user').order_by('-created_at')[:10]
            
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

class UserTimelineView(TemplateView):
    template_name = 'pages/user_timeline.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # URLから渡されたユーザー名（username）をもとに、そのユーザーが存在するかチェックして取得
        target_user = get_object_or_404(User, username=self.kwargs['username'])
        context['target_user'] = target_user
        
        # そのユーザーが投稿したお散歩ログだけを最新順にすべて取得
        context['logs'] = WalkLog.objects.filter(user=target_user).order_by('-created_at')
        
        return context

@login_required
@require_POST
def toggle_like(request, pk):
    # いいね対象のお散歩ログを取得（無ければ404エラー）
    log = get_object_or_404(WalkLog, pk=pk)
    
    # 自分がすでにいいねしているかチェック
    if log.likes.filter(id=request.user.id).exists():
        # すでにいいねしていれば、いいねを外す
        log.likes.remove(request.user)
    else:
        # まだいいねしていなければ、いいねをつける
        log.likes.add(request.user)
        
    # ボタンを押した元のページ（トップや個別タイムライン）にそのまま戻す
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
@require_POST
def toggle_follow(request, username):
    # フォローしたい相手のユーザーを取得
    target_user = get_object_or_404(User, username=username)
    
    # 自分自身のプロフィールと、相手のプロフィールを取得
    my_profile = request.user.profile
    target_profile = target_user.profile
    
    # 自分が自分をフォローしようとしている場合は何もしない（一応の安全対策）
    if my_profile == target_profile:
        return redirect('user_timeline', username=username)
        
    # すでにフォローしているかチェック
    if my_profile.following.filter(pk=target_profile.pk).exists():
        # すでにフォローしていれば、フォローを外す
        my_profile.following.remove(target_profile)
        messages.success(request, f"{target_user.username} さんのフォローを解除しました。")
    else:
        # まだフォローしていなければ、フォローする
        my_profile.following.add(target_profile)
        messages.success(request, f"{target_user.username} さんをフォローしました！🐾")
        
    # 元にいた相手の個別タイムライン画面に戻す
    return redirect('user_timeline', username=username)

@login_required
@require_POST
def add_comment(request, pk):
    # コメント対象のお散歩ログを取得
    log = get_object_or_404(WalkLog, pk=pk)
    
    # フォームから送られてきたデータを取得
    form = CommentForm(request.POST)
    
    if form.is_valid():
        # まだデータベースには保存せず、インスタンスだけを作る
        comment = form.save(commit=False)
        # 「誰が」「どのお散歩ログに」コメントしたかをセット
        comment.user = request.user
        comment.walk_log = log
        # データベースに正式保存
        comment.save()

        if log.user != request.user:
            Notification.objects.create(
                user=log.user,                # 通知を受け取る人（お散歩ログの投稿者）
                sender=request.user,          # アクションした人（コメントした人）
                walk_log=log,                 # 対象のお散歩ログ
                comment=comment,              # 対象のコメント
                notification_type='comment'   # 通知の種類
            )
        
        messages.success(request, 'コメントを投稿しました！🐾')
        
    # コメントを入力した元のページ（トップや個別タイムライン）にそのまま戻す
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def notification_list(request):
    # 👤 ログインユーザー宛ての通知をすべて取得
    notifications = Notification.objects.filter(user=request.user)
    
    # 👀 このページを開いた瞬間に、そのユーザーの未読通知をすべて「既読（is_read=True）」にする
    unread_notifications = notifications.filter(is_read=False)
    unread_notifications.update(is_read=True)
    
    return render(request, 'pages/notification_list.html', {
        'notifications': notifications
    })

@login_required
@require_POST
def toggle_comment_like(request, pk):
    # いいね対象のコメントを取得
    comment = get_object_or_404(Comment, pk=pk)
    
    # 既にログインユーザーがいいねをしていたら消す、していなければ足す
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
    else:
        comment.likes.add(request.user)
        
        # 他人のコメントにいいねした時だけ通知を飛ばす
        if comment.user != request.user:
            Notification.objects.create(
                user=comment.user,            # 通知を受け取る人（コメントを書いた人）
                sender=request.user,          # いいねした人
                walk_log=comment.walk_log,    # 対象のお散歩ログ
                comment=comment,              # 対象のコメント
                notification_type='like'      # 通知の種類を「いいね」に
            )
            
    return redirect(request.META.get('HTTP_REFERER', '/'))

class ShopTimelineView(LoginRequiredMixin, ListView):
    model = ShopPost
    template_name = 'pages/shop_timeline.html'
    context_object_name = 'shop_posts'

    def get_queryset(self):
        # まずは通常通り最新のお知らせ一覧を取得します
        posts = ShopPost.objects.all().order_by('-created_at')
        
        # 💡 ここからパワーアップ！
        # 各お知らせに対して、ログインユーザーがいいねしているかのフラグ（is_liked）をその場で追加します
        for post in posts:
            post.is_liked = post.likes_received.filter(user=self.request.user).exists()
            
        return posts

class ShopPostCreateView(LoginRequiredMixin, CreateView):
    model = ShopPost
    form_class = ShopPostForm
    template_name = 'pages/shop_post_form.html'
    success_url = reverse_lazy('shop_my_posts')

    def form_valid(self, form):
        # 🔗 ログイン中ユーザーのお店プロフィールを自動でセットする
        form.instance.shop = self.request.user.shop_profile
        return super().form_valid(form)

class ShopProfileEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """お店専用のプロフィール編集画面"""
    model = ShopProfile
    form_class = ShopProfileForm
    template_name = 'pages/shop_profile_form.html'
    success_url = reverse_lazy('shop_timeline')  # 保存したらタイムラインへ

    # お店アカウントだけがアクセスできるように制限
    def test_func(self):
        return self.request.user.is_shop

    # 🎯 自分のプロフィールだけを編集できるようにターゲットを絞る（安全版に修正）
    def get_object(self, queryset=None):
        try:
            # すでにプロフィールがあればそれを取得
            return ShopProfile.objects.get(user=self.request.user)
        except ShopProfile.DoesNotExist:
            # 💡 もし無ければ、実際のモデルのフィールド名「shop_name」に合わせて安全に作成
            return ShopProfile.objects.create(
                user=self.request.user,
                name=self.request.user.username,  # 初期値としてユーザー名をセット
                location="未設定"                 # 初期値として未設定をセット
            )

class ShopMyPostListView(LoginRequiredMixin, ListView):
    """ログイン中のお店が、自分の投稿したお知らせだけを一覧で確認する画面"""
    model = ShopPost
    template_name = 'pages/shop_my_posts.html'  # これから作るHTML
    context_object_name = 'shop_posts'
    paginate_by = 10  # 溜まってきた時のためにページネーションを設定

    def get_queryset(self):
        # ログインしているお店ユーザー自身の投稿だけを最新順に絞り込む
        return ShopPost.objects.filter(user=self.request.user).order_by('-created_at')

class ShopPostEditView(UpdateView):
    model = ShopPost
    fields = ['title', 'content', 'image'] # 編集させたいフィールド
    template_name = 'pages/shop_post_form.html' # 編集用テンプレート
    success_url = reverse_lazy('shop_my_posts') # 完了後のリダイレクト先

class ShopPostDeleteView(DeleteView):
    model = ShopPost
    template_name = 'pages/shop_post_confirm_delete.html' # 削除確認用テンプレート
    success_url = reverse_lazy('shop_my_posts')

@login_required
@require_POST
def toggle_shop_post_like(request, pk):
    """お店のお知らせに対するいいねの付け外し"""
    post = get_object_or_404(ShopPost, pk=pk)
    
    # すでにいいねしているかチェック
    like_queryset = ShopPostLike.objects.filter(shop_post=post, user=request.user)
    
    if like_queryset.exists():
        # すでにいいねしていれば削除
        like_queryset.delete()
    else:
        # まだなら新しく作成
        ShopPostLike.objects.create(shop_post=post, user=request.user)
        
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_POST
def add_shop_post_comment(request, pk):
    """お店のお知らせに対するコメントの追加"""
    post = get_object_or_404(ShopPost, pk=pk)
    
    # フォームを使わず、POST送信されたテキストを直接取得して保存します
    comment_text = request.POST.get('text')
    
    if comment_text:
        ShopPostComment.objects.create(
            shop_post=post,
            user=request.user,
            text=comment_text
        )
        messages.success(request, 'お店のお知らせにコメントを投稿しました！')
        
    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
@require_POST
def toggle_shop_follow(request, user_id):
    """お店アカウントに対するフォローの付け外し（Profileモデル完全準拠版）"""
    from django.contrib.auth import get_user_model
    from django.shortcuts import get_object_or_404, redirect
    
    User = get_user_model()
    target_user = get_object_or_404(User, pk=user_id)
    
    # 自分とお店の「Profile」を取り出す
    my_profile = request.user.profile
    target_profile = getattr(target_user, 'profile', None)

    if target_profile:
        # 🎯 相手のProfileがすでにフォロー中なら外す、いなければ足す
        if target_profile in my_profile.following.all():
            my_profile.following.remove(target_profile)
        else:
            my_profile.following.add(target_profile)
        
    return redirect(request.META.get('HTTP_REFERER', '/shop/'))

class ShopAgentTimelineView(LoginRequiredMixin, ListView):
    """選択された特定のお店アカウントの投稿のみを一覧表示する画面"""
    model = ShopPost
    template_name = 'pages/shop_agent_timeline.html'
    context_object_name = 'shop_posts'

    def get_queryset(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.target_user = get_object_or_404(User, pk=self.kwargs['user_id'])
        
        posts = ShopPost.objects.filter(user=self.target_user).order_by('-created_at')
        for post in posts:
            post.is_liked = post.likes_received.filter(user=self.request.user).exists()
            
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        target_user = self.target_user
        context['target_user'] = target_user
        
        # 🏪 【最重要】Userモデルから直接紐づくお店プロフィール（shop_profile）を取得
        # もし shop_profile という名前でなければ、逆参照名に合わせて自動で取得します
        shop_profile = getattr(target_user, 'shop_profile', None)
        if not shop_profile:
            # 万が一、別名で紐づいている場合のセーフティ
            shop_profile = getattr(target_user, 'profile', None)
            
        context['shop_profile'] = shop_profile  # これで店舗名と画像が100%復活します！
        
        # 📊 フォロー関係のカウント
        my_profile = self.request.user.profile
        target_profile = getattr(target_user, 'profile', None)
        
        # フォロワー数を計算（相手のProfileをフォローしている全Profileの合計）
        follower_count = 0
        if target_profile:
            from base.models import Profile
            follower_count = Profile.objects.filter(following=target_profile).count()
        elif shop_profile:
            from base.models import Profile
            follower_count = Profile.objects.filter(following=shop_profile).count()
            
        context['follower_count'] = follower_count
        return context