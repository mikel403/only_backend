from .descriptors import *
#latest_only=True: one vote per expert (their last description), used by the expert panel.
#latest_only=False: every description counts, used to show all the times a single expert described the nodule
def expertPanel_fn(descriptions, latest_only=True):
    statistics={descriptor:{} for descriptor in descriptors}
    physician_id=[]

    desc_final={}
    physician_list={}
    for description in descriptions:
        physician_id=description["user_id"]
        id=description["id"]
        if (physician_id not in physician_list) or (id>physician_list[physician_id]):
            desc_final[physician_id]=description
            physician_list[physician_id]=id

    selected=desc_final.values() if latest_only else descriptions
    for desc in selected:
        for key,carac in desc.items():
            if key in ["id","content_type_id","object_id","nodule_id","user_id"]:
                continue
            if carac:
                if carac in statistics[key]:
                    statistics[key][carac]+=1
                else:
                    statistics[key][carac]=1
    for descriptor, stats in statistics.items():
        total_descriptor=sum(list(statistics[descriptor].values()))
        for carac,value in stats.items():
            statistics[descriptor][carac]=value/total_descriptor
        statistics[descriptor]["total"]=total_descriptor
    return statistics
    