from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

num_posts_to_show: int = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.select_related('author')
    paginator = Paginator(post_list, num_posts_to_show)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.group.select_related('group')
    paginator = Paginator(posts, num_posts_to_show)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, template, context)


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    posts = profile.posts.select_related('author')
    num_posts = posts.count()
    paginator = Paginator(posts, num_posts_to_show)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    guest = True
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=profile
        ).exists()
        guest = False
    context = {
        'author': profile,
        'page_obj': page_obj,
        'num_posts': num_posts,
        'following': following,
        'guest': guest,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.select_related('post')
    show_first_signs = 30
    title = post.text[:show_first_signs]
    author = post.author
    num_posts = author.posts.select_related().count()
    form = CommentForm(request.POST)
    context = {
        'post': post,
        'title': title,
        'author': author,
        'num_posts': num_posts,
        'comments': comments,
        'form': form
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    if request.method == 'POST':
        form = PostForm(
            request.POST,
            files=request.FILES or None,
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user.username)
        return render(request, template, {'form': form})
    form = PostForm()
    return render(request, template, {'form': form})


@login_required
def post_edit(request, pk):
    template = 'posts/create_post.html'
    post = Post.objects.get(pk=pk)
    if not post.author.username == request.user.username:
        return redirect('posts:post_detail', post_id=pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=pk)
    form = PostForm(instance=post)
    return render(request, template, {'form': form, 'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts, num_posts_to_show)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


@login_required
def profile_follow(request, username):
    current_follows = Follow.objects.filter(
        author__following__user=request.user)
    new_follow = Follow(user=request.user, author=User.objects.get(
                        username=username))
    if len(current_follows) != 0:
        for follow in current_follows:
            if (username != follow.author.username
               and new_follow.user != new_follow.author):
                new_follow.save()
    if new_follow.user != new_follow.author:
        new_follow.save()
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    follow = Follow.objects.filter(author=User.objects.get(username=username))
    follow.delete()
    return redirect('posts:follow_index')
