import os
import asyncore
import utils
from pathlib import Path


class HTTPHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        request = self.recv(8192).decode()
        if request:
            print(request)
            headers, data = request.split('\r\n\r\n')
            headers = headers.split('\r\n')
            method, path, http_version = headers[0].split(' ')
            headers = {key.strip():val.strip() for key, val in map(lambda x: x.split(': '), headers[1:])}
            headers['method'] = method
            headers['path'] = path
            headers['http_version'] = http_version
            if 'Cookie' in headers:
                headers['Cookie'] = dict(map(lambda x: x.split('='), headers['Cookie'].replace(' ', '').split(';')))

            if method == 'GET':
                self.handle_get(headers, data)
            elif method == 'POST':
                self.handle_post(headers, data)
            elif method == 'DELETE':
                self.handle_delete(headers, data)
            else:
                self.send(utils.construct_response(501, 'Not Implemented', 'close', Path('template_html/501.html').read_bytes()))

            self.close()

    def handle_get(self, headers, data):
        route = {'/':'./index.html'}
        path = headers['path'].replace('..', '.')
        cookies = {}
        if 'Cookie' not in headers or 'sess_id' not in headers['Cookie'] or not utils.check_cookies({'sess_id':headers['Cookie']['sess_id']}):
            cookies = {'sess_id':utils.rand_string(16)}
        print(cookies)
        if cookies:
            utils.add_cookies(cookies)

        if path in route:
            path = route[path]
        else:
            path = '.' + path

        if not os.path.isfile(path):
            self.send(utils.construct_response(404, 'Not Found', 'close', utils.get_content_type('html'), Path('template_html/404.html').read_bytes()))
        else:
            self.send(utils.construct_response(200, 'OK', 'Keep-Alive', utils.get_content_type(path.split('.')[-1]), Path(path).read_bytes(), cookies=cookies))

    def handle_post(self, headers, data):
        pass

    def handle_delete(self, headers, data):
        pass

class HTTPServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket()
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accepted(self, sock, addr):
        print('Incoming connection from {}'.format(repr(addr)))
        handler = HTTPHandler(sock)


server = HTTPServer('localhost', 8080)
asyncore.loop()
