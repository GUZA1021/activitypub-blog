from django.http import JsonResponse
from django.contrib.auth import get_user_model

User = get_user_model()

def webfinger(request):
    resource = request.GET.get("resource")

    if not resource:
        return JsonResponse({"error": "resource parameter is required"}, status = 400)
    
    if not resource.startswith("acct:"):
        return JsonResponse({"error": "resource should start with 'acct:' "}, status = 400)
    
    #Parse username and domain from acct:username@domain, removes acct prefix
    try:
        username, domain = resource[5:].split("@")
    except:
        return JsonResponse({"error": "invalid resource parameter"}, status = 400)
    
    if not username or not domain:
        return JsonResponse({"error": "invalid parameter"}, status = 400)
    

    #Check if domain matches this server
    host = request.get_host()
    if domain != host:
        return JsonResponse({"error": "invalid domain"}, status = 400)
    
    #Check that user exists on this server
    try:
        User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({"error": "user not found"}, status = 404)
    
    #Return a JRD file

    return JsonResponse({"subject" : resource, 
                         "links" : [
                             {
                                 "rel" : "self", 
                                 "type" : "application/activity+json", 
                                 "href": f"https://{host}/ap/users/{username}/"
                                 }
                            ]
                        },
                        content_type="application/jrd+json")