# Inteligent Car Shopping with LLM

## Purpose

To create a smart car search assistant to search for cars with user defined parameters. Find cars in a defined area. compare the available cars for reliablity using publicly used data. Compare used car features, milage and condition within parameters and help narrow the choices to the most reliable cars with high value for money.

## Conditions

Should be able to define search area by post code (UK) and search area (miles). Define min and max vehicle costs as listed. Optionally restrict by car make and drive train type (automatic / manual)

## Search example

Use this search URL as basis for search and scrape

`https://www.autotrader.co.uk/car-search?postcode=bt73fn&radius=50&price-to=2500&make=&homeDeliveryAdverts=include&advertising-location=at_cars&page=1`

autotrader provides an API, be it seems to be only available to advertisers

`https://developers.autotrader.co.uk/api`

## Car Data

Use open and avilable APIs and other data to compare car features and documented reliablity

`https://smartcar.com/blog/car-database-api`
`https://developer.edmunds.com/api-documentation/vehicle/`
`https://carfinancesaver.co.uk/blog/top-car-apis/`
`https://vehicledatabases.com/articles/vehicle-data-extraction-api`
`https://www.motorcheck.co.uk/api/`
`https://scrapingrobot.com/blog/car-api/`

## AI Integration

Integration with an LLM is essential to provide a complete decision making process.

Initial use is intended to use Google API and the currently free gemini-2.5 model.

`https://ai.google.dev/gemini-api/docs/quickstart?lang=python`
`https://github.com/google-gemini`

Functionality should include being able to use OpenAI and Anthropic, if easily done. Should also support simple model additions, i.e. Ollama via local install of web address

## Interface

Intended as a terminal application using a terminal GUI, or TUI.

Should allow for selection and configuration of a LLM, and configuration of vehicle search paramters.

## Some thoughts

Make sure and setup the development environment

- Use Poetry to install dependencies and manage the virtual environment.

## Conclusion

I need to buy a car with little money and want to make sure I am making the smartest possible choice