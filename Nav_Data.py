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
        api_endpoint = 'https://arbeidsplassen.nav.no/public-feed/api/v1/ads?size=100'
        api_headers = {'accept': 'application/json',
                       'Authorization': 'Bearer ' + self.token}
        download = requests.get(url=api_endpoint, headers=api_headers)
        if download.status_code == 200:
            self.data = download.json()
            print("Download complete")  # TODO example print, change to display in GUI
            self.lift_data()
            return True
        elif download.status_code == 401:
            print("Error 401 not authorized, public token likely expired. Get a new one at: https://github.com/navikt/pam-public-feed")  # TODO example print, change to display in GUI
            return False
        else:
            print("Error: " + str(download.status_code))  # TODO example print, change to display in GUI
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
        ns = Namespace("http://example.org/")  # TODO example properties, remember to change, Replace ns example with out own ontology
        self.graph.bind("ex", ns)
        sch = Namespace("http://schema.org/")
        self.graph.bind("schema", sch)
        dbp = Namespace("http://dbpedia.org/ontology/")
        self.graph.bind("dbpedia-owl", dbp)
        for job_ad in self.data['content']:
            unique_key = job_ad['uuid']
            for graph_predicate in job_ad:
                if type(job_ad[graph_predicate]) is list:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(graph_predicate + "-uid:" + unique_key)))
                    for dict_data_from_list in job_ad[graph_predicate]:
                        for elm_in_list in dict_data_from_list:
                            if (elm_in_list == "country" or elm_in_list == "county" or elm_in_list == "city") and elm_in_list is not None:
                                self.graph.add((ns[graph_predicate + "-uid:" + unique_key], dbp[elm_in_list], ns[self.clean_text(dict_data_from_list[elm_in_list])]))
                            elif elm_in_list == "postalCode":
                                self.graph.add((ns[graph_predicate + "-uid:" + unique_key], dbp[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                            elif elm_in_list == "municipal":
                                self.graph.add((ns[graph_predicate + "-uid:" + unique_key], dbp["municipality"], ns[self.clean_text(dict_data_from_list[elm_in_list])]))
                            elif elm_in_list == "address":
                                self.graph.add((ns[graph_predicate + "-uid:" + unique_key], sch[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                            else:
                                self.graph.add((ns[graph_predicate + "-uid:" + unique_key], ns[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                elif type(job_ad[graph_predicate]) is dict:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(graph_predicate + "-uid:" + unique_key)))
                    job_data_dict = job_ad[graph_predicate]
                    for dict_data_from_dict in job_data_dict:
                        if dict_data_from_dict == "description" and job_data_dict[dict_data_from_dict] is not None:
                            self.graph.add((ns[graph_predicate + "-uid:" + unique_key], sch[dict_data_from_dict], Literal(self.clean_html_tags(job_data_dict[dict_data_from_dict]))))
                        elif dict_data_from_dict == "name" and job_ad[graph_predicate] is not None:
                            self.graph.add((ns[graph_predicate + "-uid:" + unique_key], sch[dict_data_from_dict], ns[self.clean_text(job_data_dict[dict_data_from_dict])]))
                        elif dict_data_from_dict == "homepage" and job_ad[graph_predicate] is not None:
                            self.graph.add((ns[graph_predicate + "-uid:" + unique_key], sch["url"], Literal(job_data_dict[dict_data_from_dict])))
                        elif dict_data_from_dict == "orgnr" and job_ad[graph_predicate] is not None:
                            self.graph.add((ns[graph_predicate + "-uid:" + unique_key], sch["identifier"], Literal(job_data_dict[dict_data_from_dict])))
                        else:
                            self.graph.add((ns[graph_predicate + "-uid:" + unique_key], ns[dict_data_from_dict], Literal(job_data_dict[dict_data_from_dict])))
                elif graph_predicate == "description" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch[graph_predicate], Literal(self.clean_html_tags(job_ad[graph_predicate]))))
                elif graph_predicate == "updated" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif (graph_predicate == "link" or graph_predicate == "sourceurl" or graph_predicate == "positioncount") and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate])))
                elif graph_predicate == "title" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch[graph_predicate], ns[self.clean_text(job_ad[graph_predicate])]))
                elif graph_predicate == "jobtitle" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch["jobTitle"], ns[self.clean_text(job_ad[graph_predicate])]))
                elif graph_predicate == "engagementtype" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch["employmentType"], ns[self.clean_text(job_ad[graph_predicate])]))
                elif graph_predicate == "expires" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch[graph_predicate], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "starttime" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch["jobStartDate"], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "applicationDue" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch["applicationDeadline"], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "published" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch["datePosted"], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "link" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch["relatedLink"], Literal(job_ad[graph_predicate])))
                elif type(job_ad[graph_predicate]) is str and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], ns[graph_predicate], ns[self.clean_text(job_ad[graph_predicate])]))
                else:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate])))
            #break  # To test run on only one ad remove # on #break

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

    # Runs allows us to run queries on the graph
    def query(self, statement):
        qres = self.graph.query(statement)
        for row in qres:
            print("%s has title %s" % row)   # TODO example print, change to display in GUI


if __name__ == "__main__":
    api_public_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwdWJsaWMudG9rZW4udjFAbmF2Lm5vIiwiYXVkIjoiZmVlZC1hcGktdjEiLCJpc3MiOiJuYXYubm8iLCJpYXQiOjE1NTc0NzM0MjJ9.jNGlLUF9HxoHo5JrQNMkweLj_91bgk97ZebLdfx3_UQ'
    example_query = """PREFIX ex:<http://example.org/> SELECT DISTINCT ?uuid ?title WHERE {?uuid ex:title ?title .}"""
    nav = NavData(api_public_token)
    #nav.update_token(api_public_token)
    nav.download_data()
    #nav.save_json("data.json")
    #nav.load_json("data.json")
    nav.serialize('nav_triples.ttl')
    #nav.load_serialized_data('nav_triples.ttl')
    nav.query(example_query)
    # TODO Create GUI with support for all functions
    # TODO Add Dbpedia integration for linking to info about cities/countries/etc.
    # TODO improve and expand query and filtering options
    # TODO add option to search on UIB's sv faculty study lines and get possible jobs for a student with x degree
