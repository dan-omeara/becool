"""
File: becool.py
Author: Dan O'Meara
---
Weather app to determine coolest place in local area.
Best suited for microclimates.
"""
DEFAULT_ZIP_DATA = {"94101": {"city": "San Francisco",
                              "lat": 37.77,
                              "lng": -122.41,
                              }}

# Used for debugging API responses
import time 

from uszipcode import SearchEngine
import openmeteo_requests
import requests_cache
from retry_requests import retry

API_BASE_URL = "https://api.open-meteo.com/v1/forecast"
# API_BASE_URL = "http://api.weatherapi.com/v1/forecast.json"
# API_KEY = constants.API_KEY
RADIUS = 10 # miles

def main():
    """
    Asks user for zip code, then determines the coolest zipcode within a given radius.
    Radius is set as a constant (currently 10 miles).
    """
    while True:
        zip_code = input("Enter your zip code: ")
        
        loc_data, zip_code = get_zip_basics(zip_code)
        
        nearby_locs = get_local_zips(loc_data[zip_code]["lat"], loc_data[zip_code]["lng"], RADIUS)
        
        print("There are " + str(len(nearby_locs.keys()))
              + " zip codes within a " + str(RADIUS) + " mile radius.")
        input("Press any key to continue.")
        
        weather_results = get_weather(nearby_locs)
        
        # Used for debugging API responses
        # write_to_file(weather_results, filename = str(time.time()))

        coolest_zip = calculate_coolest_zip(weather_results, zip_code)
        display_results(weather_results, zip_code, coolest_zip)
        print("")


def get_zip_basics(zip_code):
    """
    Gets a basic data for the given zip_code.
    Uses the uszipcode package.
    For errors in input or unknown zip codes (note that not all 5-digit numbers 
    have been assigned as zip codes), the function defaults to San Francisco (94101).
    Returns:
    --Nested dictionary with zip code as key, with 
    corresponding city, state, lat, and lon [nested dict]
    """
    zip_data = {}
    
    search = SearchEngine()
    z = search.by_zipcode(zip_code)
    if bool(z) == False: # if zipcode not in database
        print ("Zipcode not found.")
        print ("Defaulting to 94901.")
        zip_code = "94901"
        zip_data = DEFAULT_ZIP_DATA
    else:
        zip_data[z.zipcode] = {
            "city": z.major_city,
            "lat": z.lat,
            "lng": z.lng,
        }

    return zip_data, zip_code


def get_local_zips(lat, lng, rad):
    """
    Gets a list of all zip codes in a given radius
    """
    nearby_locs = {}

    search = SearchEngine()
    result = search.by_coordinates(lat, lng, radius=rad, returns=None)
    for z in result:

        nearby_locs[z.zipcode]={
            "city": z.major_city,
            "lat": z.lat,
            "lng": z.lng,
        }

    return nearby_locs


    # try:
    #     zcdb[zip_code]
    # except (KeyError):
    #     print("Cannot find zip code. Defaulting to San Francisco (94102).")
    #     zip_code = "94102"

    # local_zips = [z.zip for z in zcdb.get_zipcodes_around_radius(zip_code, radius)]

    # return local_zips, zip_code


def get_lat_long_params(nearby_locs):
    """
    Generates three lists:
    --zip codes
    --latitudes
    --longitudes
    """
    zip_codes = []
    latitudes = []
    longitudes = []

    for zip_code in nearby_locs:
        zip_codes.append(zip_code)
        latitudes.append(nearby_locs[zip_code]["lat"])
        longitudes.append(nearby_locs[zip_code]["lng"])

    print ("zip codes =", zip_codes)
    print ("latitudes =", latitudes)
    print ("longitudes =", longitudes)

    return zip_codes, latitudes, longitudes


def get_weather(nearby_locs):
    """
    Uses Open-Meteo to gets weather for each lat/lon provided.
    Parameters: 
    --Nearby locations nested dictionary, with zip codes as keys, and 
    other location information (lat/long) as internal keys within nested
    dictionary [dict] 
    --Example:{
        "94901": {
        "city": "San Francisco"
        "state": "California"
        "lat": ...
        }
    }
    Returns a dictionary where the keys are zip codes and the 
    values are weather results in JSON format [string]
    """
    # Initialize dictionary
    weather_results = {}

    # Display initial status messages
    print("")
    print ("Finding weather...")
    print("(This may take up to a minute.) \n")

    # Extract lat/long lists from nested dictionary of nearby locations
    zip_codes, latitudes, longitudes = get_lat_long_params(nearby_locs)

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    params = {
        "latitude": latitudes,
        "longitude": longitudes,
        "current": "temperature_2m",
        "daily": "temperature_2m_max",
        "temperature_unit": "fahrenheit",
        "forecast_days": 1
    }

    responses = openmeteo.weather_api(API_BASE_URL, params=params)    

    # Process each location
    for i in range(len(responses)):
        print ("Zipcode:", zip_codes[i])
        zip_code = zip_codes[i]
        city = nearby_locs[zip_code]["city"]
        print ("City:", city)

        response = responses[i]
        print(f"Latitude: {response.Latitude()}")
        print(f"Longitude: {response.Longitude()}")

        # Current values. The order of variables needs to be the same as requested.
        current = response.Current()
        current_temperature_2m = current.Variables(0).Value()

        # print(f"Current time {current.Time()}")
        print(f"Current temperature_2m {current_temperature_2m}")

        # Process daily data. The order of variables needs to be the same as requested.
        daily = response.Daily()
        daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
        max_temp = float(daily_temperature_2m_max[0])

        print("Daily max temp: ", max_temp)
        print("---")
        
        weather_results[zip_code] = {
            "city": city,
            "lat": response.Latitude(),
            "lng": response.Longitude(),
            "curr_temp": current_temperature_2m,
            "max_temp": max_temp
        }

    return weather_results


def calculate_coolest_zip(weather_results, my_zip):
    """
    Using the weather results by zip code, determines which nearby
    zip code area has the coolest expected weather that day.
    Parameters:
    --Weather results by zip code [dict]
    --User inputted zip code [string]
    """

    # Set initial coolest_zip and coolest_max_temp to user's zipcode
    coolest_zip = my_zip
    coolest_max_temp = weather_results[coolest_zip]["max_temp"]

    # Compare each zipcode's max_temp with the previous, and store if coolest
    for zip_code in weather_results:
        print ("Comparing to", zip_code,
               "where the max temperature today is",
                round(weather_results[zip_code]["max_temp"], 1), "...")
        if weather_results[zip_code]["max_temp"] < coolest_max_temp:
            coolest_zip = zip_code
            coolest_max_temp = weather_results[zip_code]["max_temp"]

    print("Result found!")

    return coolest_zip


def write_to_file(weather_results_by_zip, filename = "response.json"):
    """
    Writes text to file in the directory. 
    Defaults to filename response.json
    Not used in main program, but helpful for debugging API response issues.
    """
    try:
        f = open(filename, "w", encoding="utf-8")
        try:
            f.write(str(weather_results_by_zip))
            f.close()
            print("Successfully written to " + filename + ".\n")
        except (IOError, OSError):
            print ("Error writing to " + filename + ".")
    except (FileNotFoundError, NameError, PermissionError, OSError):
        return "Error opening " + filename + "."


def display_results(weather_results, my_zip, coolest_zip):
    """
    Displays the current and max temperature in the user's inputted zip code and
    the current and max temperature in the zip code nearby (within the radius) with 
    the coolest max temperature
    """
    select_zips = [my_zip, coolest_zip]

    # If user location (or default) is the coolest zipcode, just show temp and max_temp there
    if my_zip == coolest_zip:
        city_name = weather_results[my_zip]['city']
        curr_temp = round(weather_results[my_zip]['curr_temp'], 1)
        max_temp = round(weather_results[my_zip]['max_temp'], 1)

        print("")
        print("The current temperature in "
              + str(city_name)
              + " (" + str(my_zip) + ")" + " is "
              + str(curr_temp) + " degrees Fahrenheit.")
        print("The max temperature in "
              + str(city_name)
              + " (" + str(my_zip) + ")"
              + " today is expected to be "
              + str(max_temp) + " degrees Fahrenheit.")
        print("Your zip code is expected to be the coolest in the surrounding "
              + str(RADIUS) + "-mile radius.")

    # If the user is not in coolest zip code, display comparison
    else:
        for zip_code in select_zips:
            print("")

            city_name = weather_results[zip_code]['city']
            curr_temp = round(weather_results[zip_code]['curr_temp'], 1)
            max_temp = round(weather_results[zip_code]['max_temp'], 1)

            print("The current temperature in "
                  + str(city_name)
                  + " (" + str(zip_code) + ")" + " is "
                  + str(curr_temp) + " degrees Fahrenheit.")
            print("The max temperature in "
                  + str(city_name)
                  + " (" + str(zip_code) + ")"
                  + " today is expected to be "
                  + str(max_temp) + " degrees Fahrenheit.")


if __name__ == '__main__':
    main()
