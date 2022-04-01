# Lucas Reicher
# Final Project for CSE150 
# 2/19/22

import sys
import csv
import socket

DEFAULT_PORT = '80'
DEFAULT_TIMEOUT = 10.0
DEFAULT_BUFFER_SIZE = 1024
# Lists for use in Log.csv append
COLUMN_NAMES = ["Successful or Unsuccessful", "Server Status Code", "Requested URL" , 
                "hostname", "source IP", "destination IP", "source port", 
                "destination port", "Server Response line (including code and phrase)"]

class ChunkedEncodingError(Exception):
    pass

class ContentLengthError(Exception):
    pass

class EmptyResponse(Exception):
    pass

def create_error_entry(connected, url, hostname, socket_ip, server_ip, socket_port, server_port, msg):
    if connected:
        log_entry = ["Unsuccessful", "ERR", sys.argv[1],hostname,
                         socket_ip,server_ip,socket_port,server_port,msg]
    else:
        log_entry = ["Unsuccessful", "ERR", sys.argv[1],hostname,
                         "N/A", "N/A", "N/A", "N/A", msg]
    return log_entry


def update_log(log_entry):
    # Append an entry to Log.csv containing the above information
    # Use mode 'a' to append instead of writing over file
    try:
        with open('Log.csv', 'a') as logfile:
            logwriter = csv.writer(logfile, delimiter=',', quoting=csv.QUOTE_MINIMAL)
            # Since we open with 'a', the file pointer will be at the end of the file content
            # If the 'end' is 0, we haven't written to the log so we should first append the
            #  column names. 
            if logfile.tell() == 0:
                logwriter.writerow(COLUMN_NAMES)
            logwriter.writerow(log_entry)
    except IOError,e:
        print("An error occured while opening or writing Log.csv: "+ str(e))
        
# Returns a HTTP GET Request with the given hostname and an optional file path
# Shouldn't have to .encode() the request string since Python 2.xx strings are just byte arrays
def create_GET(hostname, page=None):
    if page is not None:
        return 'GET /{} HTTP/1.1\r\nHost:{}\r\n\r\n'.format(page, hostname)#.encode()
    else: return 'GET / HTTP/1.1\r\nHost:{}\r\n\r\n'.format(hostname)#.encode()

# Strips 'http://' prefix from the URL if is present. If the url does not start with
# 'http://' the program terminates. 
def strip_http(url):
    if not url.startswith('http://'):
        if url.startswith('https://'):
            print("HTTPS not supported. Use only http://")
        else: 
            print("URL invalid. Must start with 'http://'")
        sys.exit()
    else: return url.replace('http://', '')

# Splits the supplied url into a url,page,port tuple.
#     if port is accidently placed after page or port is not numerical, terminate the program.
def parse_url_input(url):
    port = DEFAULT_PORT
    page = None
    url = strip_http(url)
    if "/" in url:
        url, page = url.split("/", 1)
    if ":" in url:
        url,port = url.split(":", 1)
    if page is not None and ":" in page:
        print("URL Invalid. Port should come before Path.")
        sys.exit()
    if not port.isdigit():
        print("URL Invalid. Port must be an integer.")
        sys.exit()
    else: port = int(port)
    return (url, page, port)

# Returns a tuple containing status code and full status line of the server's response
def parse_header(header):
    # Check if this response is chunk encoded
    chunked = 'Transfer-Encoding: chunked' in header
    # Peel off the server response line
    server_status_line,rest_of_header = header.split("\r\n",1)
    # SERVER RESPONSE LINE: PROTOCOL STATUS_CODE STATUS_PHRASE
    # STATUS_PHRASE might contain spaces, so don't split more than twice
    protocol, server_status_code, server_status_phrase = server_status_line.split(" ",2)
    # Try to find the content-length field and its corresponding value
    content_length = 0
    if not chunked:
        content_length_index = rest_of_header.find('Content-Length: ')
        if content_length_index > -1:
            if '\r\n' in rest_of_header[content_length_index:]:
                content_length,rest_of_header = rest_of_header[content_length_index:].split('\r\n',1)
                content_length = content_length.replace('Content-Length: ', '')
                if not content_length.isdigit():
                    raise ContentLengthError
                else: content_length = int(content_length)

    return (chunked, content_length, server_status_code, server_status_line)

# Returns TRUE if a string is in IPv4 format. Must have 3 '.'s and have integers
#   on either side of the '.'s whose values must be in the range [0,255]
def is_IPv4(url):
    if url.count('.') == 3:
        values = url.split('.',3)
        return all(value.isdigit() and 0 <= int(value) <= 255 for value in values)
    else: return False
        
    # 0 - 255 numerical
    # 3 periods '.'

# Process the cmdline args and split up the hostname, url, port, and page
def process_input():
    argc = len(sys.argv)  
    if argc == 2:
        url, page, port = parse_url_input(sys.argv[1])
        hostname = url
        if is_IPv4(url):
            print("URL ERROR: If URL is an IPv4, must include hostname as second arg")
            sys.exit()
    elif argc == 3:
        url, page, port = parse_url_input(sys.argv[1])
        hostname = sys.argv[2]
        if not is_IPv4(url):
            print("URL Error: Invalid IPv4 address")
            sys.exit()
    else:
        print("Usage: python2 lreicherMyCurl.py url hostname(if url is IPv4)")
        sys.exit()
    
    return (hostname, url, port, page)
        

def send_curl():
    # Process cmdline args as input and create corresponding HTTP request
    hostname,url,port,page = process_input()
    http_request = create_GET(hostname,page)
    result = ""
    header = ""
    connected = False
    socket_ip,socket_port = None,None
    server_ip,server_port = None,None

    #print("")
    #print('hostname: ' + str(hostname))
    #print('url: ' + str(url))
    #print('port: ' + str(port))
    #print('page: ' + str(page))
    #print('http_request --v\n' + str(http_request))

    # Seperate try-except for socket creation so we 
    # don't try to close a non-existant socket later on
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(DEFAULT_TIMEOUT)
    except socket.error, e:
        print("While creating the socket...")
        print("Socket Error: " + str(e))
        sys.exit()
    except Exception, e:
        print("Exception: " + str(e))
        sys.exit()

    try:
        # Connect to the requested url with port (default = 80)
        s.connect((url,port))
        connected = True
        #print("connected")

        # IP,PORT for server and client. Will need this when adding Log.csv entries
        socket_ip,socket_port = s.getsockname()
        server_ip,server_port = s.getpeername()

        # Send the http request to the server
        s.send(http_request)
        #print("sent")

        # download until we know we've received the entire header
        while True:
            header += s.recv(DEFAULT_BUFFER_SIZE)
            if len(header) == 0:
                raise EmptyResponse
            # there will be a '\r\n\r\n' between the header and content
            if '\r\n\r\n' in header:
                # split apart the header and content html
                header,html = header.split('\r\n\r\n',1)
                break
        # parse the header for chunk encoding, content-length, and server status line
        # also return server status code separately to avoid splitting later
        # since I split on \r\n\r\n, its possible we removed the \r\n from after the
        #    'content-length' field. Since I use the \r\n to split, I need to append one.
        chunked, content_length, server_status_code, server_status_line = parse_header(header+'\r\n')
        # if the server response is ChunkEncoded, we want to skip downloading the content.
        if chunked:
            raise ChunkedEncodingError
        # initialize the bytes_received with the length of the partial html already received.
        # python 2 strings are bytes, so this is easy
        bytes_received = len(html)
        # while there is still more content to download, append it to the full html string
        #     and update the number of bytes received
        while content_length > bytes_received:
            received = s.recv(DEFAULT_BUFFER_SIZE)
            bytes_received += len(received)
            html += received
    except socket.error, e:
        print("Unsuccessful")
        # Print the requested URL
        print(sys.argv[1])
        # Print the server status line
        print("Socket Error: " + str(e))
        log_entry = create_error_entry(connected, sys.argv[1], hostname, socket_ip, 
                                       server_ip, socket_port, server_port, str(e))
        update_log(log_entry)
        s.close()
        sys.exit()
    except ContentLengthError:
        print("Unsuccessful")
        # Print the requested URL
        print(sys.argv[1])
        # Print the server status line
        # I can't see this ever happening, but to be safe I'll create an exception.
        print("Content-Length field is not an integer.")
        log_entry = create_error_entry(connected, sys.argv[1], hostname, socket_ip, 
                                       server_ip, socket_port, server_port, 
                                       "Content-Length is not an integer")
        update_log(log_entry)
        s.close()
        sys.exit()
    except ChunkedEncodingError:
        print("Chunked Encoding is not supoorted.")
    except EmptyResponse:
        print("Unsuccessful")
        # Print the requested URL
        print(sys.argv[1])
        print("Empty reply from server.")
        log_entry = create_error_entry(connected, sys.argv[1], hostname, socket_ip, 
                                       server_ip, socket_port, server_port, 
                                       "Empty reply from server")
        update_log(log_entry)
        s.close()
        sys.exit()
    except Exception, e:
        # Catches any exception that may have been missed above
        print("Unsuccessful")
        # Print the requested URL
        print(sys.argv[1])
        print("Exception: " + str(e))
        log_entry = create_error_entry(connected, sys.argv[1], hostname, socket_ip, 
                                       server_ip, socket_port, server_port, str(e))
        update_log(log_entry)
        s.close()
        sys.exit()
    finally:
        s.close()
    
    # if the content is not chunk encoded and the server responded with status code 200,
    #     then write the received content to a HTTPoutput.html
    if not chunked and server_status_code == '200':
        success_string = 'Successful'
        try:
            with open("HTTPoutput.html", "w") as f:
                f.write(html)
        except IOError:
            print("An error occured while opening or writing to HTTPOutput.html")
            sys.exit()
        print("Success")
    else:
        success_string = 'Unsuccessful' 
        print("Unsuccessful")

    # Print the requested URL
    print(sys.argv[1])

    # Print the server status line
    print(server_status_line)

    log_entry = [success_string,server_status_code,sys.argv[1],hostname,
                 socket_ip,server_ip,socket_port,server_port,server_status_line]
    update_log(log_entry)
    sys.exit()

    
if __name__ == '__main__':
    send_curl()
