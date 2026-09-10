from django import forms
from blog.models import Post

class CommentForm(forms.Form):
    author = forms.CharField(max_length=50, widget=forms.TextInput(
        attrs={"class": "form-control", "placeholder": "Your Name"}))
    
    body = forms.CharField(
        widget=forms.Textarea(
        attrs={"class": "form-control", "placeholder": "Leave a comment"}
    ))


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "body", "hashtags"]

        widgets = {
            "title": forms.TextInput(attrs={"class": "input", "placeholder": "Title"}),
            "body": forms.Textarea(attrs={"class": "textarea", "placeholder": "Write your post...."}),
            "hashtags": forms.TextInput(attrs={"class": "input", "placeholder": "#activitypub"}),       
        }


class SearchUserForm(forms.Form):
    handle = forms.CharField(max_length=200, widget=forms.TextInput(
        attrs={"class": "input", "placeholder": "@username@domain"}
    ))