from django import template
from django.conf import settings
from dolores.settings import FB_APP_ID, FB_APP_SECRET
register = template.Library()
facebookLoginScript = """
    <!-- Facebook Login -->
    <script type="text/javascript">
        fblogin = function(success,fail){
            FB.login(function(response) {
                if (response.session){
                    if(response.scope){
                        if (success!=null){
                            success();
                        }
                    } else {
                        if (fail!=null){

                            fail();
                        }
                    }
                } else {
                    fail();
                }
            },
            {scope:'read_stream,publish_stream,offline_access,user_photos'});
        };
    </script>
    <!-- Facebook Login Status -->
    <script type="text/javascript">
        fbconnected = function(success,fail){
            FB.getLoginStatus(function(response) {
                if (response.session) {
                    if(success!=null) success();
                } else {
                    if(fail!=null) fail();
                }
            });
        };
    </script>
    """
class FacebookLoginScriptNode(template.Node):
    def render(self, context):
        return facebookLoginScript
    def facebook_login_script(parser, token):
        return FacebookLoginScriptNode()
    register.tag(facebook_login_script)
facebookLoadScript = """
    <!-- Load the Facebook SDK -->
    <div id="fb-root"></div>
    <script src="http://connect.facebook.net/en_US/all.js"></script>
    <script>
        FB.init({
            appId  : '%s',
            status : true,
            cookie : true,
            xfbml  : true
        });
    </script>
""" % FB_APP_ID
class FacebookLoadScriptNode(template.Node):
    def render(self, context):
        return facebookLoadScript
    def facebook_load_script(parser, token): 
        return FacebookLoadScriptNode()
    register.tag(facebook_load_script)