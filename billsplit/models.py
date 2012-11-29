from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context
from django.conf import settings
#C:\Python\Lib\site-packages;C:\Python\Lib\site-packages\django\bin;C:\Program Files\Python\Lib\site-packages


#class Location(models.Model):
#    name = models.CharField(max_length=50)
#    lon = models.IntegerField()
#    lat = models.IntegerField()
#
#    def __str__(self):
#        return self.name

class Friendship(models.Model):
    from_friend = models.ForeignKey(User, related_name='from_friend')
    to_friend = models.ForeignKey(User, related_name='to_friend')
    created = models.DateTimeField(auto_now = True)

    def __str__(self):
        return '%s %s' % (self.from_friend, self.to_friend)

class Invitation(models.Model):
    name = models.CharField(max_length=50)
    email = models.EmailField()
    code = models.CharField(max_length=20)
    sender = models.ForeignKey(User)

    def __unicode__(self):
        return u'%s, %s' % (self.sender.username, self.email)

    def send(self):
        subject = u'Invitation to dolores'
        link = 'http://%s/welcome/new/%s/' % (settings.SITE_HOST,self.code)
        template = get_template('main/invitation_email.txt')
        context = Context({
        'name': self.name,
        'link': link,
        'sender': '%s %s' % (self.sender.first_name, self.sender.last_name,),
        })
        message = template.render(context)
        send_mail(
        subject, message,
        settings.DEFAULT_FROM_EMAIL, [self.email]
        )


class Item(models.Model):
    item_id = models.IntegerField(blank=True)
    item = models.CharField(max_length=50)
    creator = models.ForeignKey(User, related_name='item_creator')
    cost = models.IntegerField()
    created = models.DateTimeField(auto_now = True)
    details = models.CharField(max_length=50)
    score = models.IntegerField(default='0')

    def __str__(self):
        return self.item

class Event(models.Model):
    creator = models.ForeignKey(User, related_name='event_creator')
    name = models.CharField(max_length=50)
    date = models.DateTimeField()
    description = models.TextField()
    members = models.ManyToManyField(User, related_name='event_members')
    items = models.ManyToManyField(Item, blank=True, null=True)
    location = models.CharField(max_length=50)
    
    def __str__(self):
        return '%s' % (self.name)

class Comment(models.Model):
    creator = models.ForeignKey(User)
    created = models.DateTimeField(auto_now = True)
    content = models.TextField(max_length=200)
    event = models.ForeignKey(Event)
    item = models.IntegerField()

    def __str__(self):
        return unicode("%s: %s" % (self.event, self.content[:60]))


class EventInvitation(models.Model):
    event = models.ForeignKey(Event)
    sender = models.ForeignKey(User, related_name='from_event')
    name = models.CharField(max_length=50)
    email = models.EmailField()
    code = models.CharField(max_length=20)

    def __unicode__(self):
        return u'%s, %s' % (self.event, self.sender)

    def send(self):
        subject = u'%s %s invited you to %s' % (self.sender.first_name, self.sender.last_name, self.event.name)
        link = 'http://%s/welcome/event/%s/' % (settings.SITE_HOST,self.code)
        template = get_template('main/event_invitation_email.txt')
        context = Context({
        'name': self.name,
        'event': self.event.name,
        'link': link,
        'sender': '%s %s' % (self.sender.first_name, self.sender.last_name,),
        })
        message = template.render(context)
        send_mail(
        subject, message,
        settings.DEFAULT_FROM_EMAIL, [self.email]
        )

class MemberBill(models.Model):
    event = models.ForeignKey(Event)
    member = models.ForeignKey(User)
    net = models.DecimalField(max_digits=10, decimal_places=2)
    
    def formattedprice(self):
        return "%01.2f" % self.net

    def __str__(self):
        return '%s %s' % (self.event, self.member)