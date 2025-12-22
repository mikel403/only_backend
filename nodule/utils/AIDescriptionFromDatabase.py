import pandas as pd
import os
from django.conf import settings

model_path = os.path.join(settings.MEDIA_ROOT, 'ai_descriptions', 'desc_manuela_probs.csv')
# model_path = os.path.join("media", 'ai_descriptions', 'desc_manuela_probs.csv')
database=pd.read_csv(model_path,header=0,index_col=0)
database.index=[index.replace for index in database.index]
del database["birads"]
# database=database.to_dict(orient='records')
def isInDatabase(nodule):
    if nodule in database.index:
        return True
    return False

import ast

def probs_database(nodule):
    nodule_data=database.loc[nodule].to_dict()
    for key, diccionary in nodule_data.items():
        nodule_data[key]=ast.literal_eval(diccionary)
    return nodule_data