import os
import json
from decimal import Decimal

import unicodecsv as csv
from geopy.geocoders import GoogleV3
import requests
#import arrow

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

def build_cpid_names():
    fnames = os.listdir(DATA_PATH+'/'+'councils')
    cpids = load_cpids()
    cpid_names = {}
    for fname in fnames:
        unique_code = '_'.join(fname.split('_')[:-2])
        curr = cpids[unique_code]['Clean entity'].title()
        if unique_code in cpids and curr not in cpid_names:
            cpid_names[curr] = unique_code
    return cpid_names

MAPPING = {
    'City of Westminster':'Westminster City Council',
    'Lewisham':'Lewisham London Borough Council'
    }

def fetch_cost(term="Rough sleeping"):
    resp = requests.get('http://unitcost.toastwaffle.com/api/entry?search=%s' % term)
    data = json.loads(resp.text)['data']
    first = data[0]
    cost = first['current_cost']
    return cost

def load_council_csv(path):
    data = []
    print path
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
    total = sum([Decimal(x[INDEX].strip()) for x in month])
    return "%0.2f" % float(total)

def geocode(address):
    address = address + ', London, United Kingdom'    
    try:        
        place = geocoder.geocode(address)
        print 'Address is %s' % address
    except Exception as e:
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
        f = open(fname, 'rb')
        res = json.load(f)
        f.close()
        return res
    except:
        f = open(fname, 'w')
        res = fn()
        json.dump(res, f)
        f.close()
        return res

def parse_query(query):
    args = query.split(' ')
    council = ''
    category = ''
    place = None
    if 'around' in args:
        place = geocode(' '.join(args[args.index('around')+1:]))
        print place
        council = get_council(place)
        category = ' '.join(args[1:args.index('around')])
    return (category, council, place)

def fetch_history(council, councils):
    history = {'labels':[], 'data':[]}
    try:
        cpids = build_cpid_names()
        cname = MAPPING[council]
        cpid = cpids[cname]
        all = councils[cpid]
        keys = sorted(all.keys())
        for month in keys:
            history['labels'].append(month)
            focus = all[month][0][:20]
            history['data'].append(total_spend(focus))
    except Exception as e:
        print e
    return json.dumps(history)
