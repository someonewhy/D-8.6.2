from allauth.account.forms import SignupForm
from django import forms
from django.contrib.auth.models import Group
from .models import Post




class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'post_type']


class BasicSignupForm(SignupForm):
    email = forms.EmailField(label="Email")
    first_name = forms.CharField(label="Имя")
    last_name = forms.CharField(label="Фамилия")

    def save(self, request):
        user = super().save(request)
        basic_group = Group.objects.get(name='common')
        basic_group.user_set.add(user)
        return user
