import json
import urllib.request
import urllib.parse

# User
import config

def category(uid_list):
    url = 'http://octopart.com/api/v3/categories/get_multi'
    url += '?apikey='
    url += config.apikey

    args = []
    for uid in uid_list:
        args.append(('uid[]', uid))

    url += '&' + urllib.parse.urlencode(args)
    data = urllib.request.urlopen(url).read()
    server_response = json.loads(data)

    categories = []

    for (uid, category) in server_response.items():
        categories.append(category['name'])

    return tuple(categories)


def search(keyword):
    url = 'http://octopart.com/api/v3/parts/search'
    url += '?apikey='
    url += config.apikey

    args = [
    ('q', keyword),
    ('start', 0),
    ('limit', 9)
    ]

    url += '&' + urllib.parse.urlencode(args)
    data = urllib.request.urlopen(url).read()
    search_response = json.loads(data)

    # variants = [('Found', search_response['hits'], '', '')]
    variants = [search_response['hits']]

    for result in search_response['results']:
        # variants.append((result['item']['mpn'], result['item']['manufacturer']['name'], result['snippet'], result['item']['uid']))

        r = {
            'uid'             :result['item'   ]['uid'],
            'part_number'     :result['item'   ]['mpn'],
            'octopart_url'    :result['item'   ]['octopart_url'],
            'manufacturer'    :result['item'   ]['manufacturer']['name'],
            'manufacturer_url':result['item'   ]['manufacturer']['homepage_url'],
            'description'     :result['snippet']
        }

        variants.append(r)

    return variants


def part(uid):    
    url = 'http://octopart.com/api/v3/parts/'
    url += uid
    url += '?'
    url += '&apikey='
    url += config.apikey
    url += '&include[]=specs'
    url += '&include[]=short_description'
    url += '&include[]=category_uids'
    url += '&include[]=datasheets'

    data = urllib.request.urlopen(url).read()
    item = json.loads(data)

    params = {}

    params['UID'] = uid
    params['Part Number'] = item['mpn']
    params['Manufacturer'] = item['manufacturer']['name']
    params['Part Description'] = item['short_description']

    for spec in item['specs']:
        try:
            params['<' + item['specs'][spec]['metadata']['name'] + '>'] = \
                         item['specs'][spec]['display_value']
        except:
            params['<' + item['specs'][spec]['metadata']['name'] + '>'] = None

    params['Categories'] = category(item['category_uids'])  

    params['Datasheets'] = []
    for option in item['datasheets']:
        try:
            params['Datasheets'].append((option['attribution']['sources'][0]['name'], option['url']))
        except:
            pass
    params['Datasheets'] = tuple(params['Datasheets'])

    return params

