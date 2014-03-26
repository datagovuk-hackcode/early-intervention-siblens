import os
import json
from decimal import Decimal

import unicodecsv as csv
from geopy.geocoders import GoogleV3
import requests
import arrow

geocoder = GoogleV3()

DATA_PATH = '../data'
CPID_PATH = DATA_PATH + '/' + 'CPID_uniques.csv'

def load_cpids(path=CPID_PATH):
    cpids = {}
    with open(path, 'rb') as f:
        reader = csv.reader(f)
        header = reader.next()
        for row in reader:
            cpids[row[5]] = dict(zip(header, row))
    return cpids

def fetch_data():
    fnames = os.listdir(DATA_PATH+'/'+'councils')
    cpids = load_cpids()
    councils = {}
    file_count = len(fnames)
    i = 0
    for fname in fnames:
        i += 1
        # print 'Processing file %s of %s: %s' % (i , file_count, fname)
        unique_code = '_'.join(fname.split('_')[:-2])
        date = '-'.join(fname.split('_')[-2:])
        date = (date + "-01").replace('.csv', '') 
        if unique_code in cpids:
            council = load_council_csv(DATA_PATH+'/councils/'+fname)
            if unique_code not in councils.keys():
                councils[unique_code] = {}
            if date not in councils[unique_code].keys():
                councils[unique_code][date] = []                
            councils[unique_code][date].append(council)
    return councils
                
def load_council_csv(path):
    data = []
    with open(path, 'rb') as f:
        reader = csv.reader(f)
        header = reader.next()
        for row in reader:
            if (row[0]+row[1]).strip() == '':
                break
            data.append(row)
            # data['spending'].append(dict(zip(header, row)))
    return data

def match_category(category, month):
    # Dummy implementation pending classifier
    from random import sample
    return sample(month, 20)

def total_spend(month):
    INDEX = 0
    if month[0][0] == '':
        INDEX = 1
    return sum([Decimal(x[INDEX].strip()) for x in month])

def geocode(address):
    try:        
        place = geocoder.geocode(address)
    except:
        return None
    return place

def get_council(place):
    try:
        raw = place.raw
        location = raw['geometry']['location']
        pcode_path = 'http://uk-postcodes.com/latlng/%s,%s.json' % (location['lat'], location['lng'])
        resp = requests.get(pcode_path)
        pcode_data = json.loads(resp.text)
        council = pcode_data['administrative']['council']['title']
    except:
        return None
    return council

def get_location_council(address):
    return get_council(geocode(address))

def load_from_file_cache(fname, fn):
    try:
        f = open(fname, 'r')
        res = json.load(f)
        f.close()
        return res
    except:
        f = open(fname, 'w')
        res = fn()
        json.dump(res, f)
        f.close()
        return res
