import psycopg2
import pandas as pd
from os import listdir, makedirs
from os.path import isfile, join, exists
import datetime
import sys
import progressbar
from time import sleep

#============================== Functions =================================#
def connectDB(dbname = 'mygreencar', user='mygreencar',host='localhost'):
	"""
	Connect to postgreSQL db
	"""
	url =  "dbname=%s user=%s host=%s" % (dbname,user,host)
	try:
		conn = psycopg2.connect(url)
	except:
		print "I am unable to connect to the database"
	return conn, conn.cursor()

def pushQuery(query):
	"""
	Query that does not need return values
	"""
	cur.execute(query)


def pullQuery(query):
	"""
	Query that has return values
	"""
	cur.execute(query)
	return cur.fetchall()

def printProgressBar(count, total, suffix=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', suffix))
    sys.stdout.flush()

#============================== Main script ===============================#
# Connect to db and get connection manager: conn and cursor: cur
conn, cur = connectDB()

# input directory of trips here
dirPath 	= "/Users/mygreencar/Documents/workspace/trips_with_consumptions/"
# output directory 
outputPath  = "/Users/mygreencar/Documents/workspace/trips_with_cons_link_id/"
tripFiles = [f for f in listdir(dirPath) if not f.startswith('.')]

#----------- for loop for trip tripFiles here ------------#
# resultDir = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S_")+'trip_with_link_id'
resultDir = 'results'
if not (exists(join(outputPath, resultDir))):
    makedirs(join(outputPath, resultDir))

for n,inputFile in enumerate(tripFiles):
    if not (exists(join(outputPath, resultDir, inputFile))):
        shouldSkipThisFile = False
        print (str(n+1) + '/' + str(len(tripFiles)) + ': ' + inputFile + '\n')

        dfData = pd.read_csv(join(dirPath, inputFile))
        dfData.dropna(axis=1,how='all',inplace=True)
        if(dfData["timestamp"].isnull().values.any()):
            dfData.drop(dfData.index[[0,1]], inplace=True)
            dfData.reset_index(drop=True, inplace=True)
        
        lngArr = dfData["longitude"]
        latArr = dfData["latitude"]
        if(lngArr.isnull().values.any()):
            for ind in lngArr[lngArr.isnull() == True].index.tolist():
                if(ind == 0):            
                    lngArr[ind] = lngArr[ind+1]
                else:
                    lngArr[ind] = lngArr[ind-1]
        if(latArr.isnull().values.any()):
            for ind in latArr[latArr.isnull() == True].index.tolist():
                if(ind == 0):            
                    latArr[ind] = latArr[ind+1]
                else:
                    latArr[ind] = latArr[ind-1]
        
        ## Skil this trip if empty trip
        if(len(lngArr)==0):
            continue

        ## Get the list of CA queryResult
        gidArr = []
        osmIdArr = []
        bar = progressbar.ProgressBar(maxval=len(lngArr), \
            widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
        bar.start()
        for i,(lng,lat) in enumerate(zip(lngArr, latArr)):
            qResult = pullQuery("select gid,osm_id from ca_osm_roads where st_dwithin(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326), 0.0005) ORDER BY ST_Distance(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326)) limit 1;"%(lng,lat,lng,lat))
            if(len(qResult) == 0):
                qResult = pullQuery("select gid,osm_id from ca_osm_roads where st_dwithin(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326), 0.001) ORDER BY ST_Distance(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326)) limit 1;"%(lng,lat,lng,lat))
            if(len(qResult) == 0):
                qResult = pullQuery("select gid,osm_id from ca_osm_roads where st_dwithin(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326), 0.002) ORDER BY ST_Distance(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326)) limit 1;"%(lng,lat,lng,lat))
            if(len(qResult) == 0):
                qResult = pullQuery("select gid,osm_id from ca_osm_roads where st_dwithin(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326), 0.005) ORDER BY ST_Distance(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326)) limit 1;"%(lng,lat,lng,lat))
            if(len(qResult) == 0):
                qResult = pullQuery("select gid,osm_id from ca_osm_roads where st_dwithin(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326), 0.01) ORDER BY ST_Distance(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326)) limit 1;"%(lng,lat,lng,lat))
            if(len(qResult) == 0):
                qResult = pullQuery("select gid,osm_id from ca_osm_roads where st_dwithin(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326), 0.1) ORDER BY ST_Distance(ca_osm_roads.geom, ST_GeomFromText('Point(%s %s)',4326)) limit 1;"%(lng,lat,lng,lat))
            if(len(qResult) == 0):
                shouldSkipThisFile = True
                break
            gidArr.append(qResult[0][0])
            osmIdArr.append(qResult[0][1])
            bar.update(i+1)
        
        if not (shouldSkipThisFile):
            # save trip file with associated link ids
            dfgid = pd.DataFrame(gidArr,columns=['gid'])
            dfosmIdArr = pd.DataFrame(gidArr,columns=['osm_id'])
            df = pd.concat([dfData, dfgid, dfosmIdArr],axis=1)
            df.to_csv(join(outputPath, resultDir, inputFile), index=False)

#------------ for loop for trip tripFiles to here -----------# 
cur.close()
conn.close()