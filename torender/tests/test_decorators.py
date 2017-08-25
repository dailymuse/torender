import torender
import tornado.testing
import tornado.web
import tornado.log
import os
import logging

CONTENTS = """
<body>
    <h1>Hello, world!</h1>
</body>
<script type='text/javascript'>
    var h2 = document.createElement('h2');
    h2.appendChild(document.createTextNode('Hello from prerender'));
    document.body.appendChild(h2);
</script>
""".strip().encode("utf8")

PRERENDERED_CONTENTS = """
<html><head></head><body>
    <h1>Hello, world!</h1>

<h2>Hello from prerender</h2></body></html>
""".strip().encode("utf8")

ALLOWED_PARAMS = set(["a", "b", "a[]", "b[]", "_escaped_fragment_"])

class BaseHandler(tornado.web.RequestHandler):
    def _get(self):
        self.set_header("Content-Type", 'text/html; charset=utf-8')
        self.finish(CONTENTS)

class PrerenderableWithoutParamsHandler(BaseHandler):
    @torender.prerenderable
    def get(self):
        self._get()

class PrerenderableWithParamsHandler(BaseHandler):
    @torender.prerenderable(params=["a", "b"])
    def get(self):
        # Because of the whitelisted parameters, params that aren't in
        # EXPECTED_PARAMS shouldn't be passed in
        input_arguments = set(self.request.arguments)
        unexpected_arguments = input_arguments - ALLOWED_PARAMS
        if len(unexpected_arguments) > 0:
            raise Exception("Unexpected parameters: %s" % ", ".join(unexpected_arguments))

        self._get()

class _BaseTestCase(tornado.testing.AsyncHTTPTestCase):
    def get_handlers(self):
        return [
            (r"^/no-params$", PrerenderableWithoutParamsHandler),
            (r"^/with-params$", PrerenderableWithParamsHandler),
        ]

    def get_settings(self):
        return {}

    def get_app(self):
        return tornado.web.Application(self.get_handlers(), **self.get_settings())

    def request(self, path, **kwargs):
        """Makes a request to one of the routes exposed by this test"""
        self.http_client.fetch(self.get_url(path), self.stop, **kwargs)
        return self.wait()

class PrerenderableTestCase(_BaseTestCase):
    def get_settings(self):
        settings = {}

        if "PRERENDER_TOKEN" in os.environ:
            settings["prerender_token"] = os.environ["PRERENDER_TOKEN"]
        if "PRERENDER_HOST" in os.environ:
            settings["prerender_host"] = os.environ["PRERENDER_HOST"]

        return settings

    def test_prerender(self):
        response = self.request("/no-params?_escaped_fragment_=")
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, PRERENDERED_CONTENTS)

    def test_no_prerender(self):
        response = self.request("/no-params")
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, CONTENTS)

    def test_whitelisted_params(self):
        response = self.request("/with-params?_escaped_fragment_=&a=1&b=2&c=3")
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, PRERENDERED_CONTENTS)

    def test_whitelisted_array_params(self):
        response = self.request("/with-params?_escaped_fragment_=&a[]=1&a[]=2&b=2&c=3")
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, PRERENDERED_CONTENTS)


class UnconfiguredPrerenderableTestCase(_BaseTestCase):
    def test_unconfigured(self):
        # This should raise a warning when attempting to prerender, but
        # continue onward to render the normal (non-prerendered) content,
        # because it's hitting the default host (service.prerender.io) without
        # a token.

        # If we're using a version of python that supports `assertLogs`, use
        # it to check for the warning - otherwise just run the code
        if hasattr(self, "assertLogs"):
            with self.assertLogs(tornado.log.app_log, logging.WARNING):
                self.check_unconfigured()
        else:
            self.check_unconfigured()

    def check_unconfigured(self):
        response = self.request("/no-params?_escaped_fragment_=")
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, CONTENTS)

class DisabledPrerenderableTestCase(_BaseTestCase):
    def get_settings(self):
        return dict(prerender_disabled=True)

    def test_disabled(self):
        response = self.request("/no-params?_escaped_fragment_=")
        self.assertEqual(response.code, 200)
        self.assertEqual(response.body, CONTENTS)
