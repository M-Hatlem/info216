# requires request library, download at: pip install requests
# requires request BeautifulSoup4, download at: pip install beautifulsoup4
import requests
import json
import re
from rdflib import Graph, Namespace, Literal
from bs4 import BeautifulSoup


class NavData:
    def __init__(self, token):
        self.token = token
        self.graph = Graph()
        self.data = None

    # This function downloads the data set from Nav, it requires a token as an input
    def download_data(self):
        api_endpoint = 'https://arbeidsplassen.nav.no/public-feed/api/v1/ads?size=4999'
        api_headers = {'accept': 'application/json',
                       'Authorization': 'Bearer ' + self.token}
        download = requests.get(url=api_endpoint, headers=api_headers)
        if download.status_code == 200:
            self.data = download.json()
            print("Download complete")
            return True
        elif download.status_code == 401:
            print(
                "Error 401 not authorized, public token likely expired. Get a new one at: https://github.com/navikt/pam-public-feed")
            return False
        else:
            print("Error: " + str(download.status_code))
            return False

    # if you want to save the json data downloaded, do this after a download:
    def save_json(self):
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    # If you want to load a JSON file saved earlier, you can load a JSON document with nav data using this command. if you do this you don't need to download data
    def load_data(self):
        with open("data.json", "r", encoding='utf-8') as json_file:
            self.data = json.load(json_file)

    # This function lifts the data downloaded from nav into rdf triples
    def lift_data(self):
        graph = self.graph
        nameSpace = Namespace("http://example.org/")
        graph.bind("ex", nameSpace)
        nav_data = self.data
        for job_ad in nav_data['content']:
            unique_key = job_ad['uuid']
            for graph_predicate in job_ad:
                if type(job_ad[graph_predicate]) is list:
                    graph.add((nameSpace[unique_key], nameSpace[graph_predicate], nameSpace[graph_predicate + "-unique_key-" + unique_key]))
                    for dict_data_from_list in job_ad[graph_predicate]:
                        for elm_in_list in dict_data_from_list:
                            graph.add((nameSpace[graph_predicate + "-unique_key-" + unique_key], nameSpace[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                elif type(job_ad[graph_predicate]) is dict:
                    graph.add((nameSpace[unique_key], nameSpace[graph_predicate], nameSpace[graph_predicate + "-unique_key-" + unique_key]))
                    job_data_dict = job_ad[graph_predicate]
                    for dict_data_from_dict in job_data_dict:
                        if dict_data_from_dict == "description" and job_data_dict[dict_data_from_dict] is not None:
                            graph.add((nameSpace[graph_predicate + "-unique_key-" + unique_key], nameSpace[dict_data_from_dict], Literal(self.clean_html_tag(job_data_dict[dict_data_from_dict]))))
                        else:
                            graph.add((nameSpace[graph_predicate + "-unique_key-" + unique_key], nameSpace[dict_data_from_dict], Literal(job_data_dict[dict_data_from_dict])))
                elif graph_predicate == "description" and job_ad[graph_predicate] is not None:
                    graph.add((nameSpace[unique_key], nameSpace[graph_predicate], Literal(self.clean_html_tag(job_ad[graph_predicate]))))
                elif type(job_ad[graph_predicate]) is str:
                    graph.add((nameSpace[unique_key], nameSpace[graph_predicate], nameSpace[self.clean_spaces(job_ad[graph_predicate])]))
                else:
                    graph.add((nameSpace[unique_key], nameSpace[graph_predicate], Literal(job_ad[graph_predicate])))
            # To test run on only one ad remove # on #break
            #break

    # This function removes html tags from the description of the ads
    def clean_html_tag(self, in_data):
        soup = BeautifulSoup(in_data, 'html.parser')
        out_data = soup.get_text()
        out_data = out_data.replace("\r", "")
        out_data = out_data.replace("\n", "")
        return out_data

    # This function removes new lines from the description of the ads
    def clean_spaces(self, in_data):
        in_data = re.sub(' ', '_', in_data)
        in_data = re.sub("'", '', in_data)
        out_data = re.sub('"', '', in_data)
        return out_data

    # This function serializes the data to a turtle file and saves it locally
    def serialize(self):
        self.graph.serialize(destination='nav_data.txt', format='turtle')


if __name__ == "__main__":
    api_public_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwdWJsaWMudG9rZW4udjFAbmF2Lm5vIiwiYXVkIjoiZmVlZC1hcGktdjEiLCJpc3MiOiJuYXYubm8iLCJpYXQiOjE1NTc0NzM0MjJ9.jNGlLUF9HxoHo5JrQNMkweLj_91bgk97ZebLdfx3_UQ'
    nav = NavData(api_public_token)
    nav.download_data()
    nav.lift_data()
    nav.serialize()

# TODO: Looka at URI's and TimeDates, make literals instead of objects???

# TODO: Replace example with out own ontology

# TODO: create a fucntion that imports replaces ex in schema and other vocab properties in the finished file
