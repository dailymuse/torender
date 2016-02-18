# Torender [![Build Status](https://travis-ci.org/dailymuse/torender.png)](https://travis-ci.org/dailymuse/torender) #

Torender adds [prerender](https://prerender.io/) capabilities to tornado-based
applications.

Requires tornado >= 3.2.

## Installation ##

Via pip:

    pip install torender

## Usage ##

Add torender's decorator to endpoints that you want to be prerenderable:

    import torender

    class MainHandler(tornado.web.RequestHandler):
        @torender.prerenderable
        def get(self):
            self.write("Hello, world")

You can also whitelist query parameters for the page. This will strip out
irrelevant query parameters (e.g. tracking params like `utm_source`) before
forwarding the request to prerender. If you cache prerender pages, this will
increase performance (by preventing executions on redundant pages). And if you
use [prerender.io](http://prerender.io), it will further decrease your costs
(because you have less pages that are being prerendered.)

To whitelist query parameters, use the `params` arg for the decorator:

    import torender

    class MainHandler(tornado.web.RequestHandler):
        @torender.prerenderable(params=["first_allowed_query_param", "second_allowed_query_param"])
        def get(self):
            self.write("Hello, world")

## Settings ##

Using tornado application settings, you can set these parameters:

* `prerender_host` - The prerender host. Defaults to
  `http://service.prerender.io`.
* `prerender_token` - The token to pass into the prerender host. Required for
  [the hosted version of prerender](http://prerender.io/).
* `prerender_request_timeout` - How long in seconds to wait before giving up
  on a request to prerender. Defaults to 20.
* `prerender_disabled` - Setting this to true will disable prerendering. This
  way you can turn off prerender without removing all the uses of the
  `prerenderable` decorator in code.

Note that you'll need to either set `prerender_host` to point to your
prerender installation or `prerender_token` to the token given to you by
prerender.io.

## Running Tests ##

Tests require node.js and tox. To run them:

    make init
    tox
