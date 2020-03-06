# requires request library, download at: pip install requests
# requires BeautifulSoup4, download at: pip install beautifulsoup4
# requires rdflib, download at: pip install rdflib
import requests
import json
import re
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import XSD
from bs4 import BeautifulSoup


class NavData:
    def __init__(self, token):
        self.token = token
        self.graph = Graph()
        self.data = None

    # allows you to update nav's download token
    def update_token(self, new_token):
        self.token = new_token

    # This function downloads the data set from Nav, it requires a token as an input
    def download_data(self):
        api_endpoint = 'https://arbeidsplassen.nav.no/public-feed/api/v1/ads?size=4999'
        api_headers = {'accept': 'application/json',
                       'Authorization': 'Bearer ' + self.token}
        download = requests.get(url=api_endpoint, headers=api_headers)
        if download.status_code == 200:
            self.data = download.json()
            print("Download complete")
            self.lift_data()
            return True
        elif download.status_code == 401:
            print(
                "Error 401 not authorized, public token likely expired. Get a new one at: https://github.com/navikt/pam-public-feed")
            return False
        else:
            print("Error: " + str(download.status_code))
            return False

    # if you want to save the json data downloaded, do this after a download, requires filname as input:
    def save_json(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)

    # If you want to load a JSON file saved earlier, you can load a JSON document with nav data using this command. if you do this you don't need to download data, requires filename as input
    def load_json(self, filename):
        with open(filename, "r", encoding='utf-8') as json_file:
            self.data = json.load(json_file)
        self.lift_data()

    # This function lifts the data downloaded from nav into rdf triples
    def lift_data(self):
        ns = Namespace("http://example.org/")
        self.graph.bind("ex", ns)
        for job_ad in self.data['content']:
            unique_key = job_ad['uuid']
            for graph_predicate in job_ad:
                if type(job_ad[graph_predicate]) is list:
                    self.graph.add((ns[unique_key], ns[graph_predicate], ns[graph_predicate + "-unique_key-" + unique_key]))
                    for dict_data_from_list in job_ad[graph_predicate]:
                        for elm_in_list in dict_data_from_list:
                            self.graph.add((ns[graph_predicate + "-unique_key-" + unique_key], ns[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                elif type(job_ad[graph_predicate]) is dict:
                    self.graph.add((ns[unique_key], ns[graph_predicate], ns[graph_predicate + "-unique_key-" + unique_key]))
                    job_data_dict = job_ad[graph_predicate]
                    for dict_data_from_dict in job_data_dict:
                        if dict_data_from_dict == "description" and job_data_dict[dict_data_from_dict] is not None:
                            self.graph.add((ns[graph_predicate + "-unique_key-" + unique_key], ns[dict_data_from_dict], Literal(self.clean_html_tags(job_data_dict[dict_data_from_dict]))))
                        else:
                            self.graph.add((ns[graph_predicate + "-unique_key-" + unique_key], ns[dict_data_from_dict], Literal(job_data_dict[dict_data_from_dict])))
                elif graph_predicate == "description" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(self.clean_html_tags(job_ad[graph_predicate]))))
                elif (graph_predicate == "applicationDue" or graph_predicate == "expires" or graph_predicate == "starttime" or graph_predicate == "published" or graph_predicate == "updated") and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif (graph_predicate == "link" or graph_predicate == "sourceurl" or graph_predicate == "positioncount") and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate])))
                elif type(job_ad[graph_predicate]) is str and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], ns[graph_predicate], ns[self.clean_text(job_ad[graph_predicate])]))
                else:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate])))
            # To test run on only one ad remove # on #break
            #break
        self.add_vocab()

    # This function removes html tags and new lines from the description of the ads
    @staticmethod
    def clean_html_tags(in_data):
        soup = BeautifulSoup(in_data, 'html.parser')
        out_data = soup.get_text()
        out_data = out_data.replace("\r", "")
        out_data = out_data.replace("\n", "")
        return out_data

    # This function removes new lines, ' and " from the description of the ads
    @staticmethod
    def clean_text(in_data):
        in_data = re.sub(' ', '_', in_data)
        in_data = re.sub("'", '', in_data)
        out_data = re.sub('"', '', in_data)
        return out_data

    # This function serializes the data to a turtle file and saves it locally. Requires a name to save as
    def serialize(self, filename):
        self.graph.serialize(destination=filename, format='turtle')

    # This function allows you to load a turtle file you previously serialized into the graph, requires the name of the file to load
    def load_serialized_data(self, filename):
        self.graph.parse(filename, format="turtle")

    # This function adds the other vocabs, and replaces the prefixes of our custom ontology with the more used ones
    def add_vocab(self):
        sch = Namespace("http://schema.org/")  # TODO example properties, remember to change
        self.graph.bind("sch", sch)  # TODO example properties, remember to change
        foaf = Namespace("http://foaf.org/")  # TODO example properties, remember to change
        self.graph.bind("foaf", foaf)  # TODO example properties, remember to change
        temp_graph = self.graph.serialize(format="turtle")
        temp_graph = temp_graph.decode("utf-8")
        new_graph = ""
        for line in temp_graph.split("\n"):
            if "ex:description" in line or "ex:published" in line or "ex:title" in line:  # TODO example properties, remember to change
                line = line.replace("ex:description", "sch:description")  # TODO example properties, remember to change
                line = line.replace("ex:published", "sch:published")  # TODO example properties, remember to change
                line = line.replace("ex:title", "sch:title")  # TODO example properties, remember to change
                new_graph = new_graph + line + "\n"
            elif "ex:name" in line or "ex:extent" in line:  # TODO example properties, remember to change
                line = line.replace("ex:name", "foaf:extent")  # TODO example properties, remember to change
                line = line.replace("ex:extent", "foaf:extent")  # TODO example properties, remember to change
                new_graph = new_graph + line + "\n"
            else:
                new_graph = new_graph + line + "\n"
        # self.graph=Graph()  # De-commenting this will overwrite the original ex:properies instead of having both the new and the old ones
        self.graph.parse(data=new_graph, format="turtle")


if __name__ == "__main__":
    api_public_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwdWJsaWMudG9rZW4udjFAbmF2Lm5vIiwiYXVkIjoiZmVlZC1hcGktdjEiLCJpc3MiOiJuYXYubm8iLCJpYXQiOjE1NTc0NzM0MjJ9.jNGlLUF9HxoHo5JrQNMkweLj_91bgk97ZebLdfx3_UQ'
    nav = NavData(api_public_token)
    #nav.update_token(api_public_token)
    nav.download_data()
    #nav.save_json("data.json")
    #nav.load_json("data.json")
    nav.serialize('nav_triples.ttl')

# TODO: Replace ns example with out own ontology in lift_data function
# TODO: things to find vocabs in add_vocab() for: workLocations, title, starttime, sector, published, occupationCategories, link, jobtitle, extent, expires, engagementtype, employer, description, applicationDue, homepage, name, orgnr, address, city, country, county, municipal, postalCode . try to have as many in the same vocabs as possible
