from django.conf.urls.defaults import patterns, include, url
# from django.conf.urls.defaults import *
import views
from django.contrib import admin
from django.views.static import * 
from django.conf import settings

admin.autodiscover()

urlpatterns = patterns('',
    (r'^billsplit/media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    url(r'^admin/', include(admin.site.urls)),
#    (r'^fbconnect/$', views.index),
	(r'^paypal/$', views.paypal),
    (r'^account/', include('django.contrib.auth.urls')),
#    (r'^login/$', login),
    (r'^register/$',  views.register),

    (r'^home/$', views.display_home),
#    (r'^events/$', views.display_my_events),
    (r'^event/(\d+)/$', views.display_event),
    (r'^event/(\d+)/new_item/$', views.new_item),
#    (r'^(\d+)/list/$', views.display_event_list),
#    (r'^(\d+)/new_item/$', views.new_item),
#    (r'^(\d+)/my_items/$', views.display_my_items),
#    (r'^(\d+)/details/$', views.display_details),
#    (r'^invites/$', views.display_invites),
    (r'^new_event/$', views.new_event),
#    (r'^(\d+)/new_invite/$', views.new_invite),
#    (r'^(\d+)/final/$', views.display_final_list),
#    (r'^(\d+)/checkout/$', views.display_checkout),
#    (r'^(\d+)/pay/$', views.display_pay),
#    (r'^(\d+)/thanks/$', views.display_return),
	(r'^invite/$', views.friend_invite),
	(r'^welcome/new/(\w+)/$', views.friend_accept),
	(r'^welcome/new/$', views.invite_register),
	(r'^welcome/event/(\w+)/$', views.event_accept),
	(r'^event_join/$', views.event_join),
    (r'^event/(\d+)/event_invite/$', views.event_invite),
    (r'^edit_account/$', views.edit_account),
    (r'^my_account/$', views.my_account),
)

urlpatterns += patterns('django.contrib.auth.views',
    (r'^$', 'login'),
    (r'^logout/$', 'logout'),
    (r'^password_change/$',  'password_change', {'post_change_redirect': '/password_change/done/'}),
    (r'^password_change/done/$', 'password_change_done'),
    (r'^reset_password/$', 'password_reset'),
    (r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',  'password_reset_confirm'),
    
)