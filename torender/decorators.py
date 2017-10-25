import tornado.web
from tornado import httpclient, log, web, gen
import functools
import re

try:
    from urllib.parse import urlencode
except:
    from urllib import urlencode

# Timeout for the request in seconds
DEFAULT_REQUEST_TIMEOUT = 20.0

# Service that provides prerendering functionality
DEFAULT_PRERENDER_HOST = "http://service.prerender.io"

# Regex used to strip multi-param encoding
MULTI_PARAM_REGEX = re.compile("\[[0-9]*\]$")

# taken from https://github.com/prerender/prerender_rails/blob/master/lib/prerender_rails.rb
# googlebot, yahoo, and bingbot are not in this list because
# we support _escaped_fragment_ and want to ensure people aren't
# penalized for cloaking.
CRAWLER_USER_AGENTS = [
    # 'googlebot',
    # 'yahoo',
    # 'bingbot',
    'baiduspider',
    'facebookexternalhit',
    'twitterbot',
    'rogerbot',
    'linkedinbot',
    'embedly',
    'bufferbot',
    'quora link preview',
    'showyoubot',
    'outbrain',
    'pinterest/0.',
    'developers.google.com/+/web/snippet',
    'www.google.com/webmasters/tools/richsnippets',
    'slackbot',
    'vkshare',
    'w3c_validator',
    'redditbot',
    'applebot',
    'whatsapp',
    'flipboard',
    'tumblr',
    'bitlybot',
    'skypeuripreview',
    'nuzzel',
    'discordbot',
    'google page speed',
    'qwantify'
]

def prerenderable(method=None, params=None):
    """
    Decorate methods with this to allow an endpoint to be prerenderable. This
    is used on endpoints that rely on client-side javascript execution for
    proper rendering. Because search crawlers cannot necessarily execute
    javascript, this goes to a service that is capable of executing
    javascript to render the page results before returning them to the client.

    Pass in params to whitelist the query parameters allowed to be passed on
    to prerender. Whitelisting is useful to reduce the number of calls to
    prerender, as you can ignore irrelevant query parameters (such as ones
    automatically sent by referrers.)

    A basic example:

        import torender

        class MainHandler(tornado.web.RequestHandler):
            @torender.prerenderable
            def get(self):
                self.write("Hello, world")

    Here's an example that whitelists the allowed query parameters:

        import torender

        class MainHandler(tornado.web.RequestHandler):
            @torender.prerenderable(params=["first_allowed_query_param", "second_allowed_query_param"])
            def get(self):
                self.write("Hello, world")
    """

    if method is None:
        return functools.partial(prerenderable, params=params)

    whitelisted_params = set(params) if params != None else None

    @web.asynchronous
    @gen.coroutine
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        # Prerender is disabled - continue to the method
        if self.settings.get("prerender_disabled", False) == True:
            method(self, *args, **kwargs)
            return

        # Normal request - continue to the method
        user_agent = self.request.headers.get("User-Agent", "").lower()
        if self.get_argument("_escaped_fragment_", None) == None and not any(crawler_user_agent in user_agent for crawler_user_agent in CRAWLER_USER_AGENTS):
            method(self, *args, **kwargs)
            return

        # The request is coming from a PhantomJS client - continue to the
        # method
        if "PhantomJS" in self.request.headers.get("User-Agent", ""):
            method(self, *args, **kwargs)
            return

        prerender_token = self.settings.get("prerender_token")
        prerender_host = self.settings.get("prerender_host", DEFAULT_PRERENDER_HOST)
        new_url = "%s/%s://%s%s" % (prerender_host, self.request.protocol, self.request.host, self.request.path)
        query_args = self.request.query_arguments

        # Sort the query parameters to prevent redundant calls
        if len(query_args) > 0:
            flattened_query_args = []

            for k, v in query_args.items():
                escaped_param = MULTI_PARAM_REGEX.sub("", k)
                if whitelisted_params == None or escaped_param in whitelisted_params:
                    for i in v:
                        flattened_query_args.append((k, i))

            flattened_query_args.sort()

            new_url = "%s?%s" % (new_url, urlencode(flattened_query_args))

        response = None

        fetch_kwargs = {
            "headers": {},
            "request_timeout": float(self.settings.get("prerender_request_timeout", DEFAULT_REQUEST_TIMEOUT)),
        }

        if prerender_token:
            fetch_kwargs["headers"]["X-Prerender-Token"] = prerender_token

        # Make the request to prerender, and proxy the results
        try:
            response = yield httpclient.AsyncHTTPClient().fetch(new_url, **fetch_kwargs)
        except httpclient.HTTPError:
            log.app_log.warning("HTTP error when making a request to prerender", exc_info=True)
        except Exception:
            log.app_log.error("Error when making a request to prerender", exc_info=True)
        else:
            if response.code == 200:
                self.finish(response.body)
                return

        # If an error occurs, continue with the normal method
        method(self, *args, **kwargs)
        return

    return wrapper
