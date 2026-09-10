from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from blog.models import Post, Follower, Following

User = get_user_model()

def user_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=profile_user).order_by("-created_on")
    followers = Follower.objects.filter(user=profile_user)
    following = Following.objects.filter(user=profile_user)

    context = {"profile_user": profile_user, 
               "posts": posts,
               "posts_count": posts.count(),
               "followers_count": followers.count(),
               "following_count": following.count(),
    }
    return render(request, "users/profile.html", context)


# Create your views here.
