import sys
import atexit
import multiprocessing
from datetime import datetime
from urllib import urlencode
import logging

from webob.request import Request
from webob.response import Response

logger = logging.getLogger(__name__)

class AnalyticsMiddleware(object):
    def __init__(self, app, tracking_id):
        logger.debug('Initializing the AnalyticsMiddleware with tracking_id=%s', tracking_id)
        self.tracking_id = tracking_id
        self.wrapped_app = app
        self.hit_queue = multiprocessing.Queue()
        self.queue_runner = Consumer(self.hit_queue)
        self.queue_runner.start()

        @atexit.register
        def shutdown():
            logger.info('Sending a poison pill to the queue runner')
            self.hit_queue.put(None)

    def __call__(self, environ, start_response):
        logger.debug("AnalyticsMiddleware got called")
        start_time = datetime.now()
        req = Request(environ)
        # If we have a session id, use it
        try:
            id_ = req.cookies['beaker.session.id']
        # If we don't, screw it, we can't track user stuff
        except KeyError:
            id_ = ''

        # Pass the response through
        content_length = 0
        app_iter = self.wrapped_app(environ, start_response)
        for chunk in app_iter:
            content_length += len(chunk)
            yield chunk
        end_time = datetime.now()
            
        try:
            email = environ.get('beaker.session')['email']
        except:
            email = ''

        d = {'t':'pageview',
             'tid': self.tracking_id,
             'dl': req.path_url,
             'pdt': int((end_time - start_time).total_seconds() * 1000),
             'cd1': email,
             'cid': id_,
             'cm1': content_length,
             'dr': req.headers['Referer'] if 'Referer' in req.headers else '',
            }
        ua = req.headers['User-Agent'] if 'User-Agent' in req.headers else None
        self.hit_queue.put(AnalyticsSubmitter(d, start_time, ua))

class Consumer(multiprocessing.Process):
    def __init__(self, hit_queue):
        multiprocessing.Process.__init__(self)
        self.hit_queue = hit_queue

    def run(self):
        proc_name = self.name
        try:
            while True:
                next_task = self.hit_queue.get()
                if next_task is None:
                    # Poison Pill says exit
                    logger.info('%s: Exiting' % proc_name)
                    break
                logger.debug('{}: {}'.format(proc_name, next_task))
                answer = next_task()
        except:
            pass

class AnalyticsSubmitter(object):
    def __init__(self, parameters, hit_time, user_agent=None):
        self.parameters = parameters
        self.hit_time = hit_time
        self.user_agent = user_agent

    def __repr__(self):
        return "AnalyticsSubmitter('{}', '{}', '{}')".format(self.parameters, self.hit_time, self.user_agent)

    def __call__(self):
        item = self.parameters
        req = Request.blank('https://ssl.google-analytics.com/collect')
        req.method = 'POST'
        if self.user_agent:
            logger.debug('Setting User-Agent to: {}'.format(self.user_agent))
            req.headers['User-Agent'] = self.user_agent

        queue_time = int((datetime.now() - self.hit_time).total_seconds() * 1000)
        item.update({'v': 1,
                     'qt': queue_time
                     })
        req.body = urlencode(item)

        logger.debug('Submitting these analytics to Google: %s', req.body)
        res = req.get_response()
        if res.status == '200 OK':
            logger.debug('200 OK')
        else:
            logger.error('Google returned a response status: %s', res.status)

        return res.status
