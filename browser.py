import socket

# The difference between http and https is that https is more secure—but 
# let’s be a little more specific. The https scheme, or more formally HTTP 
# over TLS, is identical to the normal http scheme, except that all
# communication between the browser and the host is encrypted. There are 
# quite a few details to how this works: which encryption algorithms are used,
# how a common encryption key is agreed to, and of course how to make sure
# that the browser is connecting to the correct host. Luckily, the Python ssl 
# library implements all of these details for us.
import ssl

class URL:
    
    # Let’s start with parsing the URL. I’m going to make parsing a URL return 
    # a URL object, and I’ll put the parsing code into the constructor. The
    # __init__ method is Python’s peculiar syntax for class constructors, and
    # the self parameter, which you must always make the first parameter of
    # any method, is Python’s analog of this.


    def __init__(self, url):
        
        # The split(s, n) method splits a string at the first n copies of s.
        
        # Detect which scheme is being used and set the appropriate port:

        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"] , "scheme is not recognized"
        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443
            
        # Detect hostname and path: 

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        # Adding support for custom ports, which are specified in a URL by 
        # putting a colon after the host name
        
        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)
    
    # Now that the URL has the scheme, host, port and path fields, we can 
    # download the web page at that URL. We’ll do that in a new method, 
    # request:
    
    def request(self):

        # The first step to downloading a web page is connecting to the host.
        # The operating system provides a feature called “sockets” for this. 
        # When you want to talk to other computers (either to tell them 
        # something, or to wait for them to tell you something), you create a
        # socket, and then that socket can be used to send information back 
        # and forth. Sockets come in a few different kinds, because there are 
        # multiple ways to talk to other computers:
        #   1.  A socket has an address family, which tells you how to find 
        #       the other computer. Address families have names that begin 
        #       with AF. We want AF_INET, but for example AF_BLUETOOTH is 
        #       another.
        #   2.  A socket has a type, which describes the sort of conversation
        #       that’s going to happen. Types have names that begin with SOCK.
        #       We want SOCK_STREAM, which means each computer can send 
        #       arbitrary amounts of data over, but there’s also SOCK_DGRAM, 
        #       in which case they send each other packets of some fixed size.
        #   3.  A socket has a protocol, which describes the steps by which 
        #       the two computers will establish a connection. Protocols have
        #       names that depend on the address family, but we want 
        #       IPPROTO_TCP.

        # Exercise 1-2 to support the file scheme:
        if self.scheme == "file":
            body = open(self.path, 'r')
            return body

        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

        # Creating wrapped socket for connection to sites with HTTPS scheme,
        # using ssl library

        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)


        # Once you have a socket, you need to tell it to connect to the other 
        # computer. For that, you need the host and a port. The port depends 
        # on the protocol you are using.

        s.connect((self.host, self.port))

        # Now that we have a connection, we make a request to the other server. 
        # To do so, we send it some data using the send method. The send method
        # just sends the request to the server.
        #
        #       Note: send actually returns a number (47 in this case) that 
        #       tells you how many bytes of data you sent to the other 
        #       computer. If, say, your network connection failed midway 
        #       through sending the data, you might want to know how much 
        #       you sent before the connection failed. 
        #
        # There are a few things in this code that have to be exactly right.
        # First, it’s very important to use \r\n instead of \n for newlines.
        # It’s also essential that you put two newlines \r\n at the end, so 
        # that you send that blank line at the end of the request. If you 
        # forget that, the other computer will keep waiting on you to send 
        # that newline, and you’ll keep waiting on its response. 
        #
        # Also note the encode call. When you send data, it’s important to 
        # remember that you are sending raw bits and bytes; they could form 
        # text or an image or video. But a Python string is specifically for
        # representing text. The encode method converts text into bytes, and
        # there’s a corresponding decode method that goes the other way. If 
        # you see an error about str versus bytes, it’s because you forgot to
        # call encode or decode somewhere.
        #
        # Below includes work for Exercise "HTTP/1.1", new request headers
        # can be added to send_headers_list:

        send_headers_list = [
            "Host: {}".format(self.host),
            "Connection: close",
            "User-Agent: JohnBoi",
        ]

        headers_string = str()

        for h in send_headers_list:
            headers_string = headers_string + h + "\r\n"
        
        headers_string = headers_string + "\r\n"

        s.send(("GET {} HTTP/1.0\r\n".format(self.path) + \
            headers_string).encode("utf8"))
        
        # To read the server’s response, you could use the read function on 
        # sockets, which gives whatever bits of the response have already 
        # arrived. Then you write a loop to collect those bits as they arrive.
        # However, in Python you can use the makefile helper function, which 
        # hides the loop. If you’re in another language, you might only have 
        # socket.read available. You’ll need to write the loop, checking the
        # socket status, yourself.
        #
        # Here makefile returns a file-like object containing every byte we 
        # receive from the server. I am instructing Python to turn those bytes
        # into a string using the utf8 encoding, or method of associating 
        # bytes to letters. Hard-coding utf8 is not correct, but it’s a 
        # shortcut that will work alright on most English-language websites. 
        # In fact, the Content-Type header usually contains a charset 
        # declaration that specifies encoding of the body. If it’s absent, 
        # browsers still won’t default to utf8; they’ll guess.

        response = s.makefile("r", encoding="utf8", newline="\r\n")

        # Let’s now split the response into pieces. The first line is the 
        # status line.

        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        # After the status line come the headers. For the headers, I split 
        # each line at the first colon and fill in a map of header names to 
        # header values. Headers are case-insensitive, so I normalize them 
        # to lower case.I used casefold instead of lower, because it works 
        # better in more languages. Also, whitespace is insignificant in HTTP
        # header values, so I strip off extra whitespace at the beginning and
        # end.

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()
        
        # Headers can describe all sorts of information, but a couple of 
        # headers are especially important because they tell us that the 
        # data we’re trying to access is being sent in an unusual way. Let’s 
        # make sure none of those are present.
        
        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers

        # The usual way to send the data, then is everything after the 
        # headers.

        body = response.read()
        s.close()

        # It’s the body that we’re going to display, so let’s return that.

        return body
    
# To create our very, very simple web browser, let’s take the page HTML 
# and print all the text, but not the tags, in it. I’ll do this in a new
# function, show. This code is pretty complex. It goes through the request
# body character by character, and it has two states: in_tag, when it is 
# currently between a pair of angle brackets, and not in_tag. When the 
# current character is an angle bracket, it changes between those states; 
# normal characters, not inside a tag, are printed.

def show(body):
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")
    
# We can now load a web page just by stringing together request and show:
    
def load(url):
    body = url.request()
    show(body)
    print(vars(url))
    
# Add the following code to run load from the command line:
    
if __name__ == "__main__":
    import sys

    # Exercise 1-2 to open a test file if no url is provided:
    if len(sys.argv) == 1:
        body = open('/home/jstanton/firstbrowser/test.txt', 'r')
        show(body)
    else:
        load(URL(sys.argv[1]))