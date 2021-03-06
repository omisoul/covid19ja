import requests
import folium
import pandas as pd
import geopandas as gpd
import os
from flask import Flask, render_template, request, json, send_from_directory
from bs4 import BeautifulSoup as bs


"""
Initialization of the variables that will store the variable statistics

-> countries,cases,deaths and recoveries refers to the world statistics - this data is collected from Wikipedia. 
-> jCases,jDeaths,jRecoveries,jDates refers to data for Jamaica - this data is collected from worldometers.
->worldStats - Overall statistics of COVID-19 in the world - This data is also collected from worldometers
"""
countries = []
cases = []
deaths = []
recoveries = []
countriesDict = {}
jCases = []
jDeaths = []
jRecoveries = []
jDates = []
worldStats = []

# Parish Data - Store the information of active cases in each parish in Jamaica
parishData = {
    'id':['Kingston & St Andrew','St Catherine','Clarendon','Manchester',
    'St Elizabeth','Westmoreland','Hanover','St James','Trelawny','St Ann','St Mary','Portland','St Thomas'],
    'cases':[0,0,0,0,0,0,0,0,0,0,0,0,0]
}


# GraphData - Used to store the data for the graph of Active Cases, Recoveries and Deaths in Jamaica 
class GraphData:
    def __init__(self,gDates,gCases,gDeaths,gRecoveries):
        self.gDates = gDates
        self.gCases = gCases
        self.gDeaths = gDeaths
        self.gRecoveries = gRecoveries

# CountryStats - Used to store the data for different countries. 
class CountryStats:
    def __init__(self,conCases,conDeaths,conRecoveries):
        self.conCases = conCases
        self.conDeaths = conDeaths
        self.conRecoveries = conRecoveries

# Specifically updates Jamaica's information in the countries dictionary (countriesDict)
# It does this by scraping worldometers Jamaica page 
def updateJa():

    url = "https://www.worldometers.info/coronavirus/country/jamaica/"
    html = requests.get(url).text

    soup = bs(html,'html.parser')
    divs = soup.find_all("div",{"class":"maincounter-number"})
    numCases = divs[0].find_all('span')
    numDeaths = divs[1].find_all('span')
    numRecov = divs[2].find_all('span')
    numCases = numCases[0].text.replace(",","")
    numDeaths = numDeaths[0].text.replace(",","")
    numRecov = numRecov[0].text.replace(",","")
    countriesDict['Jamaica'] = [int(numCases),int(numDeaths),int(numRecov)]

# This updates the overall world statistics by scraping worldometer.
def updateWorld():
    global worldStats
    url = "https://www.worldometers.info/coronavirus/"
    html = requests.get(url).text

    soup = bs(html,'html.parser')
    divs = soup.find_all("div",{"class":"maincounter-number"})
    numCases = divs[0].find_all('span')
    numDeaths = divs[1].find_all('span')
    numRecov = divs[2].find_all('span')
    numCases = numCases[0].text
    numDeaths = numDeaths[0].text
    numRecov = numRecov[0].text
    worldStats = [numCases,numDeaths,numRecov]

# This checks for the ajax request and takes the information and formats it in JSON
def retrieveData():
    d = requests.get("https://admin.jamcovid19.moh.gov.jm/public/api/statistics?type=1")
    data = d.json()
    return data

# This uses the data that is returned by retrieveData and updates the parishData dictionary.
def updateMapData():
    global parishData

    data = retrieveData()
    pData = data['data']['parishes_wise_report']

    for pD in pData:

        if pD['parish'] in parishData['id']:
            parishIndex = parishData['id'].index(pD['parish'])
            parishData['cases'][parishIndex] = int(pD['total_cases'])

# Unimplemented
# Retrieves the age, gender and overall statistics of Jamaica COVID-19 patients 
def getStats():
    data = retrieveData()
    stats = [data['age_wise_data'],data['gender_wise_data'],data['overall_statistics']]     


# Retrieves global data from wikipedia table and updates countriesDict
def updateList():
    global countries,cases,deaths,recoveries
    countries = []
    cases = []
    deaths = []
    recoveries = []

    url = "https://en.wikipedia.org/wiki/2019%E2%80%9320_coronavirus_pandemic_by_country_and_territory"
    html = requests.get(url).text

    soup = bs(html,'html.parser')
    table = soup.find_all(id="thetable")

    for data in table:
        rows = data.find_all('tr')

        for row in rows:
            headings = row.find_all('a')
            if len(headings) > 1:
                country = headings[0]
                countries.append(country.getText())

            cells = row.find_all('td')
            if len(cells) > 1:
                cases.append(cells[0].text.strip())
                deaths.append(cells[1].text.strip())
                recoveries.append(cells[2].text.strip())
                
    countries = countries[1:-2]
    for x in range(len(countries)):
        countriesDict.update({countries[x] : [cases[x],deaths[x],recoveries[x]]})

# Retrieves data from Jamaican specific table from Wikipedia.

def updateGraphData():
    global jDates, jCases,jDeaths, jRecoveries
    jDates = []
    jCases = []
    jDeaths = []
    jRecoveries = []
    url = "https://en.wikipedia.org/wiki/2020_coronavirus_pandemic_in_Jamaica"
    html = requests.get(url).text
    soup = bs(html,'html.parser')
    tables = soup.find_all("table")
    data = tables[1]
    rows = data.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) > 1:
            date = cells[0].text.strip()
            jDates.append(date)
            for cell in cells:
                divs = cell.find_all("div")
                if len(divs) >= 3:
                    # Adding no title to any tag that doesn't have a title
                    # The title of each tag contains the information required 
                    case = divs[2].get('title','No title')
                    recovery = divs[1].get('title','No title')
                    death = divs[0].get('title','No title')
                    if case != 'No title':
                        jCases.append(case)
                        jDeaths.append(death)
                        jRecoveries.append(recovery)
                elif len(divs) >= 2:
                    case = divs[1].get('title','No title')
                    recovery = divs[0].get('title','No title')
                    if case != 'No title':
                        jCases.append(case)
                        jDeaths.append('0')
                        jRecoveries.append(recovery)
                elif len(divs) >= 1:
                    case = divs[0].get('title','No title')
                    if case != 'No title':
                        jCases.append(case)
                        jDeaths.append('0')
                        jRecoveries.append('0')


# Used to remove the legend from the folium map.
def fol_legend(choropleth:folium.Choropleth):
    del_list = []
    for child in choropleth._children:
        if child.startswith('color_map'):
            del_list.append(child)
    for del_item in del_list:
        choropleth._children.pop(del_item)
    return choropleth

# Generates an interactive map with the number of cases per parish 
def generateMap():
    # Generate parishes
    parishes = os.path.join('mapdata','jamaicapolygonmap.geojson')
    updateMapData()
    # Create Parish Dataframe
    parishDf = pd.DataFrame.from_dict(parishData)
    nil = gpd.read_file(parishes)
    nil=nil[['id','geometry']]
    nilpop=nil.merge(parishDf,on="id")
    nil.head()
    # Create a map object
    m = folium.Map(location=[18.169340,-77.336837],zoom_start=9)
 
    bins = list(parishDf['cases'].quantile([0, 0.4, 0.6, 0.8, 1]))
    fol_legend(folium.Choropleth(
        geo_data=parishes,
        data=parishDf,
        columns=['id','cases'],
        key_on='feature.id',
        fill_color='YlOrRd',
        fill_opacity = 0.7,
        line_opacity = 0.2,
        control= False,
        legend_name='COVID-19 Cases Per Parish',
        bins=bins,
        reset=True
    )).add_to(m)
    folium.LayerControl().add_to(m)
    for key in m._children:
        if key.startswith('color_map'):
            del(m._children[key])
    style_func = lambda x: {'fillColor': '#ffffff', 
                            'color':'#000000', 
                            'fillOpacity': 0.1, 
                            'weight': 0.1}
    highlight_func = lambda x: {'fillColor': '#000000', 
                                'color':'#000000', 
                                'fillOpacity': 0.50, 
                                'weight': 0.1}
    cases_highlight = folium.features.GeoJson(nilpop,style_function=style_func,control=False,
                                    highlight_function = highlight_func, tooltip=folium.features.GeoJsonTooltip(
                                        fields=['id','cases'],
                                        aliases=['Parish: ','Cases'],
                                        style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;") 
                                    ))
    #Generate map
    m.add_child(cases_highlight)
    m.keep_in_front(cases_highlight)
    folium.LayerControl().add_to(m)
    map_path = 'maps/map.html'
    m.save('maps/map.html')



app = Flask(__name__)

# Homepage Route 
@app.route("/")
def index():
    global cases,recoveries,deaths,jDates
    totalRec = 0
    updateList()
    updateGraphData()
    updateJa()
    generateMap()
    countries.sort()
    
    # Removes commas from the various lists
    cases = [case.replace(",","") for case in cases]
    deaths = [death.replace(",","") for death in deaths]
    recoveries = [recovery.replace(",","") for recovery in recoveries]
    recoveries = [recovery.replace(",","") for recovery in recoveries]

    # Removes 2020- from the jDates list 
    jDates = [jDate.replace("2020-","") for jDate in jDates]
    intJCases = [int(x) for x in jCases]
    intJDeaths = [int(x) for x in jDeaths]
    intJRecoveries = [int(x) for x in jRecoveries]

    gd = GraphData(jDates,intJCases,intJDeaths,intJRecoveries)
    jsStats = countriesDict.get('Jamaica')
    js = CountryStats(jsStats[0],jsStats[1],jsStats[2])
    
    #Coverts the following to Javascrpit Readable data
    jsCountries = json.dumps(countries)
    jsDates = json.dumps(gd.gDates[1:])
    jsCases = json.dumps(gd.gCases)
    jsDeaths = json.dumps(gd.gDeaths)
    jsRecoveries = json.dumps(gd.gRecoveries)


    return render_template("index.html", js = js, 
                            countries = countries, jsCountries = jsCountries, 
                            jsDates =jsDates, jsCases = jsCases, jsDeaths = jsDeaths, jsRecoveries = jsRecoveries)

# Used to display the interactive map
@app.route('/get_map')
def get_map():
    return send_from_directory('maps','map.html')


# Shows the world statistics of COVID-19 cases.
@app.route('/world_statistics', methods=['GET','POST'])
def world_statistics():
    global cases,recoveries,deaths,worldStats
    updateList()
    updateWorld()
    countries.sort()
    cases = [case.replace(",","") for case in cases]
    # deaths = [death.replace(",","") for death in deaths]
    deaths = [death.replace("[^0-9]","") for death in deaths]
    repD = []
    repR = []
    for death in deaths:
        try:
            repD.append(int(death))
        except:
            repD.append(0)

    recoveries = [recovery.replace(",","") for recovery in recoveries]
    recoveries = [recovery.replace("[^0-9]","0") for recovery in recoveries]
    for recovery in recoveries:
        try:
            repR.append(int(recovery))
        except:
            repR.append(0)
    intCases = [int(x) for x in cases]
    intDeaths = [int(x) for x in repD]
    intRecoveries = [int(x) for x in repR]
    con = CountryStats(worldStats[0],worldStats[1],worldStats[2])
    if request.method == 'POST':
        country = request.form.get('country')
        if country == 'The World':
            con = CountryStats(worldStats[0],worldStats[1],worldStats[2])
        else:     
            countryStats = countriesDict.get(country)
            con = CountryStats(countryStats[0],countryStats[1],countryStats[2])
        return render_template("world.html",countries = countries,con=con, select = country)
    return render_template("world.html",countries = countries, con=con, select = 'The World')

