import os
from flask import Flask, render_template,redirect, url_for, request
import time
from flask_sqlalchemy import SQLAlchemy

def readFile(path):
    with open(path, "rt") as f:
        return f.read()

def writeFile(path, contents):
    with open(path, "wt") as f:
        f.write(contents)

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
db = SQLAlchemy(app)

class Portal(db.Model):
    __tablename__="PortalStatus"

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(10),unique=True)
    status = db.Column(db.String(20))
    time = db.Column(db.Float)
    blood = db.Column(db.Float)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    superPortal = db.Column(db.Boolean)
    
    def __init__(self,name,coordinates):
        self.name = name
        self.status = "unoccupied"
        self.time = 0
        self.blood = 2
        self.latitude, self.longitude = coordinates
        if self.name == "UC": superPortal = True
        else: superPortal = False
        self.superPortal = superPortal

    def __repr__(self):
        return '<Portal %r at (%f, %f)>' % (self.name, self.latitude,
                                                            self.longitude)

db.drop_all()
db.create_all()
#initialize all portals
portals = ({"CFA":(40.441619, -79.942977), "Porter":(40.441700, -79.946314),
            "Gates":(40.443437, -79.944672),"UC":(40.443388, -79.942001),
            "MM":(40.442016, -79.941507),"Wean":(40.442661, -79.945831),
            "DH":(40.442498, -79.944479),"Hunt":(40.441069, -79.943728),
            "SYG":(40.440751, -79.941342),"Donner":(40.441894, -79.940263),
            "Rez":(40.447046, -79.946720)})
for portal,coordinates in portals.items():
    newPortal = Portal(portal,coordinates)
    db.session.add(newPortal)
    db.session.commit()

portals = ("CFA", "Porter","Gates","UC","MM","Wean",
            "DH","Hunt","SYG","Donner","Rez")
    
app = Flask(__name__)
result = None

@app.route('/index')
def index():
    return (render_template("chooseTeam.html"))

@app.route('/mapBlue', methods = ["GET","POST"])
def mapBlue():
    global result
    if request.method == "GET":
        writeFile("templates/blueMapTemp.html",changePortalColor("templates/mapBlue.html"))
        return render_template("blueMapTemp.html")
    else:
        userLocation = (request.get_json(force= True)["color"],
            request.get_json(force= True)["latitude"],
            request.get_json(force= True)["longitude"])
        result = (hackPortal(userLocation,userLocation[0]))
        print(result)
        return redirect(url_for("blueHackResult"))

@app.route('/mapRed', methods = ["GET","POST"])
def mapRed():
    global result
    if request.method == "GET":
        writeFile("templates/redMapTemp.html",changePortalColor("templates/mapRed.html"))
        return render_template("redMapTemp.html")
    else:
        userLocation = (request.get_json(force= True)["color"],
            request.get_json(force= True)["latitude"],
            request.get_json(force= True)["longitude"])
        result = (hackPortal(userLocation,userLocation[0]))
        print(result)
        return redirect(url_for("redHackResult"))

@app.route('/portalsBlue')
def portalsBlue():
    writeFile("templates/blueTemp.html",changeHtml("templates/portalsBlue.html"))
    return (render_template("blueTemp.html"))

@app.route('/helpBlue')
def helpBlue():
    return (render_template("helpBlue.html"))

@app.route('/portalsRed')
def portalsRed():
    writeFile("templates/redTemp.html",changeHtml("templates/portalsRed.html"))
    return (render_template("redTemp.html"))

@app.route('/helpRed')
def helpRed():
    return (render_template("helpRed.html"))

@app.route('/blueHackResult')
def blueHackResult():
    global result
    content = readFile("templates/blueHackResult.html")
    frontIndex = content.find("Your Hack result will be")
    endIndex = content.find("</p",frontIndex)
    content = content[:frontIndex] + result + content[endIndex-1:]
    writeFile("templates/blueResultTemp.html",content)
    return (render_template("blueResultTemp.html"))

@app.route('/redHackResult')
def redHackResult():
    global result
    content = readFile("templates/redHackResult.html")
    frontIndex = content.find("Your Hack result will be")
    endIndex = content.find("</p",frontIndex)
    content = content[:frontIndex] + result + content[endIndex-1:]
    writeFile("templates/redResultTemp.html",content)
    return (render_template("redResultTemp.html"))

def changeHtml(filename):
    global portals
    content = readFile(filename)
    for portal in portals:
        portalName = portal
        portal = Portal.query.filter_by(name="{0}".format(portal)).first()
        beginIndex = content.find("Status of {0}".format(portalName))
        index = content.find("</p",beginIndex)
        content = content[:index] + ": " + portal.status + content[index:]
    return content

def changePortalColor(filename):
    global portals
    content = readFile(filename)
    for portal in portals:
        portalName = portal
        portal = Portal.query.filter_by(name="{0}".format(portal)).first()
        beginIndex = content.find("{0}Circle".format(portalName))
        frontIndex = content.find("#000000",beginIndex)
        endIndex = frontIndex + len("#000000")
        if portal.status == "Blue":
            content = content[:frontIndex] + "#0000FF" + content[endIndex:]
        elif portal.status == "Red":
            content = content[:frontIndex] + "#FF0000" + content[endIndex:]
    return content

def hackPortal(userLocation,color):
    (userLat,userLong) = (userLocation[1],userLocation[2])
    for portal in portals:
        portalName = portal
        portal = Portal.query.filter_by(name="{0}".format(portal)).first()
        portalLat = portal.latitude
        portalLong = portal.longitude
        if isLegalHack(portalLat,portalLong,userLat,
                          userLong,color,portal)==True:
            portal.status = color
            portal.blood = 2
            portal.time = 0
            return ("{0} hacked {1}".format(color,portalName))
        elif isLegalHack(portalLat,portalLong,userLat,
                          userLong,color,portal)=="Attacked":
            portal.blood = 1
            portal.time = time.time()
            return ("{0} attacked {1}".format(color,portalName))
    return ("Hacking unsuccessful.")

def isLegalHack(portalLat,portalLong,userLat,userLong,color,portal):
    if portal.status == "unoccupied":
        if withinDis(portalLat,portalLong,userLat,userLong):
            print(1)
            return True
        else:
            print(2)
            return False
    else:
        if color != portal.status:
            if withinDis(portalLat,portalLong,userLat,userLong):
                if abs(time.time() - portal.time) > 3600:
                    if portal.blood == 2:
                      print(3)
                      return "Attacked"
                    elif portal.blood == 1:
                      print(4)
                      return True
                else:
                    print(5)
                    return False
        else:
            if withinDis(portalLat,portalLong,userLat,userLong):
                if portal.blood == 1:
                    print(6)
                    return True
                else:
                    print(7)
                    return False

def withinDis(portalLat,portalLong,userLat,userLong):
    (epsilonLat,epsilonLong) = (0.00105,0.000250)
    #(0.00095,0.000235)
    if (abs(userLat-portalLat) <= epsilonLat and
           abs(userLong-portalLong) <= epsilonLong):
        return True
    else:
        return False

if __name__ == '__main__':
    app.run(host='0.0.0.0')