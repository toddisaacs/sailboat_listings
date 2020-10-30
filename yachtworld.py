import json
import requests
import re
import datetime
import csv
import bs4
import pandas
from bs4 import BeautifulSoup
from pandas import DataFrame

# class to make easier to access JSON
class JSONObject(object):
    def __init__(self, data):
	    self.__dict__ = json.loads(data)


DOMAIN = 'www.yachtworld.com'
QUERY = '/boats-for-sale/type-sail/region-northamerica/?'
FROM_LENGTH = '37'
TO_LENGTH = '40'
KEYWORD = ''

URL = 'https://'+ DOMAIN + QUERY + 'length=' + FROM_LENGTH + '-' + TO_LENGTH

if len(KEYWORD) > 0:
  URL = URL + '&keyword=' + KEYWORD
print("URL: ", URL)

pageRequest = 1
boatList = []
firstRow = ['Make', 'Model', 'Length', 'Year', 'Price', 'Created', 'City', 'State', 'Country', 'Status', 'Image', 'Link']
boatList.append(firstRow)
iterations = 0
MAX_ITERATIONS = 150

def extractdata(url):
  page = requests.get(url)
  soup = BeautifulSoup(page.content, 'html.parser')

  # extract data from Redux in script tag as JSON
  redux_script = soup.find('script', text=re.compile(".*window.__REDUX_STATE__ =.*"))
  script_text = redux_script.string.replace(';','').replace('window.__REDUX_STATE__ = ','').strip()
  
  ##### Uncomment below to look at the JSON in Redux state #####
  # print(type(redux_script))
  # parsed_json = (json.loads(script_text))
  # print(json.dumps(parsed_json, indent=4, sort_keys=True))
  #####

  data = JSONObject(script_text)

  try:
    lastPage = data.search['searchResults']['search']['lastPage'] or 0
    count = data.search['searchResults']['search']['count'] or 0
    currentPage = data.search['searchResults']['search']['currentPage'] or 0
    currentPageSize = data.search['searchResults']['search']['currentPageSize'] or 0
  except:
    print("EXCEPTION - Failed to get page information")
    lastPage = 0
    count =  0
    currentPage = 0
    currentPageSize =  0

  print("Total records: " + str(count), "Current Page: " + str(currentPage), "Last Page: " + str(lastPage), "Page Size: " + str(currentPageSize))

  records = data.search['searchResults']['search']['records']

  for record in records:
    make = record['make'] or ""
    try:
      model = record['model'] 
    except:
      model = ""
    year = record['year'] or 0
    status = record['status'] or ""

    city = (record['location']).get('city') or ""
    state = (record['location']).get('countrySubDivisionCode') or ""
    country = (record['location']).get('countryCode') or ""
    created = record['date']['created'] or ""
    created_date = datetime.datetime.strptime(created, "%Y-%m-%dT%H:%M:%SZ")
    
    mappedURL = record['mappedURL'] or ""

    try:
      price_elem = record.get('price')
      price = price_elem['type']['amount']['USD']
    except:
      price = 0

    try:
      length = record['boat']['specifications']['dimensions']['lengths']['nominal']['ft']
    except:
      length = 0

    try:
      image = record['media'][0]['url']
      image = 'https://images.yachtworld.com/resize' + image 
      image = image.replace('LARGE', 'XLARGE')
    except:
      image = ""
  
    # print( make, model,  str(length), str(year) , str(price), created_date.strftime('%x') ,city, state, country, status, image, mappedURL)
    boat = [make, model, length, year , price, created_date.strftime('%x'), city, state, country, status, image, mappedURL]
    boatList.append(boat)

    print(boat)
  # End loop

  global pageRequest
  global iterations
  iterations = iterations + 1

  if pageRequest < lastPage and iterations < MAX_ITERATIONS:
     
    pageRequest = pageRequest + 1
    print("Extracting page ", pageRequest)
    nextURL = URL+ "&page=" + str(pageRequest)
    print(nextURL)

    extractdata(nextURL)
  # End if
# End function extractdata(url)

# execute script   
extractdata(URL)

filename = DOMAIN + '_' + FROM_LENGTH + '_' + TO_LENGTH + '_' + KEYWORD + '.csv'

with open (filename,'w') as file:
   writer=csv.writer(file)
   for row in boatList:
      writer.writerow(row)
