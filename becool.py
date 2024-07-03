"""
File: becool.py
Author: Dan O'Meara
---
Weather app to determine coolest place in local area.
Best suited for microclimates.
TODO:
--Issues with API accuracy. Switch to Open-Meteo (https://open-meteo.com/)
--Switch from zip-code setup to lat/long
"""

# Used for debugging API responses
# import time 

import requests
from pyzipcode import ZipCodeDatabase
import constants


API_BASE_URL = "http://api.weatherapi.com/v1/forecast.json"
API_KEY = constants.API_KEY
RADIUS = 10 # miles

def main():
    """
    Asks user for zip code, then determines the coolest zipcode within a given radius.
    Radius is set as a constant (currently 10 miles).
    """
    while True:
        zip_code = input("Enter your zip code: ")
        nearby_zips, zip_code = get_local_zips(zip_code, RADIUS)
        print("There are " + str(len(nearby_zips))
              + " zip codes within a " + str(RADIUS) + " mile radius.")
        input("Press any key to continue.")
        weather_results = get_weather(nearby_zips)

        # Used for debugging API responses
        # write_to_file(weather_results, filename = str(time.time()))

        coolest_zip, cleaned_results = calculate_coolest_zip(weather_results, zip_code)
        display_results(cleaned_results, zip_code, coolest_zip)
        print("")


def get_local_zips(zip_code, radius):
    """
    Gets a list of local locations surrounding the given zip_code, within the given radius.
    Uses the pyzipcode package.
    For errors in input or unknown zip codes (note that not all 5-digit numbers 
    have been assigned as zip codes), the function defaults to San Francisco (94101).
    Returns:
    --Local zip codes [list]
    --User-inputted zip code, changing it to 94101 if it is not found [integer]
    """
    zcdb = ZipCodeDatabase()
    local_zips = []
    try:
        local_zips = [z.zip for z in zcdb.get_zipcodes_around_radius(zip_code, radius)]
    except KeyError:
        print("Cannot find zip code. Defaulting to San Francisco (94101).")
        zip_code = "94101"
        local_zips = [z.zip for z in zcdb.get_zipcodes_around_radius(zip_code, radius)]

    return local_zips, zip_code


def get_weather(nearby_zips):
    """
    Uses WeatherAPI to gets weather for each zip code provided.
    Parameters: 
    --Nearby zip codes [list]
    Returns a dictionary where the keys are zip codes and the 
    values are weather results in JSON format [string]
    """
    # Display initial status messages
    print("")
    print ("Finding weather...")
    print("(This may take up to a minute.) \n")

    # Attempt to not get cached answers
    h = {
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

    # Query API
    weather_results_by_zip = {}
    for zip_code in nearby_zips:
        params = {
            "q": zip_code,
            "days" : "1",
            "key": API_KEY,
        }
        response = requests.get(API_BASE_URL, params, timeout = 10, headers = h)

        # For debugging API responses
        # write_to_file(response.json(), filename=(zip_code + ".json"))

        weather_results_by_zip.update({zip_code: response.json()})

    return weather_results_by_zip


def calculate_coolest_zip(weather_results_by_zip, my_zip):
    """
    Using the weather results by zip code, determines which nearby
    zip code area has the coolest expected weather that day.
    Parameters:
    --Weather results by zip code [dict]
    --User inputted zip code [string]
    """
    cleaned_results = {}

    for zip_code in weather_results_by_zip:
        # Skipping any issues in data from API
        if "error" in weather_results_by_zip[zip_code]:
            continue
        else:
            location = weather_results_by_zip[zip_code]["location"]
            curr_weather = weather_results_by_zip [zip_code]["current"]
            forecast_weather = weather_results_by_zip [zip_code]["forecast"]

            city_name = location['name']
            curr_temp = curr_weather['temp_f']
            avg_temp = forecast_weather["forecastday"][0]["day"]["avgtemp_f"]
            max_temp = forecast_weather["forecastday"][0]["day"]["maxtemp_f"]

            cleaned_results.update({zip_code: {
                "city_name": city_name,
                "curr_temp": curr_temp,
                "avg_temp" : avg_temp, # not currently used, but useful for testing
                "max_temp": max_temp,
            }})

    if not cleaned_results:
        print("Error. Zip codes not recognized by weather database.")

    else:
        # Set initial coolest_zip and coolest_max_temp to user's zipcode
        coolest_zip = my_zip
        coolest_max_temp = cleaned_results[coolest_zip]["max_temp"]

        # Compare each zipcode's max_temp with the previous, and store if coolest
        for zip_code in cleaned_results:
            print ("Comparing to", zip_code, "where the max temperature today is",
                   cleaned_results[zip_code]["max_temp"], "...")
            if cleaned_results[zip_code]["max_temp"] < coolest_max_temp:
                coolest_zip = zip_code
                coolest_max_temp = cleaned_results[zip_code]["max_temp"]

    print("Result found!")

    return coolest_zip, cleaned_results


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


def display_results(cleaned_results, my_zip, coolest_zip):
    """
    Displays the current and max temperature in the user's inputted zip code and
    the current and max temperature in the zip code nearby (within the radius) with 
    the coolest max temperature
    """
    select_zips = [my_zip, coolest_zip]

    # If user location (or default) is the coolest zipcode, just show temp and max_temp there
    if my_zip == coolest_zip:
        city_name = cleaned_results[my_zip]['city_name']
        curr_temp = cleaned_results[my_zip]['curr_temp']
        max_temp = cleaned_results[my_zip]['max_temp']

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

            city_name = cleaned_results[zip_code]['city_name']
            curr_temp = cleaned_results[zip_code]['curr_temp']
            max_temp = cleaned_results[zip_code]['max_temp']

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
