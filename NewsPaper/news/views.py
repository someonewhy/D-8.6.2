from datetime import datetime
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from .filters import PostFilter
from .models import Post
from .models import BaseRegisterForm
from .forms import BasicSignupForm
from django.contrib.auth.models import User, Group


class PostListView(LoginRequiredMixin, ListView):
    model = Post
    show_content = 'content'
    template_name = 'posts.html'
    context_object_name = 'object_list'
    paginate_by = 3

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['time_now'] = datetime.utcnow()
        context['total_posts_count'] = Post.objects.count()
        context['next_sale'] = None
        return context


class PostDetail(DetailView):
    model = Post
    template_name = 'post.html'
    context_object_name = 'post'

    def post(self, request, *args, **kwargs):
        post = self.get_object()
        rating = request.POST.get('rating')

        if rating:
            post.rating = int(rating)
            post.save()

        return render(request, self.template_name, {self.context_object_name: post})


class SearchView(View):
    template_name = 'search.html'

    def get(self, request):
        query = request.GET.get('q')
        object_list = Post.objects.filter(post_type='news')

        if query:
            object_list = object_list.filter(
                Q(title__icontains=query) |
                Q(author__user__username__icontains=query) |
                Q(created_at__lt=query)
            )

        filter = PostFilter(request.GET, queryset=object_list)
        filter.form.fields['title'].label = 'Заголовок'
        filter.form.fields['author__user__username'].label = 'Автор'
        filter.form.fields['created_at__lt'].label = 'Позже указываемой даты'

        return render(request, self.template_name, {'filter': filter})


class AuthorPermissionMixin(PermissionRequiredMixin):
    permission_required = ['news.change_post', 'news.create_news_view', 'news.create_article_view']

    def dispatch(self, request, *args, **kwargs):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return super().dispatch(request, *args, **kwargs)

        if request.user.groups.filter(name='authors').exists():
            return super().dispatch(request, *args, **kwargs)

        return self.handle_no_permission()


class CreateNewsView(LoginRequiredMixin,AuthorPermissionMixin, CreateView):
    model = Post
    fields = ['author', 'post_type', 'categories', 'title', 'content']
    template_name = 'create_news.html'
    success_url = reverse_lazy('post_list')

    # Переопределение метода form_valid для установки post_type в 'news'
    def form_valid(self, form):
        form.instance.post_type = 'news'
        return super().form_valid(form)


class EditNewsView(LoginRequiredMixin, AuthorPermissionMixin, UpdateView):
    model = Post
    fields = ['author', 'post_type', 'categories', 'title', 'content']
    template_name = 'edit_news.html'
    success_url = reverse_lazy('edit_news')


class DeleteNewsView(LoginRequiredMixin, AuthorPermissionMixin, DeleteView):
    model = Post
    template_name = 'delete_news.html'
    success_url = reverse_lazy('post_list')


class CreateArticleView(LoginRequiredMixin,AuthorPermissionMixin, CreateView):
    model = Post
    fields = ['author', 'post_type', 'categories', 'title', 'content']
    template_name = 'create_article.html'
    success_url = reverse_lazy('post_list')

    def form_valid(self, form):
        form.instance.post_type = 'article'
        return super().form_valid(form)


class EditArticleView(LoginRequiredMixin, AuthorPermissionMixin, UpdateView):
    model = Post
    fields = ['author', 'post_type', 'categories', 'title', 'content']
    template_name = 'edit_article.html'
    success_url = reverse_lazy('edit_article')


class DeleteArticleView(LoginRequiredMixin, AuthorPermissionMixin, DeleteView):
    model = Post
    template_name = 'delete_article.html'
    success_url = reverse_lazy('success_url_name')


class BaseRegisterView(CreateView):
    model = User
    form = BasicSignupForm()
    form_class = BaseRegisterForm
    success_url = '/'


def signup_view(request):
    if request.method == 'POST':
        form = BasicSignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            return redirect('post_list')
    else:
        form = BasicSignupForm()
    return render(request, 'registration/signup.html', {'form': form})


class BecomeAuthorView(View):
    def get(self, request):
        user = request.user
        common_group = Group.objects.get(name='common')
        authors_group = Group.objects.get(name='authors')
        already_author = user.groups.filter(name='authors').exists()

        if not user.groups.filter(name='common').exists():
            common_group.user_set.add(user)

        if not already_author:
            authors_group.user_set.add(user)

        context = {
            'already_author': already_author,
        }

        return render(request, 'become_author.html', context)
