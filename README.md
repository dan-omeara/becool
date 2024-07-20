# Be Cool

A console program that tells the user what the coolest location in a 10-mile radius of them is. This is ideal for avoiding hotspots during heatwaves, and is particularly well-suited to [microclimates](https://en.wikipedia.org/wiki/Microclimate#Cities_and_regions_known_for_microclimates).

The program uses [Open-Meteo](https://open-meteo.com/), which does not require a user API key. Note, however, that the limit is 10,000 requests daily. 

This currently only works in the US as it relies on zip codes.

## Technical Details

To determine the coolest nearby location:
* User inputs zip code.
* Using the uszipcode package, gets a list of local zips within a given radius. 
* Gets the weather data for these zipcodes through a bulk API call to Open-Meteo; note that Open-Meteo supports bulk calls with up to 1000 locations in a single call.
* Processes weather data to a more readable format for debugging
* Compares the daily maximum temperature for each zip code to determine coolest zip code
* Displays results

## Packages used

* time - only used for debugging API responses
* openmeteo_requests - for API request
* requests_cache - for API request
* retry_requests - for API request
* uszipcode - for offline zip code calculations and lookups

## Todo

* Set up limits for API calls (1000 location limit)
* Build out front end GUI

