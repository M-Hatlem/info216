# requires request library, download at: pip install requests
# requires BeautifulSoup4, download at: pip install beautifulsoup4
# requires rdflib, download at: pip install rdflib
# requires jsonmerge, download at: pip install jsonmerge
# requires owlrl, download at: pip install owlrl
import requests
import json
import re
import owlrl.RDFSClosure
from jsonmerge import Merger
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import XSD
from bs4 import BeautifulSoup
import tkinter


# This class handles all the data and functionality related to it such as downloading it, semnatically annotating and lifting it as well as allowing us to run queries
class NavData:
    def __init__(self, token):
        self.token = token
        self.graph = Graph()
        self.data = None
        owl = owlrl.CombinedClosure.RDFS_OWLRL_Semantics(self.graph, False, False, False)
        owl.closure()
        owl.flush_stored_triples()
        self.graph.parse("NavBaseOnt.ttl", format="turtle")

    # allows you to update Nav's download token in case it's expired or has been changed
    def update_token(self, new_token):
        self.token = new_token

    # This function downloads the data set from Nav, it requires a token as an input
    def download_data(self):
        counter = 0
        interface.status.set("Downloading data please wait..." + " \n Data sets downloaded: " + str(counter))
        interface.gui.update_idletasks()
        api_endpoint = 'https://arbeidsplassen.nav.no/public-feed/api/v1/ads?size=100'
        api_headers = {'accept': 'application/json', 'Authorization': 'Bearer ' + self.token}
        merg_schema = {"properties": {"content": {"mergeStrategy": "append"}}}
        merger = Merger(merg_schema)
        download = requests.get(url=api_endpoint, headers=api_headers)
        if download.status_code == 200:
            self.data = download.json()
            download_active = True
            while download_active is True:
                latest_download = (self.data['content'][len(self.data['content']) - 1]['published'])[0:19]
                download = requests.get(url=api_endpoint + "&published=[*," + latest_download + ")", headers=api_headers)
                counter += 1
                interface.status.set("Downloading data please wait..." + " \n Data sets downloaded: " + str(counter) + " \n Total job ads fetched: " + str(len(self.data['content'])))
                interface.gui.update_idletasks()
                self.data = merger.merge(self.data, download.json())
                # if counter == 2:   # Dev option to not download all ads, but instead a limited number, makes for faster testing. remove the # on this and the line bellow to use
                #    download_active = False
                if latest_download == (self.data['content'][len(self.data['content']) - 1]['published'])[0:19]:
                    download_active = False
            self.lift_data()
        elif download.status_code == 401:
            interface.status.set("Error 401 not authorized, public token likely expired \n go to settings --> 'update Token' and input a new one, then press Re-download in the settings menu to update. \n Get a new token at: https://github.com/navikt/pam-public-feed")
        else:
            interface.status.set(" http error: " + str(download.status_code) + "\n program failed try again")

    # if you want to save the json data downloaded, do this after a download, requires filename as input:
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
        interface.status.set("Download complete, lifting data please wait...:")
        interface.gui.update_idletasks()
        ns = Namespace("https://github.com/M-Hatlem/info216/blob/master/Ontology/NavOntologyDefinition.txt#")
        self.graph.bind("ex", ns)
        sch = Namespace("http://schema.org/")
        self.graph.bind("schema", sch)
        dbp = Namespace("http://dbpedia.org/ontology/")
        self.graph.bind("dbpedia-owl", dbp)
        for job_ad in self.data['content']:
            unique_key = job_ad['uuid']
            for graph_predicate in job_ad:
                if type(job_ad[graph_predicate]) is list:
                    self.graph.add((ns[unique_key], ns[graph_predicate], ns[graph_predicate + "-uid-" + unique_key]))
                    for dict_data_from_list in job_ad[graph_predicate]:
                        for elm_in_list in dict_data_from_list:
                            if (elm_in_list == "country" or elm_in_list == "county" or elm_in_list == "city") and dict_data_from_list[elm_in_list] is not None:
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], dbp[elm_in_list], ns[self.clean_text(dict_data_from_list[elm_in_list])]))
                            elif elm_in_list == "postalCode":
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], dbp[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                            elif elm_in_list == "municipal" and dict_data_from_list[elm_in_list] is not None:
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], dbp["municipality"], ns[self.clean_text(dict_data_from_list[elm_in_list])]))
                            elif elm_in_list == "address":
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                            else:
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], ns[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                elif type(job_ad[graph_predicate]) is dict:
                    self.graph.add((ns[unique_key], ns[graph_predicate], ns[graph_predicate + "-uid-" + unique_key]))
                    job_data_dict = job_ad[graph_predicate]
                    for dict_data_from_dict in job_data_dict:
                        if dict_data_from_dict == "description" and job_data_dict[dict_data_from_dict] is not None:
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch[dict_data_from_dict], Literal(self.clean_html_tags(job_data_dict[dict_data_from_dict]))))
                        elif dict_data_from_dict == "name" and job_data_dict[dict_data_from_dict] is not None:
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch[dict_data_from_dict], ns[self.clean_text(job_data_dict[dict_data_from_dict])]))
                        elif dict_data_from_dict == "homepage":
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch["url"], Literal(job_data_dict[dict_data_from_dict], datatype=XSD.link)))
                        elif dict_data_from_dict == "orgnr":
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch["identifier"], Literal(job_data_dict[dict_data_from_dict])))
                        else:
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], ns[dict_data_from_dict], Literal(job_data_dict[dict_data_from_dict])))
                elif graph_predicate == "description" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch[graph_predicate], Literal(self.clean_html_tags(job_ad[graph_predicate]))))
                elif graph_predicate == "updated":
                    self.graph.add((ns[unique_key], sch["dateModified"], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "sourceurl":
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate], datatype=XSD.link)))
                elif graph_predicate == "title" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch[graph_predicate], ns[self.clean_text(job_ad[graph_predicate])]))
                elif graph_predicate == "jobtitle" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch["jobTitle"], ns[self.clean_text(job_ad[graph_predicate])]))
                elif graph_predicate == "engagementtype" and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], sch["employmentType"], ns[self.clean_text(job_ad[graph_predicate])]))
                elif graph_predicate == "expires":
                    self.graph.add((ns[unique_key], sch[graph_predicate], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "starttime":
                    self.graph.add((ns[unique_key], sch["jobStartDate"], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "applicationDue":
                    self.graph.add((ns[unique_key], sch["applicationDeadline"], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "published":
                    self.graph.add((ns[unique_key], sch["datePosted"], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "link":
                    self.graph.add((ns[unique_key], sch["relatedLink"], Literal(job_ad[graph_predicate], datatype=XSD.link)))
                elif type(job_ad[graph_predicate]) is str and job_ad[graph_predicate] is not None:
                    self.graph.add((ns[unique_key], ns[graph_predicate], ns[self.clean_text(job_ad[graph_predicate])]))
                else:
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate])))
            # break  # Dev option to test run on only one ad remove # on #break
        interface.status.set("Lifting complete")
        interface.gui.update_idletasks()
        interface.query_mode()

    # This function removes html tags and new lines from the description of the ads
    @staticmethod
    def clean_html_tags(in_data):
        soup = BeautifulSoup(in_data, 'html.parser')
        out_data = soup.get_text()
        out_data = out_data.replace("\r", "")
        out_data = out_data.replace("\n", "")
        return out_data

    # This function removes new lines, ' and " from the strings to make them URL friendly
    @staticmethod
    def clean_text(in_data):
        in_data = re.sub(' ', '_', in_data)
        out_data = re.sub('[^A-Za-z0-9_æøåÆØÅ]+', '', in_data)
        return out_data

    # This function serializes the data to a turtle file and saves it locally. Requires a name to save as
    def serialize(self, filename):
        self.graph.serialize(destination=filename, format='turtle')

    # This function allows you to load a turtle file you previously serialized into the graph, requires the name of the file to load
    def load_serialized_data(self, filename):
        self.graph.parse(filename, format="turtle")
        interface.query_mode()

    # Runs queries on the graph
    def query(self, statement):
        query_res = self.graph.query(statement)
        q_res_txt = ""
        for row in query_res:
            q_res_txt = q_res_txt + "%s %s %s" % row + "\n"
        q_res_txt = q_res_txt.replace("https://github.com/M-Hatlem/info216/blob/master/Ontology/NavOntologyDefinition.txt#", "")
        q_res_txt = q_res_txt.replace("_", " ")
        interface.result_text.set(q_res_txt)
        interface.gui.update_idletasks()


# This class controls the GUI and everything displayed to the user
class TKinterGui:
    # This sets up the essentials of the GUI and adds functionality to the context menu
    def __init__(self):
        self.q_mode_active = False
        self.gui = tkinter.Tk()
        self.gui.title('Semantic job-searcher')
        self.gui.geometry("800x500")
        self.result_text = tkinter.StringVar()
        self.result = tkinter.Label(self.gui, textvariable=self.result_text, justify='left')
        menu = tkinter.Menu(self.gui)
        self.gui.config(menu=menu)
        importmenu = tkinter.Menu(self.gui)
        menu.add_cascade(label="Import file", menu=importmenu)
        importmenu.add_command(label='Import JSON file', command=lambda: nav.load_json("data.json"))
        importmenu.add_command(label='Import Turtle file', command=lambda: nav.load_serialized_data('nav_triples.ttl'))
        savemenu = tkinter.Menu(self.gui)
        menu.add_cascade(label="Save data", menu=savemenu)
        savemenu.add_command(label='Save JSON file', command=lambda: nav.save_json("data.json"))
        savemenu.add_command(label='Save Turtle file', command=lambda: nav.serialize('nav_triples.ttl'))
        settingsmenu = tkinter.Menu(self.gui)
        menu.add_cascade(label="Settings", menu=settingsmenu)
        settingsmenu.add_command(label='Update token', command=self.update_token)
        settingsmenu.add_command(label='Re-download data', command=nav.download_data)
        self.status = tkinter.StringVar()
        tkinter.Label(self.gui, textvariable=self.status).place(relx=.5, rely=.3, anchor="center")
        download_btn = tkinter.Button(text='Download data sets', command=lambda: [download_btn.place_forget(), nav.download_data()])
        download_btn.place(relx=.5, rely=.5, anchor="center")

    # Opens the page for updating your token, this can only be done if you have't entered query mode already as you already need valid data to do so. Will already show the latest token used by us, but can be changed
    def update_token(self):
        if self.q_mode_active is False:
            self.status.set("Public token:")
            input_token_fld = tkinter.Entry(self.gui, width=100)
            input_token_fld.place(relx=.5, rely=.3, anchor="center")
            input_token_fld.insert(0, api_public_token)
            input_token_btn = tkinter.Button(text='Set token', command=lambda: [self.status.set(""), input_token_fld.place_forget(), input_token_btn.place_forget(),  nav.update_token(input_token_fld.get())])
            input_token_btn.place(relx=.5, rely=.4, anchor="center")

    # This function allows the users to run queries and sets up the GUI accordingly
    def query_mode(self):
        self.status.set("")
        interface.gui.update_idletasks()
        if self.q_mode_active is True:
            self.result.destroy()
            self.result_text = ""
        else:
            self.q_mode_active = True
            tkinter.Label(self.gui, text="Search:").pack()
            search_fld = tkinter.Entry(self.gui, width=50)
            search_fld.pack()
            search_btn = tkinter.Button(text='Search', command=lambda: nav.query("SELECT ?articletitle ?jobtitle ?city WHERE { ex:" + nav.clean_text(search_fld.get()) + " skos:narrowerTransitive* ?jobtitle . ?job schema:jobTitle ?jobtitle . ?job schema:title ?articletitle . ?job ex:workLocations ?loc . ?loc dbpedia-owl:city ?city }"))
            search_btn.pack()
        container = tkinter.Frame(self.gui)
        canvas = tkinter.Canvas(container)
        scrollbar = tkinter.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tkinter.Frame(canvas)
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        container.pack()
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.result = tkinter.Label(scrollable_frame, textvariable=self.result_text,  justify='left')
        self.result.pack()


if __name__ == "__main__":
    api_public_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwdWJsaWMudG9rZW4udjFAbmF2Lm5vIiwiYXVkIjoiZmVlZC1hcGktdjEiLCJpc3MiOiJuYXYubm8iLCJpYXQiOjE1NTc0NzM0MjJ9.jNGlLUF9HxoHo5JrQNMkweLj_91bgk97ZebLdfx3_UQ'
    nav = NavData(api_public_token)
    interface = TKinterGui()
    interface.gui.mainloop()
    # TODO Add Dbpedia integration for linking to info about cities/countries/etc.
    # TODO add option to search on UIB's sv faculty study lines and get possible jobs for a student with x degree
