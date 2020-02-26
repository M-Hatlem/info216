import json
from rdflib import URIRef, Graph, Namespace, Literal


def lift_data():
    graph = Graph()
    nameSpace = Namespace("http://example.org/")
    with open("data.json", "r", encoding='utf-8') as json_file:
        nav_data = json.load(json_file)
        for job_ad in nav_data['content']:
            unique_key = job_ad['uuid']
            for graph_predicate in job_ad:
                if type(job_ad[graph_predicate]) is list:
                    graph.add( (nameSpace[unique_key], nameSpace[graph_predicate], nameSpace[unique_key + graph_predicate]) )
                    for dict_data_from_list in job_ad[graph_predicate]:
                        for elm_in_list in dict_data_from_list:
                            graph.add( (nameSpace[unique_key + graph_predicate], nameSpace[elm_in_list], Literal(dict_data_from_list[elm_in_list])) )
                elif type(job_ad[graph_predicate]) is dict:
                    graph.add( (nameSpace[unique_key], nameSpace[graph_predicate], nameSpace[unique_key + graph_predicate]) )
                    job_data_dict = job_ad[graph_predicate]
                    for dict_data_from_dict in job_data_dict:
                        graph.add( (nameSpace[unique_key], nameSpace[dict_data_from_dict], Literal(job_data_dict[dict_data_from_dict])) )
                else:
                    graph.add ((nameSpace[unique_key], nameSpace[graph_predicate], Literal(job_ad[graph_predicate])) )
            #To test run on only one ad remove # on #break
            #break
        print(graph.serialize(format='turtle'))
        graph.serialize(destination='output.txt', format='turtle')


if __name__ == "__main__":
    lift_data()

# TODO: clean html formatting from input