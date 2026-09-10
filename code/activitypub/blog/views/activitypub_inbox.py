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


def follow_request(activity, user, domain, username):
    actor_value = activity.get("actor")
    actor_object = activity.get("object")

    my_actor = f"https://{domain}/ap/users/{username}/"

    # Check if the follow is actually for this blog
    if actor_object != my_actor:
        return {"error" : "Follow destination is not for this actor"}, 400

    # Saving actor URL short version
    if not actor_value:
        return {"error" : "No actor in follow activity"}, 400
    
    # Fetch followers actor json to get their inbox URL. Prodromu required to deliver Accept to followers inbox
    try:
        response = requests.get(actor_value,headers={"Accept" : "application/activity+json"}, timeout = 5)
        actor_data = response.json()
        follower_inbox = actor_data.get("inbox")
    except Exception:
        return {"error" : "Could not fetch follower actor"}, 400
    
    if not follower_inbox:
        return {"error" : "Could not find follower inbox"}, 400
    
    Follower.objects.update_or_create(actor_url = actor_value, user = user, defaults={"display_name" : actor_data.get("preferredUsername",actor_value), "inbox_url" : follower_inbox} )

    # Accept activity 
    accept_data = {
        "@context" : "https://www.w3.org/ns/activitystreams",
        "id": f"https://{domain}/ap/users/{username}/accept/{datetime.now(timezone.utc).timestamp()}",
        "type" : "Accept",
        "actor" : my_actor,
        "object" : activity,
    }

    # Post it ito followers inbox
    try:
        signed_post(username, follower_inbox, accept_data, domain)
    except Exception as e:
        print(f"Failed {e}")


    return {"status": "ok"}, 200

# Unfollow handling
# W3C spec section 7.5

def undo_request(activity, user):
    obj = activity.get("object", {})
    if obj.get("type") == "Follow":
        actor_value = activity.get("actor")
        Follower.objects.filter(actor_url=actor_value, user = user).delete()
        return {"status" : "ok"}, 200
    return {"status": "ignored"}, 202


def create_request(activity):
    object = activity.get("object")
    inReplyTo = object.get("inReplyTo")

    #Only accept type = Note
    if object.get("type") != "Note":
        return {"status": "ignore"}, 202
    
    #Check if note is a reply
    if not object.get("inReplyTo"):
        return {"status": "not a reply"}, 202
    
    try:
        post = Post.objects.get(activitypub_id=inReplyTo)
    except Post.DoesNotExist:
        return {"error": "Post does not exist"}, 404
    
    content = object.get("content")

    actor = activity.get("actor")

    comment_id = object.get("id")

    if not Comment.objects.filter(comment_id = comment_id).exists():
        Comment.objects.create(post=post, author=actor, comment_id=comment_id, body=content)

    return {"status": "reply saved"}, 200


def like_request(activity):

    object = activity.get("object")

    post = Post.objects.get(activitypub_id=object)
    post.likes += 1
    post.save()

    return ({"status": "ok"}, 200)



@csrf_exempt
def inbox(request, username):
    domain = request.get_host()
    user = get_object_or_404(User, username=username)
    # my_actor = f"https://{domain}/ap/users/{username}/"

    if request.method == "GET":
        data = {
        "@context": "https://www.w3.org/ns/activitystreams",
        "id": f"https://{domain}/ap/users/{username}/inbox/",
        "type": "OrderedCollection",
        "totalItems" : 0,
        "orderedItems" : [],       
        }
        return JsonResponse(data, content_type="application/activity+json")


    # Inbox is meant to recieve POST request from other servers
    if request.method != "POST":
        return JsonResponse({"error" : "Method not allowed"}, status = 405)
    
    try:
        body = request.body.decode("utf-8")
        activity = json.loads(body)
    except(json.JSONDecodeError):
        return JsonResponse({"error" : "Invalid JSON"}, status=400)
    
    activity_type = activity.get("type")
    
    match activity_type:
        case "Follow":
            result, status_code = follow_request(activity, user, domain, username)
        case "Undo":
            result, status_code = undo_request(activity, user)
        case "Create":
            result, status_code = create_request(activity)
        case "Like":
            result, status_code = like_request(activity)
        case _:
            return JsonResponse({"status": "activity type not supported yet"}, status=202, content_type="application/activity+json")
            


    return JsonResponse(result, status=status_code, content_type="application/activity+json")


