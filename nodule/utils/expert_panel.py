from .descriptors import *
def expertPanel_fn(descriptions):
    statistics={descriptor:{} for descriptor in descriptors}
    physicist_id=[]

    desc_final={}
    physicist_list={}
    for description in descriptions:
        print(description)
        physicist_id=description["object_id"]
        id=description["id"]
        if (physicist_id not in physicist_list) or (id>physicist_list[physicist_id]):
            desc_final[physicist_id]=description
            physicist_list[physicist_id]=id


    for physicist_id,desc in desc_final.items():
        for key,carac in desc.items():
            if key in ["id","content_type_id","object_id","nodule_id"]:
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
    