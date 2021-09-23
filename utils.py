import pickle
import pprint
pp = pprint.PrettyPrinter(indent=4)

with open('interlink_index.pkl' , "rb" ) as f:
    index_interlinks = pickle.load(f)

pp.pprint(repr(index_interlinks))

def convert_index_to_list : # convert double entry index to single entry type list of cpaths
    pass


#   FIGURE OUT WHICH LIBRARY TO USE FOR VISUALIZATION OF THE NETWORK
# https://www.google.com/search?q=how+to+visualize+networks+graphs+in+python&rlz=1C1CHBF_enIN923IN923&oq=how+to+visualize+networks+graphs++in+python&aqs=chrome..69i57.19242j0j1&sourceid=chrome&ie=UTF-8
# https://plotly.com/python/network-graphs/
# https://towardsdatascience.com/visualizing-networks-in-python-d70f4cbeb259
# https://towardsdatascience.com/python-interactive-network-visualization-using-networkx-plotly-and-dash-e44749161ed7
# https://programminghistorian.org/en/lessons/exploring-and-analyzing-network-data-with-python
# https://melaniewalsh.github.io/Intro-Cultural-Analytics/Network-Analysis/Making-Network-Viz-with-Bokeh.html





# move this to analysis_utilities.py
from heapq import nlargest

def get_n_most_linked_notes( n , interlink_counter_store = interlink_counter_store ):
    result = nlargest( n , interlink_counter_store, key = interlink_counter_store.get)
    return result

interlink_counter_store = note_interlink_counter_generate_dict(index_interlinks = index_interlinks)
