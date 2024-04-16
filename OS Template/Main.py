from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash #This library lets us easily hash + verify passwords.
import requests

#Instantiate Flask App
app = Flask(__name__)

#URI to connect to College DB - mine is mfm (after SVR-CMP-01/), YOU WILL NEED TO EDIT THIS to your username.
app.config['SQLALCHEMY_DATABASE_URI'] = (
'mssql+pyodbc://SVR-CMP-01/mfm?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes'
)

#Create DB object using Flask app object
db = SQLAlchemy(app)

#Map out User table
class User(db.Model):
    Id = db.Column(db.Integer, primary_key = True)
    Name = db.Column(db.String(50), nullable = False)
    Email = db.Column(db.String(70), unique = True)
    PasswordHash = db.Column(db.String(128)) #Store a hashed (encrypted) user password rather than plaintext.
    UserType = db.Column(db.String(20))#Used to check whether the user is a staff member, admin or customer etc. 

    #Function to create hashed passwords
    def set_password(self, password):
        self.PasswordHash = generate_password_hash(password)

    #Function to check stored hashed passwords
    def check_password(self, password):
        return check_password_hash(self.PasswordHash, password)

#Create tables if they don't already exist.
with app.app_context():
    db.create_all()
    
#Starting page
@app.route('/')
def index():
    return render_template('login.html')

#Dashboard homepage
@app.route('/home')
def home():
    return render_template('home.html', weather_data = get_weather())

#Login page and handling login POST
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(Email = username).first()
        if user:
            if user.check_password(password):
                return redirect(url_for('home'))
    else:     
        return render_template('login.html')

#Signup page and handling signup POST
@app.route('/signup', methods=['GET', 'POST'])
def signup():

    #When the user submits (or rather POSTs) the form we run the following code.
    if request.method == 'POST':
        fName = request.form['fname'] #Assign the form contents to variables for us to use later.
        sName = request.form['sname']        
        email = request.form['email']
        password = request.form['password']

        name = fName + " " + sName

        if User.query.filter_by(Email=email).first(): #Checks if there is already a user with this email address.
            return redirect(url_for('signup')) #You should provide some feedback to the user rather than just redirect to the same page like this.
        else:
            new_user = User(Name=name, Email=email) #Create a new User object which we will use to INSERT into our database
            new_user.set_password(password)
            with app.app_context():
                db.session.add(new_user)
                db.session.commit() #Make sure you .commit() otherwise the changes don't go through to the DB.
                return redirect(url_for('login'))

    else:
        return render_template('signup.html')

#Function accessing weather API at https://www.weatherapi.com/
def get_weather():
    try:
        api_key = 'a627aa23eb5e4fd3954133600242102' #This should likely be saved in a config file
        location = 'Horsham'
        response = requests.get(f'http://api.weatherapi.com/v1/current.json?key={api_key}&q={location}&aqi=no')
        response.raise_for_status() #Will generate an error if there is a problem with our API call.

        json = response.json()

        weather_data = { #Extract the data from the JSON we received into a dictionary so we can use it later.
            'location': json['location']['name'],
            'temperature': json['current']['temp_c'],
            'condition': json['current']['condition'],
            'wind': json['current']['wind_mph']
        }

        return weather_data

    except requests.RequestException as err:
        return {'error fetching weather': str(err)}


#Run in debug mode.
if __name__ == '__main__':
    app.run(debug = True)

