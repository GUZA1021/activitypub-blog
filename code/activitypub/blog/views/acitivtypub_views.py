import json

from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, JsonResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required

from datetime import datetime, timezone

from blog.models import Post, Follower, Comment, Following
from blog.forms import SearchUserForm



from .http_signatures import signed_post

import requests

User = get_user_model()

AS2_TYPES = [
    'application/activity+json',
    'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'
]

# look up a user
def get_user_or_404(username):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404

def deliver_post(post, request):
    "Sends create/Article activity to all followers inboxes"
    domain = request.get_host()
    user = post.author
    base_url = f"https://{domain}"

    activity= {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Create",
        "id": f"{base_url}/ap/post/{post.pk}/activity/",
        "actor": f"{base_url}/ap/users/{user.username}/",
        "published": post.created_on.isoformat(),
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "cc": [f"{base_url}/ap/users/{user.username}/followers/"],
        "object": {
            "type": "Note",
            "id": post.activitypub_id,
            "content": post.body,
            "published": post.created_on.isoformat(),
            "attributedTo": f"{base_url}/ap/users/{user.username}/",
            "url": f"{base_url}/post/{post.pk}/",
            "to": ["https://www.w3.org/ns/activitystreams#Public"],
            "cc": [f"{base_url}/ap/users/{user.username}/followers/"],
    }
    }

    #Sends to each followers inbox
    followers = Follower.objects.filter(user=user)
    for follower in followers:
        try:
            signed_post(user.username, follower.inbox_url, activity, domain)
        except Exception as e:
            print(f"Failed {e}")


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk) #måske fix, can crash hvis posts ikke eksistere, måske lav en 404 page
    domain = request.get_host()

    data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type": "Note",
        "id": post.activitypub_id,
        "content": post.body,
        "summary": post.body[:100],
        "published": post.created_on.isoformat(),
        "attributedTo": f"https://{domain}/ap/users/{post.author.username}/",
        "url": f"https://{domain}/post/{post.pk}/",
        "to": ["https://www.w3.org/ns/activitystreams#Public"],
        "cc": [f"https://{domain}/ap/users/{post.author.username}/followers/"],

        }
    

    
    return JsonResponse(data, content_type="application/activity+json")



def actor(request, username):
    domain = request.get_host()
    user = get_user_or_404(username) # look up the user

    data = {
        "@context":[ "https://www.w3.org/ns/activitystreams",
                    "https://w3id.org/security/v1"],
        
        "id": f"https://{domain}/ap/users/{username}/",
        "type": "Person",
        "name": user.get_full_name() or username,
        "summary": "AP blog on the fediverse",
        "inbox": f"https://{domain}/ap/users/{username}/inbox/",
        "outbox": f"https://{domain}/ap/users/{username}/outbox/",
        "followers": f"https://{domain}/ap/users/{username}/followers/",
        #"following": f"https://{domain}/ap/following/", #mangler at lave
        #"liked": f"https://{domain}ap/liked/",#  mangler at lave 
        "url": f"https://{domain}/",
        "preferredUsername": username,

        "publicKey": {
            "id": f"https://{domain}/ap/users/{username}/#main-key",
            "type": "Key",
            "owner": f"https://{domain}/ap/users/{username}/",
            "publicKeyPem": user.public_key,
        }
    }

    return JsonResponse(data, content_type="application/activity+json")

def outbox(request, username):
    user = get_user_or_404(username)
    domain = request.get_host()
    posts = Post.objects.filter(author=user).order_by("-created_on") # get all posts (newest first)

    # convert each django post into an activitystreams article
    ordered_items = []
    for post in posts:
        ordered_items.append({
            "type": "Create",
            "id": f"https://{domain}/ap/post/{post.pk}/activity/",
            "actor": f"https://{domain}/ap/users/{username}/",
            "published": post.created_on.isoformat(),

            # "to" defines primary audience of the acitivty
            # Using Public means the activity (post) is visible for everyone
            "to": ["https://www.w3.org/ns/activitystreams#Public"],

            # "cc" is used to include additional audience,
            # Here, the activity is also send to all followers of the actor
            "cc": [f"https://{domain}/ap/users/{username}/followers/"],
            "object": {
                "type" : "Note",
                "id" : post.activitypub_id,
                "content" : post.body,
                "published": post.created_on.isoformat(),
                "attributedTo": f"https://{domain}/ap/users/{username}/",
                "url": f"https://{domain}/post/{post.pk}/",
                "to": ["https://www.w3.org/ns/activitystreams#Public"],
                "cc": [f"https://{domain}/ap/users/{post.author.username}/followers/"],
            }
        })

    #return all posts as an orderedcollection
    data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type" : "OrderedCollection",
        "id" : f"https://{domain}/ap/users/{username}/outbox/",
        "totalItems" : len(ordered_items),
        "orderedItems" : ordered_items,
    }

    return JsonResponse(data, content_type="application/activity+json")


def followers(request, username):
    user = get_user_or_404(username)
    domain = request.get_host()
    follower_list = Follower.objects.filter(user=user)
    items = []
    for f in follower_list:
        items.append(f.actor_url)

    # followers collection
    data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "type" : "OrderedCollection",
        "id" : f"https://{domain}/ap/users/{username}/followers/",
        "totalItems" : len(items),
        "orderedItems" : items,
    }
    return JsonResponse(data, content_type="application/activity+json")

@login_required
def search_user(request):
    form = SearchUserForm()
    result = None

    if "handle" in request.GET:
        form = SearchUserForm(request.GET)

        if form.is_valid():            
            handle = form.cleaned_data["handle"]

            try:
                username, domain = split_handle(handle)

                webfinger_url = f"https://{domain}/.well-known/webfinger?resource=acct:{username}@{domain}"

                webfinger_response = requests.get(webfinger_url, headers={"Accept": "application/jrd+json"})

                webfinger_response.raise_for_status()

                webfinger_data = webfinger_response.json()

                actor_url = find_actor_url(webfinger_data)

                if actor_url:
                    actor_response = requests.get(actor_url, headers={"Accept": "application/jrd+json"})

                    actor_response.raise_for_status()
                    result = actor_response.json()

            except Exception as e:
                print(e)
                

    context = {
        "form": form, 
        "result": result 
    }
    return render(request, "blog/search_user.html", context)


@login_required
def follow_users(request):
    if request.method == "POST":
        actor_url = request.POST.get("actor_url")
        domain = request.get_host()

        base_url = f"https://{domain}"
        user = request.user

        try:
            headers={"Accept": "application/activity+json"}
            actor_resposne = requests.get(actor_url, headers=headers)
            #Mangler raisefor status flere steder
            actor_data = actor_resposne.json()
            remote_inbox = actor_data.get("inbox")

            if not remote_inbox:
                return redirect("search_user")

            following, created = Following.objects.get_or_create(user=user, 
                                                                 actor_url=actor_url,
                                                                 defaults={
                                                                     "inbox_url": remote_inbox,
                                                                     "display_name": actor_data.get("preferredUsername", actor_url)
                                                                 })
            
            activity = {
                "@context": "https://www.w3.org/ns/activitystreams",
                "id": f"{base_url}/ap/users/{user.username}/follow/{following.pk}/",
                "type": "Follow",
                "actor": f"{base_url}/ap/users/{user.username}/",
                "object": actor_url
            }

            signed_post(user.username, remote_inbox, activity, domain)


        except Exception as e:
            print(e)
        
    return redirect("search_user")

#Helper function

def split_handle(handle):
    r = handle.removeprefix("@")
    username, domain = r.split("@")
    return username, domain

def find_actor_url(webfinger_data):
    links = webfinger_data.get("links")

    if links:
        for x in links:
            if x.get("rel") == "self" and x.get("type") in AS2_TYPES:
                return x.get("href")
    return None

