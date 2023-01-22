from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .common import paginator
from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

AMOUNT = 10
User = get_user_model()


def index(request):

    template = 'posts/index.html'
    post_list = Post.objects.select_related()
    text = 'Это главная страница проекта Yatube'
    title = 'Main page'

    context = {
        'text': text,
        'title': title,
        'page_obj': paginator(request, post_list, AMOUNT),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()

    context = {
        'title': 'Сообщества',
        'group': group,
        'page_obj': paginator(request, post_list, AMOUNT),
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    posts_count = post_list.count()
    title = f'Профайл пользователя {username}'
    is_not_author = True

    following = (
        request.user.is_authenticated
        and author != request.user
        and Follow.objects.filter(
            author=author,
            user=request.user
        ).exists()
    )
    followers = author.following.all().count()
    if request.user == author:
        is_not_author = False

    context = {
        'is_not_author': is_not_author,
        'followers': followers,
        'posts_count': posts_count,
        'title': title,
        'page_obj': paginator(request, post_list, AMOUNT),
        'author': author,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    context = {
        'post': post,
        'form': CommentForm(request.POST or None),
        'comments': post.comments.select_related('post'),
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'

    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author.username)

        return render(request, template, {
            'form': form,
            'title': 'Новый пост',
        })

    form = PostForm()
    return render(request, template, {
        'form': form,
        'title': 'Новый пост',
    })


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'

    post = get_object_or_404(Post, pk=post_id)
    current_user = request.user

    if current_user != post.author:
        return redirect('posts:post_detail', post_id)

    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post,
        )

        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            return redirect('posts:post_detail', post_id)

        return render(request, template, {
            'form': form,
            'title': 'Редактировать пост',
            'is_edit': True,
            'post': post,
        })
    form = PostForm()
    return render(request, template, {
        'form': form,
        'title': 'Редактировать пост',
        'is_edit': True,
        'post_id': post_id,
    })


@login_required
def add_comment(request, post_id):

    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow_index.html'

    post_list = Post.objects.filter(
        author__following__user=request.user
    ).select_related('author', 'group')
    title = 'Following list'
    text = 'Your favorite authors'

    context = {
        'title': title,
        'text': text,
        'page_obj': paginator(request, post_list, AMOUNT),
    }

    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)

    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author,
        )

    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(
        user=request.user,
        author=author,
    ).delete()
    return redirect('posts:follow_index')
