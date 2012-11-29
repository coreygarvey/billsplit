from django import forms
from django.core.context_processors import csrf
from django.forms.models import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from models import *


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=75)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email",)

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.username = self.cleaned_data["username"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class UserChangeForm(forms.Form):
    username = forms.CharField(max_length=30, required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=75, required=True)


class EventForm(forms.ModelForm):
    name = forms.CharField(max_length=50)
    date = forms.DateTimeField()
    description = forms.CharField(widget=forms.Textarea)
    location = forms.CharField(max_length=50)

    class Meta:
        model = Event
        fields = ("creator", "name", "date", "description", "location",)

    def save(self, commit=True):
        event = super(EventForm, self).save(commit=False)
        event.creator = self.cleaned_data["creator"]
        event.name = self.cleaned_data["name"]
        event.date = self.cleaned_data["date"]
        event.description = self.cleaned_data["description"]
        event.location = self.cleaned_data["location"]
        if commit:
            event.save()
        return event

class ItemForm(forms.ModelForm):
    item_id = forms.IntegerField(required=False)
    item = forms.CharField(max_length=50)
    cost = forms.IntegerField()
    details = forms.CharField(max_length=50, required=False)

    class Meta:
        model = Item
        fields = ("item_id", "creator", "item", "cost", "details",)

    def save(self, commit=True):
        item = super(ItemForm, self).save(commit=False)
        item.item_id = self.cleaned_data["item_id"]
        item.creator = self.cleaned_data["creator"]
        item.item = self.cleaned_data["item"]
        item.cost = self.cleaned_data["cost"]
        item.details = self.cleaned_data["details"]
        if commit:
            item.save()
        return item

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ["created","image"]

class FriendInviteForm(forms.Form):
	name = forms.CharField()
	email = forms.EmailField()

class EventEmailForm(forms.Form):
	event = forms.CharField()
	name = forms.CharField(required=False)
	email = forms.EmailField()

class EventInviteForm(forms.Form):
	event = forms.CharField()
	name = forms.CharField(required=False)
	email = forms.EmailField(required=False)

class ItemScoreForm(forms.Form):
	item = forms.IntegerField()
	score = forms.IntegerField()

class MemberBillForm(forms.ModelForm):
    event = forms.CharField()
    member = forms.CharField()
    net = forms.FloatField()

    class Meta:
        model = MemberBill
        fields = ("event","member","net",)

    def save(self, commit=True):
        bill = super(MemberBillForm, self).save(commit=False)
        bill.event = self.cleaned_data["event"]
        bill.member = self.cleaned_data["member"]
        bill.net = self.cleaned_data["net"]
        if commit:
            bill.save()
        return bill