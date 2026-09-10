from django.db import models
from django.urls import reverse
from django.conf import settings

# Create your models here.

# class Category(models.Model):
#     name = models.CharField(max_length=30)

#     class Meta:
#         verbose_name_plural = "categories"

#     def __str__(self):
#         return self.name

class Post(models.Model):
    title = models.CharField(max_length=250)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    # categories = models.ManyToManyField("Category", related_name="posts")
    hashtags = models.CharField(max_length=100, blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    activitypub_id = models.URLField(blank=True, unique=True, null=True)

    def get_absolute_url(self):
        return reverse("blog_detail", args=[self.pk])
    
    def __str__(self):
        return self.title



class Comment(models.Model):
    author = models.CharField(max_length=500)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    post = models.ForeignKey("Post", on_delete=models.CASCADE)
    comment_id = models.URLField(blank=True, unique=True, null=True)


    def __str__(self):
        return f"{self.author} on '{self.post}'"

class Follower(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers", null=True, blank=True)
    actor_url = models.URLField()
    inbox_url = models.URLField(blank=True)
    display_name = models.CharField(max_length=500, blank=True)
    followed_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["actor_url", "user"], name="unique_follower"
            )
        ]

    def __str__(self):
        return self.display_name or self.actor_url
    

    
class Following(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following", null=True, blank=True)
    actor_url = models.URLField()
    inbox_url = models.URLField()
    display_name = models.CharField(max_length=500, blank=True)
    followed_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["actor_url", "user"], name="unique_following"
            )
        ]

    def __str__(self):
        return self.display_name or self.actor_url
    


