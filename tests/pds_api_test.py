from __future__ import print_function
from pds.api_client.exceptions import ApiException
from pds.api_client.configuration import Configuration
from pds.api_client.api_client import ApiClient

configuration = Configuration()
api_client = ApiClient(configuration)

from pds.api_client.api import all_products_api
from pprint import pprint

products_api = all_products_api.AllProductsApi(api_client)

try:
    api_response = products_api.product_list(q="M192545545RC", limit=20)
    pprint(api_response)
except ApiException as e:
    print("Exception when calling CollectionsApi->get_collection: %s\n" % e)