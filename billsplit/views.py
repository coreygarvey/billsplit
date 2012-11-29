from django.http import HttpResponse, HttpResponseRedirect
import models
from forms import *
from django.shortcuts import render_to_response
from django.template import RequestContext
from models import *
from django.db.models import F
from django.contrib import auth
from django.contrib.auth import login, logout, authenticate
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from django.conf import settings
from billsplit.settings import FB_APP_ID, FB_APP_SECRET
import httplib
from django.utils import simplejson
import re
from decimal import Decimal
from django.db.models import Min
from datetime import datetime

def open(request):
    return render_to_response("main/open.html", context_instance=RequestContext(request)
    )


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save();
            new_user = authenticate(username=request.POST['username'], password=request.POST['password1'])
            login(request, new_user)
            return HttpResponseRedirect('/home/')    
    else:
        form = RegistrationForm()
    return render_to_response("registration/register.html", {
        'form': form}, context_instance=RequestContext(request)
    )


def display_home(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    user = request.user
    events = Event.objects.filter(members=user)
    return render_to_response('main/home2.html',{'events':events}, context_instance=RequestContext(request))

def my_account(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    user = request.user
    events = Event.objects.filter(members=user)
    if request.method == 'POST':
        p = request.POST.copy()
        if 'confirm' in p:
            user = authenticate(username=p['username'], password=p['password'])
            if user is not None:
                return HttpResponseRedirect('/edit_account/')
            else:
                return HttpResponseRedirect('/')
    return render_to_response('main/my_account.html',{'events':events}, context_instance=RequestContext(request))


def edit_account(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    user = request.user
    events = Event.objects.filter(members=user)
    if request.method == 'POST':
        p = request.POST.copy()
        form = UserChangeForm(p)
        if form.is_valid():
            old_user = User.objects.get(id=p['id'])
            old_user.username = p['username']
            old_user.first_name = p['first_name']
            old_user.last_name = p['last_name']
            old_user.email = p['email']
            
            old_user.save()
            return HttpResponseRedirect('/my_account/')
    else:
        form = UserChangeForm()
    return render_to_response('main/edit_account.html',{'events':events, 'form':form}, context_instance=RequestContext(request))

def display_event(request, event):
    event_id=event
    event = Event.objects.get(id=event_id)
    members = event.members.all()
    comments = Comment.objects.filter(event=event).order_by('-created') 
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    if not request.user in members:
        return HttpResponseRedirect('/home/')
    else:
        if request.method == 'POST':
            p = request.POST.copy()
            if 'cost' in p:
                cost = re.sub("[^\d\.]", "", p['cost'])
                p['cost'] = cost
            item_form = ItemForm(p)
            comment_form = CommentForm(p)
            event_invite_form=EventInviteForm(p)
            event_email_form=EventEmailForm(p)
            item_score = ItemScoreForm(p)
            user = request.user
            events = Event.objects.filter(members=user)
            if 'delete' in p:
                item = Item.objects.get(id=p['item'])
                item.delete()
                comments = Comment.objects.filter(item=p['item'])
                comments.delete()
                return HttpResponseRedirect('/event/%s/' % event.id)
            if 'delete-comment' in p:
                comment = Comment.objects.get(id=p['comment'])
                comment.delete()
                return HttpResponseRedirect('/event/%s/' % event.id)
            if 'leave' in p:
                member_items = event.items.filter(creator=user)
                for item in member_items:
                    event.items.remove(item)
                member_comments = comments.filter(creator=user)
                member_comments.delete()
                event.members.remove(user)
                return HttpResponseRedirect('/home/')
            if item_form.is_valid():
                item_id = int(request.POST['item_id']) 
                if item_id > 0:
                    old_item = Item.objects.get(id=item_id)
                    new_item = ItemForm(p, instance=old_item)
                    new_item.save()
                    return HttpResponseRedirect('/event/%s/' % event.id)
                else:   
                    new_item = item_form.save();
                    event.items.add(new_item)
                    items = event.items.all()
                    comments = Comment.objects.filter(event=event.id)
                    members = event.members.all()
                    return HttpResponseRedirect('/event/%s/' % event.id)
            if event_email_form.is_valid():
                if request.POST['email']:
                    email = event_email_form.cleaned_data['email']
                    name = event_email_form.cleaned_data['name']
                    event_invitation = EventInvitation(event=event,sender=request.user, email=email, name=name, code=User.objects.make_random_password(20))
                    event_invitation.save()
                    event_invitation.send()
                    return HttpResponseRedirect('/event/%s/' % event.id)
                else:
                    event = Event.objects.get(id=event_invite_form.cleaned_data['event'])
                    name = request.POST['user_search']
                    event_invitation = EventInvitation(event=event,sender=request.user,email=form.cleaned_data['email'], name=name, code=User.objects.make_random_password(20))
                    event_invitation.save()
                    event_invitation.send()
                    return HttpResponseRedirect('/event/%s/' % event.id)
            if item_score.is_valid():
                if int(request.POST['score']) > 0:
                    item = Item.objects.get(id=request.POST['item'])
                    item.score = item.score + 1
                    item.save()
                    return HttpResponseRedirect('/event/%s/' % event.id)
                else:
                    item = Item.objects.get(id=request.POST['item'])
                    item.score = item.score - 1
                    item.save()
                    return HttpResponseRedirect('/event/%s/' % event.id)
            if comment_form.is_valid():
                    comment_form.save()
                    return HttpResponseRedirect('/event/%s/' % event.id)
            else:
                if 'payment' in p:
                    paypalList = {}
                    payment = float(request.POST['payment'])
                    bills_owed = MemberBill.objects.filter(event=event).filter(net__lt=0).order_by('net')
                    most_owed = MemberBill.objects.filter(event=event).aggregate(Min('net'))
                    most_owed_amount = most_owed['net__min']
                    while (float(most_owed_amount) < float(0.00)) and (float(payment) > float(0.00)):
                        bills_owed_first = bills_owed.filter(net = most_owed_amount);
                        number_owed_first = len(bills_owed_first);
                        try:
                            next_owed_amount = bills_owed[number_owed_first].net;                            
                        except:
                            next_owed_amount = 0;
                        delta = next_owed_amount - most_owed_amount;
                        max_pay_first = delta*number_owed_first;
                        member_payment = payment/number_owed_first;
                        if payment <= max_pay_first:
                            for bill in bills_owed_first:
                                member = bill.member
                                amount = float(member_payment);
                                try:
                                    paypalList[member] += amount
                                except:
                                    paypalList[member] = amount
                                old_net = float(bill.net)
                                new_net = old_net + amount;
                                bill.net = "%01.2f" % new_net
                                bill.save()
                                payment = payment - amount
                        else:
                            for bill in bills_owed_first:
                                member = bill.member
                                amount = float(delta);
                                try:
                                    paypalList[member] += amount
                                except:
                                    paypalList[member] = amount
                                old_net = float(bill.net)
                                new_net = old_net + amount;
                                bill.net = "%01.2f" % new_net
                                bill.save()
                                payment = payment - amount
                        most_owed = MemberBill.objects.filter(event=event).aggregate(Min('net'))
                        most_owed_amount = most_owed['net__min']
                        print paypalList
                    else:
                        paypal_link = "actionType=PAY&cancelUrl=http://billsplit.co/home&currencyCode=USD&feesPayer=EACHRECEIVER&requestEnvelope.errorLanguage=en_US&"
                        paypalFinal = {}
                        bill_number = 0;
                        while (bill_number <= 5):
                            for bill in paypalList:
                                bill_owner = User.objects.get(username=paypalList.keys()[bill_number])
                                
                                email = bill_owner.email
                                amount = paypalList[bill_owner];
                                paypal_email = 'receiverList.receiver(%d).email=%s&' % (bill_number, email);
                                paypal_amount = 'receiverList.receiver(%d).amount=%s&' % (bill_number, amount);
                                paypal_link += paypal_email
                                paypal_link += paypal_amount
                                bill_number += 1
                            bill_number = 6
                        paypal_link += 'returnUrl=http://billsplit.co/home'
                        
                         
                        PAYPAL_TEST_USERNAME = 'cgarv1_1351649473_biz_api1.gmail.com'
                        PAYPAL_TEST_PASSWORD = '1351649526'
                        PAYPAL_TEST_SIGNATURE = 'AFcWxV21C7fd0v3bYYYRCpSSRl31AkcSi3SYtvrHlHgNhUeijiBWqtou'
                        PAYPAL_APPLICATION_ID = 'APP-80W284485P519543T'
                        headers = {
                        "X-PAYPAL-SECURITY-USERID": PAYPAL_TEST_USERNAME,
                        "X-PAYPAL-SECURITY-PASSWORD": PAYPAL_TEST_PASSWORD,
                        "X-PAYPAL-SECURITY-SIGNATURE": PAYPAL_TEST_SIGNATURE,
                        "X-PAYPAL-REQUEST-DATA-FORMAT": "NV",
                        "X-PAYPAL-RESPONSE-DATA-FORMAT": "JSON",
                        "X-PAYPAL-APPLICATION-ID": PAYPAL_APPLICATION_ID,
                        }
                        paramString = paypal_link 
                        print 'Making PayPal call with paramString: %s' % paramString
                        connection = httplib.HTTPSConnection('svcs.sandbox.paypal.com', 443)
                        connection.request("POST", '/AdaptivePayments/Pay', paramString, headers)
                        response = connection.getresponse().read()
                        connection.close() # close the connection
                        print 'Got PayPal response: %s' % (response)
                        parsed_data = simplejson.loads(response)
                        paykey = parsed_data['payKey']
                        print paykey
                        events = Event.objects.filter(members=user)
                        print paypalList
                        context={'paypalList':paypalList, 'paykey':paykey,'event':event, 'events':events, 'members':members,}
                        return render_to_response('main/pay_confirm.html', context, context_instance=RequestContext(request))

        else:
            user = request.user
            events = Event.objects.filter(members=user)
            item_form=ItemForm()
            comment_form=CommentForm()
            
            items = event.items.all().order_by('-score')
            event_cost = 0;
            for item in items:
                event_cost = event_cost + item.cost;
            members_total = len(members);
            member_cost = float(event_cost)/float(members_total);
            member_cost = Decimal(str(member_cost)).quantize(Decimal('.01'))
            my_items = Item.objects.filter(creator=user)
            for member in members: 
                member_items =  items.filter(creator=member)
                user_cost = 0;
                for item in member_items:
                     user_cost = user_cost + item.cost;
                net = member_cost - user_cost;
                net = "%01.2f" % net
                try:
                    old_member_bill = MemberBill.objects.get(event=event, member=member)
                    old_member_bill.net = net
                    old_member_bill.save()
                except:
                    new_bill = MemberBill(member=member, event=event, net=net)
                    new_bill.save()
            user_items =  items.filter(creator=user)
            user_cost = 0;
            for item in user_items:
                 user_cost = user_cost + item.cost;
            net = member_cost - user_cost;
            net = "%01.2f" % net
            bills_owed = MemberBill.objects.filter(event=event).filter(net__lt=0).order_by('net')
            return render_to_response('main/event2.html', {'bills_owed':bills_owed, 'net':net,'user_cost':user_cost,'event_cost':event_cost, 'members_total':members_total, 'member_cost':member_cost,'event':event, 'events':events, 'items':items,'my_items':my_items, 'members':members, 'comments':comments, 'item_form': item_form, 'comment_form': comment_form}, context_instance=RequestContext(request))

def new_item(request, event):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    else:
        user = request.user
        event = Event.objects.get(id=event)
        events = Event.objects.filter(members=user)
        user_id = int(user.id); 
        form = ItemForm()
        if request.method == 'POST':
            item_form = ItemForm(request.POST)
            if item_form.is_valid():
                item_id = int(request.POST['item_id']) 
                if item_id > 0:
                    old_item = Item.objects.get(id=item_id)
                    new_item = ItemForm(p, instance=old_item)
                    new_item.save()
                    event = Event.objects.get(id=event)
                    return HttpResponseRedirect('/event/%s/' % event.id)
                else:
                    new_item = item_form.save();
                    event = Event.objects.get(id=event.id)
                    event.items.add(new_item)
                    items = event.items.all()
                    comments = Comment.objects.filter(event=event.id)
                    members = event.members.all()
                    return HttpResponseRedirect('/event/%s/' % event.id)
        return render_to_response('main/new_item.html', {'event':event, 'events':events, 'form': form}, context_instance=RequestContext(request))



def new_event(request):
    user = request.user
    events = Event.objects.filter(members=user)
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        p = request.POST.copy()
        if p['daypart']=='pm':
            hour = int(p['hour'])+12
        else:
            hour = int(p['hour'])
        minutes = int(p['minutes'])
        if minutes == 0:
            minutes = 00
        time = '%s:%s:00' % (hour, minutes)
        date = '%s %s' % (p['date'], time)  
        dt_obj = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        print dt_obj  
        e = {}
        e['name'] = p['name']
        e['date'] = dt_obj
        e['description'] = p['description']
        e['location'] = p['location']
        p['date'] = dt_obj
        print e
        print request.POST
        print p
        form = EventForm(p)
        if form.is_valid():
            new_event = form.save();
            event = Event.objects.get(id=new_event.id)
            event.members.clear()
            event.members.add(request.user)
            return HttpResponseRedirect('/event/%s/' % event.id)
    else:
        form = EventForm()
    return render_to_response('main/new_event2.html', {
        'form': form, 'events':events}, context_instance=RequestContext(request)
    )

def friend_invite(request):
    if request.method == 'POST':
        form = FriendInviteForm(request.POST)
        if form.is_valid():
            invitation = Invitation(name=form.cleaned_data['name'],email=form.cleaned_data['email'],code=User.objects.make_random_password(20),sender=request.user)
            invitation.save()
            invitation.send()
            return HttpResponseRedirect('/invite/')
    else:
        form = FriendInviteForm()
        variables = RequestContext(request, {'form': form})
    return render_to_response('main/friend_invite.html', variables) 

def event_accept(request, code):
    try:
        event_invitation = EventInvitation.objects.get(code__exact=code)
        request.session['event_invitation'] = event_invitation.id
        return HttpResponseRedirect('/event_join/')
    except:
        return HttpResponseRedirect('/')

def event_join(request):
    register_form = RegistrationForm()
    if request.method == 'POST':
        if 'login' in request.POST:
            user = auth.authenticate(username=request.POST['login-username'], password=request.POST['login-password'])
            if user is not None:
                if 'event_invitation' in request.session:
                    event_invitation = EventInvitation.objects.get(id=request.session['event_invitation'])
                    event = Event.objects.get(id=event_invitation.event.id)
                    event_invitation.delete()
                    add_member = event.members.add(user)
                    del request.session['event_invitation']
                    login(request, user)
                return HttpResponseRedirect('/event/%s/' % event.id )
            else:
                register_form = RegistrationForm()
                return render_to_response("main/event_join.html", {'register_form': register_form}, context_instance=RequestContext(request))
        if 'register' in request.POST:
            register_form = RegistrationForm(request.POST)
            if register_form.is_valid():
                new_user = register_form.save();
                if 'event_invitation' in request.session:
                    # Retrieve the invitation object.
                    event_invitation = EventInvitation.objects.get(id=request.session['event_invitation'])
                    # Create friendship from user to sender.
                    # friendship = Friendship(from_friend=new_user,to_friend=event_invitation.sender)
                    # friendship.save()
                    # Create friendship from sender to user.
                    # friendship = Friendship(from_friend=event_invitation.sender,to_friend=new_user)
                    # friendship.save()
                    event = Event.objects.get(id=event_invitation.event.id)
                    # Delete the invitation from the database and session.
                    event_invitation.delete()
                    add_member = event.members.add(new_user)
                    del request.session['event_invitation']
                    new_user = auth.authenticate(username=request.POST['username'], password=request.POST['password1'])
                    login(request, new_user)
                    return HttpResponseRedirect('/event/%s/' % event.id )
    return render_to_response("main/event_join.html", {
        'register_form': register_form}, context_instance=RequestContext(request)
    )



def friend_accept(request, code):
    invitation = get_object_or_404(Invitation, code__exact=code)
    request.session['invitation'] = invitation.id
    return HttpResponseRedirect('/welcome/new/')


def invite_register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save();
            if 'invitation' in request.session:
                # Retrieve the invitation object.
                invitation = Invitation.objects.get(id=request.session['invitation'])
                # Create friendship from user to sender.
                friendship = Friendship(from_friend=new_user,to_friend=invitation.sender)
                friendship.save()
                # Create friendship from sender to user.
                friendship = Friendship(from_friend=invitation.sender,to_friend=new_user)
                friendship.save()
                # Delete the invitation from the database and session.
                invitation.delete()
                del request.session['invitation']
            new_user = auth.authenticate(username=request.POST['username'], password=request.POST['password1'])
            login(request, new_user)
            return HttpResponseRedirect('/')    
    else:
        form = RegistrationForm()
    return render_to_response("registration/register.html", {
        'form': form}, context_instance=RequestContext(request)
    )

    
def event_invite(request, event):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    else:
        user = request.user
        event_id = event
        event = Event.objects.get(id=event_id)
        members = event.members.all()
        events = Event.objects.filter(members=user)
        user_id = int(user.id)
        items = event.items.all()
        form = EventInviteForm()
        item_form=ItemForm()
        comment_form=CommentForm()
        comments = Comment.objects.filter(event=event).order_by('-created')
        event_cost = 0;
        for item in items:
            event_cost = event_cost + item.cost;
            print event_cost
        members_total = len(members);
        member_cost = float(event_cost)/float(members_total);
        member_cost = Decimal(str(member_cost)).quantize(Decimal('.01'))
        my_items = Item.objects.filter(creator=user)
        for member in members: 
            member_items =  items.filter(creator=member)
            user_cost = 0;
            for item in member_items:
                 user_cost = user_cost + item.cost;
            net = member_cost - user_cost;
            net = "%01.2f" % net
            try:
                old_member_bill = MemberBill.objects.get(event=event, member=member)
                old_member_bill.net = net
                old_member_bill.save()
            except:
                new_bill = MemberBill(member=user, event=event, net=net)
                new_bill.save()
                
        if request.method == 'POST':
            form = EventInviteForm(request.POST)
            if form.is_valid():
                if request.POST['email']:
                    event = Event.objects.get(id=form.cleaned_data['event'])
                    email = form.cleaned_data['email']
                    print email
                    name = form.cleaned_data['name']
                    event_invitation = EventInvitation(event=event,sender=request.user, email=email, name=name, code=User.objects.make_random_password(20))
                    event_invitation.save()
                    event_invitation.send()
                    event=event.id
                else:
                    event = Event.objects.get(id=form.cleaned_data['event'])
                    name = request.POST['user_search']
                    first_name_matches = User.objects.get(first_name__icontains=name)
                    event_invitation = EventInvitation(event=event,sender=request.user,email=form.cleaned_data['email'], name=name, code=User.objects.make_random_password(20))
                    event_invitation.save()
                    event_invitation.send()           
        return render_to_response('main/event_invite.html', {'net':net,'user_cost':user_cost,'event_cost':event_cost, 'members_total':members_total, 'member_cost':member_cost,'event':event, 'events':events, 'form': form, 'members':members, 'comments':comments, 'item_form': item_form, 'comment_form': comment_form}, context_instance=RequestContext(request))




def event_invite1(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/')
    if request.method == 'POST':
        receiver = request.POST['receiver']
        form = EventInviteForm(request.POST)
        if form.is_valid():
            if receiver:
                event = Event.objects.get(id=form.cleaned_data['event'])
                receiver = User.objects.get(id=form.cleaned_data['receiver'])
                email = receiver.email
                name = receiver.name
                event_invitation = EventInvitation(event=event,sender=request.user, receiver=receiver, email=email, name=name, code=User.objects.make_random_password(20))
                event_invitation.save()
                event_invitation.send()
                return HttpResponseRedirect('/event_invite/%s/' % event.id)
            else:
                event = Event.objects.get(id=form.cleaned_data['event'])
                name = request.POST['user_search']
                first_name_matches = User.objects.get(first_name__icontains=name)
                event_invitation = EventInvitation(event=event,sender=request.user,email=form.cleaned_data['email'], name=name, code=User.objects.make_random_password(20))
                event_invitation.save()
                event_invitation.send()
                return HttpResponseRedirect('/event_invite/%s/' % event.id)
    else:
        form = EventInviteForm()
        variables = RequestContext(request, {'form': form})
    return render_to_response('main/event_invite.html', variables)

def search(request):
    name = request.GET.get('s', '').strip().split(' ', 1)
    client_set = Client.objects.all()

    if len(name) == 2:
        first_name, last_name = name
        client_set = client_set.filter(
            first_name__icontains=first_name,
            last_name__icontains=last_name,
        )
    else:
        name = name[0]
        client_set = client_set.filter(
            client_set.filter(first_name__icontains=name)
            | client_set.filter(last_name__icontains=name)
        )

    return render_to_response("search.html", {
        "client_list": client_list,
        "query": query
    }, context_instance=RequestContext(request))


def event_invite_register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            new_user = form.save();
            if 'invitation' in request.session:
                # Retrieve the invitation object.
                invitation = EventInvitation.objects.get(id=request.session['invitation'])
                # Create friendship from user to sender.
                friendship = Friendship(from_friend=new_user,to_friend=invitation.sender)
                friendship.save()
                # Create friendship from sender to user.
                friendship = Friendship(from_friend=invitation.sender,to_friend=new_user)
                friendship.save()
                # Delete the invitation from the database and session.
                invitation.delete()
                del request.session['invitation']
            new_user = auth.authenticate(username=request.POST['username'], password=request.POST['password1'])
            login(request, new_user)
            return HttpResponseRedirect('/')    
    else:
        form = RegistrationForm()
    return render_to_response("registration/register.html", {
        'form': form}, context_instance=RequestContext(request)
    )

def index(request):
    context = {}
    return render_to_response('main/index.html', context,
        context_instance=RequestContext(request))

def paypal(request):
    if request.method == 'POST':
        amount = request.POST['amount']
        email = request.POST['email']
        PAYPAL_TEST_USERNAME = 'cgarv1_1351649473_biz_api1.gmail.com'
        PAYPAL_TEST_PASSWORD = '1351649526'
        PAYPAL_TEST_SIGNATURE = 'AFcWxV21C7fd0v3bYYYRCpSSRl31AkcSi3SYtvrHlHgNhUeijiBWqtou'
        PAYPAL_APPLICATION_ID = 'APP-80W284485P519543T'
        headers = {
        "X-PAYPAL-SECURITY-USERID": PAYPAL_TEST_USERNAME,
        "X-PAYPAL-SECURITY-PASSWORD": PAYPAL_TEST_PASSWORD,
        "X-PAYPAL-SECURITY-SIGNATURE": PAYPAL_TEST_SIGNATURE,
        "X-PAYPAL-REQUEST-DATA-FORMAT": "NV",
        "X-PAYPAL-RESPONSE-DATA-FORMAT": "JSON",
        "X-PAYPAL-APPLICATION-ID": PAYPAL_APPLICATION_ID,
        }
        paramString = "actionType=PAY&cancelUrl=http://localhost:8000/register&currencyCode=USD&feesPayer=EACHRECEIVER&requestEnvelope.errorLanguage=en_US&receiverList.receiver(0).amount=%s&receiverList.receiver(0).email=%s&returnUrl=http://localhost:8000/register" % (amount, email)
        print 'Making PayPal call with paramString: %s' % paramString
        connection = httplib.HTTPSConnection('svcs.sandbox.paypal.com', 443)
        connection.request("POST", '/AdaptivePayments/Pay', paramString, headers)
        response = connection.getresponse().read()
        connection.close() # close the connection
        print 'Got PayPal response: %s' % (response)
        parsed_data = simplejson.loads(response)
        paykey = parsed_data['payKey']
        print paykey
        form = False
        return render_to_response("main/payment_test.html", {
            'form': form, 'paykey': paykey}, context_instance=RequestContext(request)
        )
    else:
        form = True
        return render_to_response("main/payment_test.html", {'form': form}, context_instance=RequestContext(request))


