import os
import sys
import requests
import sqlite3
from flask import Flask
from flask import render_template, redirect, url_for
from flask import request
from flask import flash
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__, template_folder='templates/')
app.secret_key = 'asfsagwq211'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///weather.db'
db = SQLAlchemy(app)


class City(db.Model):
    id = db.Column(db.INTEGER, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=True)

    def __repr__(self):
        return f"{self.name} - id: {self.id}"


con = sqlite3.connect('weather.db')
cursor = con.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
if not cursor.fetchall() or not os.path.exists('weather.db'):
    db.create_all()


# write your code here

def get_city_weather(city_name):
    api_key = "2599de8feb54f9f0ef2148f9cca389c9"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}"
    response = requests.get(url).json()
    if response['cod'] == '404':
        return None
    temperature = None
    conditions = None
    if response['cod']:
        temperature = round(response['main']['temp'] - 273.15)
        conditions = response['weather'][0]['main']
    context = {'temperature': temperature, 'conditions': conditions, 'city_name': city_name}
    return context


def weather_from_db():
    """Generate all weather from db"""
    for city in City.query.all():
        weather_dict = get_city_weather(city.name)
        weather_dict['id'] = city.id
        yield weather_dict


@app.route('/')
def index():
    weather = []
    for i in weather_from_db():
        weather.append(i)

    return render_template('index.html', weather=weather)


@app.route('/', methods=['POST'])
def add():
    if request.method == 'POST':
        try:
            city_name = request.form['city_name']
            city_name = city_name.capitalize()
            city = City(name=city_name)
            try:
                weather = get_city_weather(city_name)
                if weather:
                    if not City.query.filter_by(name=city_name).first():
                        db.session.add(city)
                        db.session.commit()
                    else:
                        flash("The city has already been added to the list!")
                else:
                    flash("The city doesn't exist!")
            except:
                pass
        except:
            db.session.rollback()

        return redirect(url_for('index'))


@app.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):
    city = City.query.filter_by(id=city_id).first()
    db.session.delete(city)
    db.session.commit()
    return redirect(url_for('index'))


# don't change the following way to run flask:
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
