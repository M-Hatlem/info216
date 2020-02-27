import json, re
from rdflib import URIRef, Graph, Namespace, Literal

# This function lifts the data downloaded from nav into rdf triples
def lift_data():
    graph = Graph()
    nameSpace = Namespace("http://example.org/")
    graph.bind("ex", nameSpace)
    with open("data.json", "r", encoding='utf-8') as json_file:
        nav_data = json.load(json_file)
        for job_ad in nav_data['content']:
            unique_key = job_ad['uuid']
            for graph_predicate in job_ad:
                if type(job_ad[graph_predicate]) is list:
                    graph.add( (nameSpace[unique_key], nameSpace[graph_predicate], nameSpace[graph_predicate + "-unique_key-" + unique_key]) )
                    for dict_data_from_list in job_ad[graph_predicate]:
                        for elm_in_list in dict_data_from_list:
                            graph.add( (nameSpace[graph_predicate + "-unique_key-" + unique_key], nameSpace[elm_in_list], Literal(dict_data_from_list[elm_in_list])) )
                elif type(job_ad[graph_predicate]) is dict:
                    graph.add( (nameSpace[unique_key], nameSpace[graph_predicate], nameSpace[graph_predicate + "-unique_key-" + unique_key]) )
                    job_data_dict = job_ad[graph_predicate]
                    for dict_data_from_dict in job_data_dict:
                        graph.add( (nameSpace[unique_key], nameSpace[dict_data_from_dict], Literal(job_data_dict[dict_data_from_dict])) )
                elif graph_predicate == "description":
                    graph.add((nameSpace[unique_key], nameSpace[graph_predicate], Literal(clean_html_tag(job_ad[graph_predicate]))) )
                elif type(job_ad[graph_predicate]) is str:
                    graph.add((nameSpace[unique_key], nameSpace[graph_predicate], nameSpace[clean_spaces(job_ad[graph_predicate])]) )
                else:
                    graph.add ((nameSpace[unique_key], nameSpace[graph_predicate], Literal(job_ad[graph_predicate])) )
            #To test run on only one ad remove # on #break
            #break
        graph.serialize(destination='output.txt', format='turtle')

# This function removes html tags from the description of the ads
def clean_html_tag(in_data):
    cleaner = re.compile('<.*?>')
    in_data = re.sub(cleaner, '', in_data)
    out_data = re.sub('\n', '', in_data)
    return out_data

def clean_spaces(in_data):
    out_data = re.sub(' ', '_', in_data)
    return out_data


if __name__ == "__main__":
    lift_data()

# TODO: clean html line gaps from input with regexp in function

# TODO: Replace example with out own ontology

# TODO: create a fucntion that imports replaces ex in schema and other vocab properties in the fniished file
