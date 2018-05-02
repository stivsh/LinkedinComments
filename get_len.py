import pickle
import os
basepath = os.path.dirname(__file__)
data_filepath = os.path.abspath(os.path.join(basepath, "data.pickle"))

with open(data_filepath,'rb') as f:
    elements = pickle.load(f)
print len(elements)
