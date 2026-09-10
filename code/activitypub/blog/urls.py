from django.urls import path
from .views import blog_views
from .views.auth_views import SignUpView
from .views import acitivtypub_views
from .views import activitypub_inbox
from .views import webfinger

urlpatterns = [
    # blog
    path("", blog_views.blog_index, name="blog_index"),
    # path("users/<str:username>/", blog_views.user_profile, name="user_profile"),
    path("post/create/", blog_views.blog_create, name="blog_create"),
    path("post/<int:pk>/", blog_views.blog_detail, name="blog_detail"),
    path("hashtag/<hashtag>/", blog_views.blog_hashtag, name="blog_hashtag"),
    path("search/", acitivtypub_views.search_user, name="search_user"),
    path("follow/", acitivtypub_views.follow_users, name="follow_users"),
    #Authentication
    path("accounts/signup/", SignUpView.as_view(), name="signup"),
    path("ap/post/<int:pk>/", acitivtypub_views.post_detail, name="post_detail_json"),
    #ActivityPub
    path("ap/users/<str:username>/", acitivtypub_views.actor, name="actor"),
    path("ap/users/<str:username>/inbox/", activitypub_inbox.inbox, name="inbox"),
    path("ap/users/<str:username>/outbox/", acitivtypub_views.outbox, name="outbox"),
    path("ap/users/<str:username>/followers/", acitivtypub_views.followers, name="followers"),
    #WebFinger
    path(".well-known/webfinger", webfinger.webfinger, name="webfinger"),


]

