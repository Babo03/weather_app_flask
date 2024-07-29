from flask import Flask, render_template, request
import requests
from datetime import datetime

app = Flask(__name__)

API_KEY = '212c345134a7a7e7df60148434a4974b'  # Replace with your OpenWeather API key

@app.route('/', methods=['GET', 'POST'])
def index():
    city = request.args.get('city', 'New York')  # Default city if none is provided
    weather_data = get_weather_data(city)
    return render_template('index.html', city=city, data=weather_data)

def get_weather_data(city):
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={API_KEY}'
    response = requests.get(url)
    data = response.json()

    # Fetch air quality data
    coord = data['city']['coord']
    air_quality_url = f'http://api.openweathermap.org/data/2.5/air_pollution?lat={coord["lat"]}&lon={coord["lon"]}&appid={API_KEY}'
    air_quality_response = requests.get(air_quality_url)
    air_quality_data = air_quality_response.json()

    # Aggregate data into 24-hour intervals
    hourly_data = data['list']
    daily_data = []
    current_day = None
    day_data = []

    for item in hourly_data:
        dt_txt = item['dt_txt']
        date = datetime.strptime(dt_txt, '%Y-%m-%d %H:%M:%S').date()

        if current_day is None:
            current_day = date

        if date == current_day:
            day_data.append(item)
        else:
            daily_data.append(aggregate_day_data(day_data, air_quality_data))
            current_day = date
            day_data = [item]

    if day_data:
        daily_data.append(aggregate_day_data(day_data, air_quality_data))

    return {'list': daily_data}

def aggregate_day_data(day_data, air_quality_data):
    # Aggregate data for one day and convert to integer
    temp = int(round(sum(item['main']['temp'] for item in day_data) / len(day_data)))
    humidity = int(round(sum(item['main']['humidity'] for item in day_data) / len(day_data)))
    wind_speed = int(round(sum(item['wind']['speed'] for item in day_data) / len(day_data)))
    pressure = int(round(sum(item['main']['pressure'] for item in day_data) / len(day_data)))
    weather_description = day_data[0]['weather'][0]['description']
    air_quality = air_quality_data['list'][0]['main']['aqi']

    return {
        'dt_txt': f"{day_data[0]['dt_txt'][:10]} 00:00:00",
        'main': {'temp': temp, 'humidity': humidity, 'pressure': pressure},
        'wind': {'speed': wind_speed},
        'weather': [{'description': weather_description}],
        'air_quality': air_quality
    }

if __name__ == '__main__':
    app.run(debug=True)
