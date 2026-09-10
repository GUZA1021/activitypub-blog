
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator

from blog.models import Post, Comment, Follower, Following
import requests
from blog.forms import CommentForm, PostForm, SearchUserForm

from .http_signatures import signed_post
from .acitivtypub_views import deliver_post

from urllib.parse import urlparse




from django.contrib.auth.decorators import login_required



def blog_index(request):
    # Get all blog posts from the databse and sort by the newest first. "-" -> decending order
    posts = Post.objects.all().order_by("-created_on") 
    paginator = Paginator(posts, 2)
    page_number = request.GET.get("page")

    pages = paginator.get_page(page_number)

    context = {
        'posts': pages
    }
    
    return render(request, "blog/index.html", context)


def blog_hashtag(request, hashtag):
    post = Post.objects.filter(hashtags__icontains=hashtag).order_by("-created_on")
    context = {"hashtag": hashtag, "posts": post}

    return render(request, "blog/hashtag.html", context)


def blog_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm()
    if request.method == "POST": 
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = Comment(
                author = form.cleaned_data["author"],
                body = form.cleaned_data["body"],
                post = post,
            )
            comment.save()
            return redirect(request.path_info)
        
    comments = Comment.objects.filter(post=post)
    context = {"post": post, "comments": comments, "form": CommentForm()}

    return render(request, "blog/detail.html", context)


@login_required
def blog_create(request):
    form = PostForm()
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            domain = request.get_host()
            post.activitypub_id = f"https://{domain}/ap/post/{post.pk}/"
            post.save()
            form.save_m2m()
            deliver_post(post, request)
            return redirect(post)
    context = {"form": form}

    return render(request, "blog/create.html", context)

