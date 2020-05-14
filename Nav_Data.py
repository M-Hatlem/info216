# requires request library, download at: pip install requests
# requires BeautifulSoup4, download at: pip install beautifulsoup4
# requires rdflib, download at: pip install rdflib
# requires jsonmerge, download at: pip install jsonmerge
# requires owlrl, download at: pip install owlrl
import requests
import webbrowser
import json
import re
import owlrl.RDFSClosure
from threading import Thread
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
        interface.status.set("Finished loading/downloading " + str(len(self.data['content'])) + " job ads \n lifting data please wait...:")
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
                            if elm_in_list == "country" or elm_in_list == "county" or elm_in_list == "city":
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], dbp[elm_in_list], ns[self.clean_text(dict_data_from_list[elm_in_list])]))
                            elif elm_in_list == "postalCode":
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], dbp[elm_in_list], Literal(dict_data_from_list[elm_in_list], datatype=XSD.zipcode)))
                            elif elm_in_list == "municipal":
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], dbp["municipality"], ns[self.clean_text(dict_data_from_list[elm_in_list])]))
                            elif elm_in_list == "address":
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                            else:
                                self.graph.add((ns[graph_predicate + "-uid-" + unique_key], ns[elm_in_list], Literal(dict_data_from_list[elm_in_list])))
                elif type(job_ad[graph_predicate]) is dict:
                    self.graph.add((ns[unique_key], ns[graph_predicate], ns[graph_predicate + "-uid-" + unique_key]))
                    job_data_dict = job_ad[graph_predicate]
                    for dict_data_from_dict in job_data_dict:
                        if dict_data_from_dict == "description":
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch[dict_data_from_dict], Literal(self.clean_html_tags(job_data_dict[dict_data_from_dict]))))
                        elif dict_data_from_dict == "name":
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch[dict_data_from_dict], ns[self.clean_text(job_data_dict[dict_data_from_dict])]))
                        elif dict_data_from_dict == "homepage":
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch["url"], Literal(job_data_dict[dict_data_from_dict], datatype=XSD.link)))
                        elif dict_data_from_dict == "orgnr":
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], sch["identifier"], Literal(job_data_dict[dict_data_from_dict])))
                        else:
                            self.graph.add((ns[graph_predicate + "-uid-" + unique_key], ns[dict_data_from_dict], Literal(job_data_dict[dict_data_from_dict])))
                elif graph_predicate == "description":
                    self.graph.add((ns[unique_key], sch[graph_predicate], Literal(self.clean_html_tags(job_ad[graph_predicate]))))
                elif graph_predicate == "updated":
                    self.graph.add((ns[unique_key], sch["dateModified"], Literal(job_ad[graph_predicate], datatype=XSD.datetime)))
                elif graph_predicate == "sourceurl":
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate], datatype=XSD.link)))
                elif graph_predicate == "title":
                    self.graph.add((ns[unique_key], sch[graph_predicate], ns[self.clean_text(job_ad[graph_predicate])]))
                elif graph_predicate == "jobtitle":
                    self.graph.add((ns[unique_key], sch["jobTitle"], ns[self.clean_text(job_ad[graph_predicate])]))
                elif graph_predicate == "engagementtype":
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
                elif graph_predicate == "positioncount":
                    self.graph.add((ns[unique_key], ns[graph_predicate], Literal(job_ad[graph_predicate], datatype=XSD.int)))
                else:
                    self.graph.add((ns[unique_key], ns[graph_predicate], ns[self.clean_text(job_ad[graph_predicate])]))
            # break  # Dev option to test run on only one ad remove # on #break
        interface.status.set("Lifting complete")
        interface.gui.update_idletasks()
        interface.query_mode()

    # This function removes html tags and new lines from the description of the ads
    @staticmethod
    def clean_html_tags(in_data):
        if in_data is None:
            return "None"
        soup = BeautifulSoup(in_data, 'html.parser')
        out_data = soup.get_text()
        out_data = out_data.replace("\r", "")
        out_data = out_data.replace("\n", "")
        return out_data

    # This function removes new lines, ' and " from the strings to make them URL friendly
    @staticmethod
    def clean_text(in_data):
        if in_data is None:
            return "None"
        in_data = re.sub(' ', '_', in_data)
        out_data = re.sub('[^A-Za-z0-9_æøåÆØÅ]+', '', in_data)
        return out_data

    # This function serializes the data to a turtle file and saves it locally. Requires a name to save as
    def serialize(self, filename):
        self.graph.serialize(destination=filename, format='turtle')

    # This function allows you to load a turtle file you previously serialized into the graph, requires the name of the file to load
    def load_serialized_data(self, filename):
        interface.status.set("Loading data please wait...")
        interface.gui.update_idletasks()
        self.graph.parse(filename, format="turtle")
        interface.query_mode()


# This class controls the GUI and everything displayed to the user
class TKinterGui:
    # This sets up the essentials of the GUI and adds functionality to the context menu
    def __init__(self):
        self.q_mode_active = False
        self.gui = tkinter.Tk()
        self.gui.title('Semantic job-searcher')
        self.gui.geometry("800x500")
        self.results = None
        menu = tkinter.Menu(self.gui)
        self.gui.config(menu=menu)
        download_thread = Thread(target=nav.download_data)
        load_json_thread = Thread(target=nav.load_json, args=("data.json",))
        save_json_thread = Thread(target=nav.save_json, args=("data.json",))
        load_ttl_thread = Thread(target=nav.load_serialized_data, args=('nav_triples.ttl',))
        save_ttl_thread = Thread(target=nav.serialize, args=('nav_triples.ttl',))
        importmenu = tkinter.Menu(self.gui)
        menu.add_cascade(label="Import file", menu=importmenu)
        importmenu.add_command(label='Import JSON file', command=lambda: [download_btn.place_forget(),  load_json_thread.start()])
        importmenu.add_command(label='Import Turtle file', command=lambda: [download_btn.place_forget(), load_ttl_thread.start()])
        savemenu = tkinter.Menu(self.gui)
        menu.add_cascade(label="Save data", menu=savemenu)
        savemenu.add_command(label='Save JSON file', command=lambda: save_json_thread.start())
        savemenu.add_command(label='Save Turtle file', command=lambda: save_ttl_thread.start())
        settingsmenu = tkinter.Menu(self.gui)
        menu.add_cascade(label="Settings", menu=settingsmenu)
        settingsmenu.add_command(label='Update token', command=self.update_token)
        settingsmenu.add_command(label='Re-download data', command=nav.download_data)
        self.status = tkinter.StringVar()
        tkinter.Label(self.gui, textvariable=self.status).place(relx=.5, rely=.3, anchor="center")
        download_btn = tkinter.Button(text='Download data sets', command=lambda: [download_btn.place_forget(), download_thread.start()])
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
            self.clear_results()
        else:
            self.q_mode_active = True
            tkinter.Label(self.gui, text="Search:").pack()
            search_fld = tkinter.Entry(self.gui, width=50)
            search_fld.pack()
            selected = {"article title": tkinter.BooleanVar(value=True), "start date": tkinter.BooleanVar(), "published": tkinter.BooleanVar(), "expires": tkinter.BooleanVar(), "last updated": tkinter.BooleanVar(), "application due": tkinter.BooleanVar(), "sector": tkinter.BooleanVar(), "extent": tkinter.BooleanVar(), "available positions": tkinter.BooleanVar(), "employer name": tkinter.BooleanVar(), "employer homepage": tkinter.BooleanVar(), "country": tkinter.BooleanVar(), "address": tkinter.BooleanVar(), "city": tkinter.BooleanVar(value=True), "county": tkinter.BooleanVar(), "municipal": tkinter.BooleanVar()}
            job_search_btn = tkinter.Button(text='Search for job', command=lambda: find.setup_query(nav.clean_text(search_fld.get()), False, selected))
            job_search_btn.pack()
            course_search_btn = tkinter.Button(text='Search for course', command=lambda: find.setup_query(nav.clean_text(search_fld.get()), True, selected))
            course_search_btn.pack()
            select_frame = tkinter.Frame(self.gui)
            sel_grid_row = 0
            sel_grid_col = 0
            for button in selected.keys():
                tkinter.Checkbutton(select_frame, text=button, variable=selected[button]).grid(row=sel_grid_row, column=sel_grid_col)
                sel_grid_col += 1
                if sel_grid_col == 8:
                    sel_grid_row += 1
                    sel_grid_col = 0
            select_frame.pack()
            container = tkinter.Frame(self.gui)
            canvas = tkinter.Canvas(container, width=770)
            yscrollbar = tkinter.Scrollbar(container, orient="vertical", command=canvas.yview)
            xscrollbar = tkinter.Scrollbar(container, orient="horizontal", command=canvas.xview)
            self.results = tkinter.Frame(canvas)
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.create_window((0, 0), window=self.results, anchor="nw")
            container.pack()
            xscrollbar.pack(side="bottom", fill="x")
            canvas.pack(side="left", expand=True)
            yscrollbar.pack(side="right", fill="y")

    # Removes the old results when searching for something new
    def clear_results(self):
        for label in self.results.winfo_children():
            label.destroy()
        interface.gui.update_idletasks()


# This class deals with the SPARQL queries
class Search:

    # Runs queries on the graph
    @staticmethod
    def query(statement, selected):
        splitter = ""
        result_col = 0
        result_row = 0
        for item in selected:
            splitter = splitter + "%s\t"
            tkinter.Label(interface.results, text=item, relief="solid", bg="gainsboro").grid(row=result_row, column=result_col, padx=2, sticky="WE")
            result_col += 1
        result_row += 1
        for row in nav.graph.query(statement):
            result_col = 0
            res_txt = splitter % row
            for col in res_txt.split("\t"):
                col = col.replace("https://github.com/M-Hatlem/info216/blob/master/Ontology/NavOntologyDefinition.txt#",
                                  "")
                col = col.replace("_", " ")
                if col == "":
                    pass
                elif result_col == selected.index("link"):
                    tkinter.Button(interface.results, text="Apply here!", command=lambda col=col: webbrowser.open(col, new=2)).grid(row=result_row, column=result_col, padx=2, sticky="WE")
                else:
                    tkinter.Label(interface.results, text=col, relief="groove").grid(row=result_row, column=result_col, padx=2, sticky="WE")
                result_col += 1
            result_row += 1
        interface.gui.update_idletasks()

    # Sets up a query depending on what a user is looking for
    def setup_query(self, searchword, course, findings):
        interface.clear_results()
        included = []
        if course is True:
            select = "SELECT DISTINCT ?jobtitle"
            query = " WHERE { ?jobtitle ex:relatedCourse ex:" + searchword + " . ?job schema:jobTitle ?jobtitle . ?job ex:workLocations ?loc . ?job ex:employer ?emp ."
            included.append("job title")
        else:
            select = "SELECT DISTINCT ?jobtitle"
            query = " ?job schema:jobTitle ?jobtitle . ?job ex:workLocations ?loc . ?job ex:employer ?emp ."
            included.append("job title")
        if findings["article title"].get() is True:
            select = select + " ?articletitle"
            query = query + " ?job schema:title ?articletitle ."
            included.append("article title")
        if findings["start date"].get() is True:
            select = select + " ?startdate"
            query = query + " ?job schema:jobStartDate ?startdate ."
            included.append("start date")
        if findings["published"].get() is True:
            select = select + " ?published"
            query = query + " ?job schema:datePosted ?published ."
            included.append("published")
        if findings["expires"].get() is True:
            select = select + " ?expires"
            query = query + " ?job schema:expires ?expires ."
            included.append("expires")
        if findings["last updated"].get() is True:
            select = select + " ?lastupdated"
            query = query + " ?job schema:dateModified ?lastupdated ."
            included.append("last updated")
        if findings["application due"].get() is True:
            select = select + " ?applicationdue"
            query = query + " ?job schema:applicationDeadline ?applicationdue ."
            included.append("application due")
        if findings["sector"].get() is True:
            select = select + " ?sector"
            query = query + " ?job ex:sector ?sector ."
            included.append("sector")
        if findings["extent"].get() is True:
            select = select + " ?extent"
            query = query + " ?job ex:extent ?extent ."
            included.append("extent")
        if findings["available positions"].get() is True:
            select = select + " ?availablepositions"
            query = query + " ?job ex:positioncount ?availablepositions ."
            included.append("available positions")
        if findings["employer name"].get() is True:
            select = select + " ?employername"
            query = query + " ?emp  schema:name ?employername ."
            included.append("employer name")
        if findings["employer homepage"].get() is True:
            select = select + " ?employerhomepage"
            query = query + " ?emp  schema:url ?employerhomepage ."
            included.append("employer homepage")
        if findings["country"].get() is True:
            select = select + " ?country"
            query = query + " ?loc  dbpedia-owl:country ?country ."
            included.append("country")
        if findings["address"].get() is True:
            select = select + " ?address"
            query = query + " ?loc  schema:address ?address ."
            included.append("address")
        if findings["city"].get() is True:
            select = select + " ?city"
            query = query + " ?loc dbpedia-owl:city ?city ."
            included.append("city")
        if findings["county"].get() is True:
            select = select + " ?county"
            query = query + " ?loc dbpedia-owl:county ?county ."
            included.append("county")
        if findings["municipal"].get() is True:
            select = select + " ?municipal"
            query = query + " ?loc dbpedia-owl:municipality ?municipal ."
            included.append("municipal")
        select = select + " ?link"
        query = query + " ?job schema:relatedLink ?link ."
        included.append("link")
        if course is True:
            self.query(select + query + " }", included)
        else:
            self.query(select + " WHERE { {ex:" + searchword + " skos:narrowerTransitive* ?jobtitle . " + query + " } UNION { ?altlable skos:altLable ex:" + searchword + " . ?altlable skos:narrowerTransitive* ?jobtitle ." + query + " } }",  included)


if __name__ == "__main__":
    api_public_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJwdWJsaWMudG9rZW4udjFAbmF2Lm5vIiwiYXVkIjoiZmVlZC1hcGktdjEiLCJpc3MiOiJuYXYubm8iLCJpYXQiOjE1NTc0NzM0MjJ9.jNGlLUF9HxoHo5JrQNMkweLj_91bgk97ZebLdfx3_UQ'
    nav = NavData(api_public_token)
    find = Search()
    interface = TKinterGui()
    interface.gui.mainloop()
