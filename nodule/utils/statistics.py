from .descriptors import *

# def statistics_fn(descriptions):
#     statistics={}
#     for desc, caracs in descriptors.items():
#         statistics[desc]={}
#         caracs.append("total")
#         for carac in caracs:
#             statistics[desc][carac]=0

#     for description in descriptions:
#         for descriptor, carac in description.items():
#             if descriptor in statistics:
#                 if carac in statistics[descriptor]:
#                     statistics[descriptor][carac]+=1
#                     statistics[descriptor]["total"]+=1
#     return statistics

def statistics_fn(descriptions):
    statistics={}
    statistics_birads={}
    for descriptor, caracs in descriptors.items():
        statistics[descriptor]={}
        statistics_birads[descriptor]={}
        for carac in caracs:
            statistics[descriptor][carac]={bir:0 for bir in birads}
            statistics[descriptor][carac]["total"]=0
            statistics_birads[descriptor]={bir:0 for bir in birads}


    

        

    for description in descriptions:
        for descriptor, carac in description.items():
            
            if descriptor in statistics:
                if carac in statistics[descriptor]:
                    if description["birads"] in birads:
                        statistics_birads[descriptor][description["birads"]]+=1
        
                        statistics[descriptor][carac][description["birads"]]+=1
                        statistics[descriptor][carac]["total"]+=1
    
    return {"statistics":statistics,"statistics_birads":statistics_birads}