from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from os import listdir
import random
from random import choice
import cgi
import urlparse
import logging

from pymongo import MongoClient
client = MongoClient('localhost:27017')
db = client.PlayerData

ext2conttype = {"jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif"}

# initialize our test images array to prevent duplicate questions.
# (Not implemented.)
# test_images = []

def Message():
    global msg
    msg = "Was this image created by an AI or a human being?"

def content_type(filename):
    return ext2conttype[filename[filename.rfind(".")+1:].lower()]

def isimage(filename):
    """true if the filename's extension is in the content-type lookup"""
    filename = filename.lower()
    return filename[filename.rfind(".")+1:] in ext2conttype

def ai_or_human():
    global which
    dirs = ['ai', 'human']
    which = random.choice(dirs)
    return which

def random_file(dir):
    """returns the filename of a randomly chosen image in dir"""
    images = [f for f in listdir(dir) if isimage(f)]
    return choice(images)

# Prevent duplicate questions (Not implemented yet.)
#def this_test(test_images,r):
#    """temporarily tracks items in current test"""
#    test_images.append(r)

# Create new player in MongoDB
def insert(name,score,count):
    print '\nCreating new player.\n'
    print(name)
    print(count)
    print(score)
    try:
        db.PlayerData.insert_one(
            {
            "name":name,
            "score":'0',
            "count":'0'
        })
        print '\nCreated new player.\n'
        print(name)
        print(count)
        print("score is", score)
    except Exception, e:
        print str(e)

# Get current player and score.
# NB: Players must have unique names!
def read(name):
    try:
        pplCol = db.PlayerData.find({"name": name})
        print '\n Loaded player from PlayerData Database! \n'
        for ppl in pplCol:
            print(ppl)
            return ppl

    except Exception, e:
        print str(e)

# Update player score.
def update(name,score,count):
    print '\n trying to update score \n'
    try:
        name = name
        score = score

        db.PlayerData.update_one(
        {"name": name},
        {
        "$set": {
            "score":score,
            "count":count,
        }
        }
    )
        print "\nPlayer score updated\n"

    except Exception, e:
      print str(e)

class GetHandler(BaseHTTPRequestHandler):
    # This could probaably be culled down.
    global img, img_tag, name, score, nameScore, ai, human, answer, count

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        formData = cgi.FieldStorage()
        x = self.wfile.write

        # Not logging.
        #logging.debug('GET %s' % (self.path))

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        args = {}
        idx = self.path.find('?')
        print('idx')
        print(idx)
        # <--- HTML starts here --->
        x("<html>")
        # <--- HEAD starts here --->
        x("<head>")
        x("<title>Art-Official Intelligence</title>")
        x('<link rel="stylesheet" href="//maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap.min.css">')
        x('<link rel="stylesheet" href="//maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap-theme.min.css">')
        x("</head>")
        # <--- HEAD ends here --->

        # <--- BODY starts here --->
        x("<body>")

        # If we already have a game in progress...
        # Also none of this should be output, but only create an array of data to print later.
        if idx >= 0:
            rpath = self.path[:idx]

            print("Handling request for " + self.path)

            # args = cgi.parse_qs(self.path[idx+1:]) DEPRECATED
            parsed = urlparse.urlparse(self.path)
            print urlparse.parse_qs(parsed.query)['subbut']

            # This should probably be try/catch for missing form element
            if 'username' in urlparse.parse_qs(parsed.query):
                name = urlparse.parse_qs(parsed.query)['username'][0]
                yourName = name # (For new player names)
                print('getting score for %s' % name)
                nameScore = read(name)

            # Yes, seriously, Python makes this incredibly verbose.
            if 'ai' in urlparse.parse_qs(parsed.query):
                answer = urlparse.parse_qs(parsed.query)['ai'][0]
            if 'human' in urlparse.parse_qs(parsed.query):
                answer = urlparse.parse_qs(parsed.query)['human'][0]
            if 'correctanswer' in urlparse.parse_qs(parsed.query):
                which = urlparse.parse_qs(parsed.query)['correctanswer'][0]

            # This will obviously break if no answer is submitted. 
            if answer == which:
                thisScore = 1
            else:
                thisScore = 0

            # Don't tell the player their score until the end!
            #x('<p>you said it was %s</p>' % answer)
            #x('<p>and it was really %s</p>' % which)
            #x('<p>Your previous score is %s </p>' % nameScore['score'])
            #x('<p>this score is %s </p>' % thisScore)

            # @TODO
            if nameScore:
                newScore = int(nameScore['score']) + thisScore
                count = int(nameScore['count']) + 1
                # Ok, maybe tell them their score as they play...
                x("<p>Your current score is: %s</p>" % newScore)
                update(name,newScore,count)
            else:
                print(read(name))
                # @TODO: Don't hard code initial count. 
                insert(name,thisScore,1)
                x("<p>Your current score is: missing</p>")
                

            # @TODO
            if 'startover' in urlparse.parse_qs(parsed.query):
                x("<p>Sorry, unsupported option in this version.</p>")
            if 'newplayer' in urlparse.parse_qs(parsed.query):
                x("<p>Sorry, unsupported option in this version.</p>")
            if 'quit' in urlparse.parse_qs(parsed.query):
                print "Location: www.google.com\n"

        # Or else it is a new game.
        else:
            count = 0
            print('Count = 0')
            nameScore = 0  # Sigh.
            rpath = self.path
            print('New Player')
            print(idx)
            print(args)

            # Rather, this should be something like if name: yourName = name else yourName = "Enter_your_name"
            yourName = "Enter_your_name"

        # Pick the next random ai or human image

        # count += 1 # No comment.
        # print(count)
        dirs = ['ai', 'human']
        which = random.choice(dirs)
        dir = 'images/'+which+'/'
        r = random_file(dir)

        # Track which images have been served
        #this_test(test_images,r)

        # Quiz ends after 20 trials
        # if count > 20:
        #    finish()

        # img = dir+r
        data_uri = open(dir+r, 'rb').read().encode('base64').replace('\n', '')
        img_tag = '<img src="data:image/png;base64,%s">' % data_uri

        #x("<p>The correct answer is %s</p>" % dir)
        # x("<p>%s</p>" % msg)
        #x("<form method='POST'>")

        x('<div class="container">')
        x('<div class="form-group">')
        x("<form method='get'>")
        x('Name: <input type="text" name="username" class="form-control" value=%s>' % yourName)
        Message()
        x(msg)
        x("<br/>Your answer: <br/>")
        
        # This should be a single radio control, not 2. 
        x('<input type="radio" name="ai" value="ai" class=""> AI')
        x("<br/>")
        x('<input type="radio" name="human" value="human" class=""> Human')
        x("<input type='hidden' name='correctanswer' value=%s>" % which)
        x("&nbsp;&nbsp;&nbsp;<input type='submit' name='subbut' value='Final answer' class='btn btn-info form-control'>")
        x("</form>")
        x('<div class="row">')
        x('<div class="col-md-5 col-md-offset-2"></div>')
        x(img_tag)
        x("&nbsp;&nbsp;&nbsp;<br ><input type='submit' name='startover' value='Start Over' class='btn-warning'>")
        x("&nbsp;&nbsp;&nbsp;<input type='submit' name='newplayer' value='New Player' class='btn-success'>")
        x("&nbsp;&nbsp;&nbsp;<input type='submit' name='quit' value='Quit' class='btn-danger'>")
        x('<div>')
        x('<div>')
        x('<div>')
        x("</body>")
        # <--- BODY ends here --->
        x("</html>")
        # <--- HTML ends here --->
        return

if __name__ == '__main__':
    from BaseHTTPServer import HTTPServer
    server = HTTPServer(('localhost', 7777), GetHandler)
    print 'Starting server, use <Ctrl + F2> to stop'
    server.serve_forever()
