# Be Cool

A console program that tells the user what the coolest location in a 10-mile radius of them is. This is ideal for avoiding hotspots during heatwaves, and is particularly well-suited to [microclimates](https://en.wikipedia.org/wiki/Microclimate#Cities_and_regions_known_for_microclimates).

The program uses [WeatherAPI](https://www.weatherapi.com/), although initial testing is showing some accuracy issues, so this may be changed in future versions. The user would need to have their own API key to use the program -- this can be obtained for free from WeatherAPI by registering.

This currently only works in the US as it relies on zip codes.

## Technical Details

To determine the coolest nearby location:
* User inputs zip code.
* Using the pyzipcode package, gets a list of local zips within a given radius. (Note that pyzipcode indicates that this radius is not a circle, but rather a square).
* Gets the weather data for these zipcodes through individual API calls to WeatherAPI
* Cleans weather data to a more readable format for debugging
* Compares the daily maximum temperature for each zip code to determine coolest zip code
* Displays results

## Packages used

* time - only used for debugging API responses
* requests - for API requests
* pyzipcode - for offline zip code calculations and lookups

## Todo

* Switch to different API
* Likely shift to lat/long instead of zip codes
* Build out front end GUI

