from django.contrib import admin
from blog.models import Comment, Post, Follower, Following

# Register your models here.

# class CategoryAdmin(admin.ModelAdmin):
#     pass

class PostAdmin(admin.ModelAdmin):
    pass

class CommentAdmin(admin.ModelAdmin):
    pass

class FollowerAdmin(admin.ModelAdmin):
    pass

class FollowingAdmin(admin.ModelAdmin):
    pass


# admin.site.register(Category, CategoryAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Follower, FollowerAdmin)
admin.site.register(Following, FollowingAdmin)