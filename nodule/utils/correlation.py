from collections import defaultdict

from .descriptors import *

def intercorrelation_fn(desc,desc_other):
    nodules_list={}
    desc_final={}
    for description in desc:
        
        nodule_id=description["nodule_id"]
        id=description["id"]
        if (nodule_id not in nodules_list) or (id>nodules_list[nodule_id]):
            desc_final[nodule_id]=description
            nodules_list[nodule_id]=id

    nodules_list_other={}
    desc_final_other={}
    for description in desc_other:
        nodule_id=description["nodule_id"]
        id=description["id"]
        if (nodule_id not in nodules_list_other) or (id>nodules_list_other[nodule_id]):
            desc_final_other[nodule_id]=description
            nodules_list_other[nodule_id]=id
    desc_final_={}
    for nodule_id,desc in desc_final.items():
        if nodule_id in desc_final_other:
            desc_final_[nodule_id]=desc
    desc_final_other_={}
    for nodule_id,desc in desc_final_other.items():
        if nodule_id in desc_final:
            desc_final_other_[nodule_id]=desc

    return kappa(desc_final_,desc_final_other_)

def intracorrelation_fn(desc):
#Creamos una lista que tiene todas las descripciones y otra lista que tan solo va a tener la descripciones de los nódulos que hayan sido descritos dos veces o más.

    nodules_list={}
    desc_total={}
    
    desc_doble={}
    for description in desc:
        nodule_id=description["nodule_id"]
        id=description["id"]
        if nodule_id not in nodules_list:
            desc_total[nodule_id]={id:description}
            nodules_list[nodule_id]=[id]
        else:
            desc_total[nodule_id][id]=description
            total_times_described=len(desc_total[nodule_id])
            if total_times_described==2:
                desc_doble[nodule_id]=desc_total[nodule_id]
            else:
                id_list=list(desc_doble[nodule_id].keys())
                id_list.append(id)
                min_id= min(id_list)
                if min_id!=id:
                    desc_doble[nodule_id].pop(min_id)
                    desc_doble[nodule_id][id]=description
    desc_final={}
    desc_previo={}
    for nodule_id,descs in desc_doble.items():
        id_order=list(descs.keys())
        id_order.sort
        desc_previo[nodule_id]=descs[id_order[0]]
        desc_final[nodule_id]=descs[id_order[1]]
    return kappa(desc_final,desc_previo)


def check_carac(y,carac):
    if carac in shape:
        lista=shape
    elif carac in margin:
        lista=margin
    elif carac in echogenicity:
        lista=echogenicity
    elif carac in orientation:
        lista=orientation
    elif carac in posterior:
        lista=posterior
    # elif carac in halo:
    #     lista=halo
    elif carac in calcification:
        lista=calcification
    elif carac in suggestivity:
        lista=suggestivity
    elif carac in birads:
        lista=birads
    else:
        return(False)
    for caract in y:
        if caract in lista:
            return True
    return False

def zero_div(a,b):
    if b==0:
        return 0
    else:
        return a/b
def elememtwise_mul(a,b):
    return [c*d for (c,d) in zip(a,b)] 

def elementwise_sum(list1,list2):
    return [sum(x) for x in zip(list1, list2)]

def list_div(lis,n):
    return [zero_div(l,n) for l in lis]
def kappa(y:dict,y_hat:dict,no_birads=False):
    shape_acc,margin_acc,echogenicity_acc,orientation_acc,posterior_acc,calcification_acc, suggestivity_acc, birads_acc=0,0,0,0,0,0,0,0
    num_shape, num_margin, num_echogenicity, num_orientation, num_posterior, num_calcification,  num_suggestivity, num_birads=0,0,0,0,0,0,0,0
    num_type_shape, num_type_margin, num_type_echogenicity, num_type_orientation, num_type_posterior,num_type_calcification, num_type_suggestivity, num_type_birads=[0]*len(shape),[0]*len(margin),[0]*len(echogenicity),[0]*len(orientation),[0]*len(posterior),[0]*len(calcification),[0]*len(suggestivity),[0]*len(birads)
    num_type_shape_h, num_type_margin_h, num_type_echogenicity_h, num_type_orientation_h, num_type_posterior_h,num_type_calcification_h, num_type_suggestivity_h, num_type_birads_h=[0]*len(shape),[0]*len(margin),[0]*len(echogenicity),[0]*len(orientation),[0]*len(posterior),[0]*len(calcification),[0]*len(suggestivity),[0]*len(birads)
    for key, desc in y.items():
        desc=list(filter(None,list(desc.values())))
        desc_other=list(filter(None,list(y_hat[key].values())))
        for carac in desc:
            if check_carac(desc_other,carac):
                if carac in shape:
                    num_shape+=1
                    num_type_shape[word_to_idx_shape[carac]]=num_type_shape[word_to_idx_shape[carac]]+1
                elif carac in margin:
                    num_margin+=1
                    num_type_margin[word_to_idx_margin[carac]]=num_type_margin[word_to_idx_margin[carac]]+1
                elif carac in echogenicity:
                    num_echogenicity+=1
                    num_type_echogenicity[word_to_idx_echogenicity[carac]]=num_type_echogenicity[word_to_idx_echogenicity[carac]]+1
                elif carac in orientation:
                    num_orientation+=1
                    num_type_orientation[word_to_idx_orientation[carac]]=num_type_orientation[word_to_idx_orientation[carac]]+1
                elif carac in posterior:
                    num_posterior+=1
                    num_type_posterior[word_to_idx_posterior[carac]]=num_type_posterior[word_to_idx_posterior[carac]]+1
                # elif carac in halo:
                #     num_halo+=1
                #     num_type_halo[word_to_idx_halo[carac]]=num_type_halo[word_to_idx_halo[carac]]+1
                elif carac in calcification:
                    num_calcification+=1
                    num_type_calcification[word_to_idx_calcification[carac]]=num_type_calcification[word_to_idx_calcification[carac]]+1
                elif carac in suggestivity:
                    num_suggestivity+=1
                    num_type_suggestivity[word_to_idx_suggestivity[carac]]=num_type_suggestivity[word_to_idx_suggestivity[carac]]+1
                
                elif carac in birads:
                    num_birads+=1
                    num_type_birads[word_to_idx_birads[carac]]=num_type_birads[word_to_idx_birads[carac]]+1
                    if carac in desc_other:
                        birads_acc+=1
                if carac in desc_other:
                    if carac in shape:
                        shape_acc+=1
                    elif carac in margin:
                        margin_acc+=1
                    elif carac in echogenicity:
                        echogenicity_acc+=1
                    elif carac in orientation:
                        orientation_acc+=1
                    elif carac in posterior:
                        posterior_acc+=1
                    # elif carac in halo:
                    #     halo_acc+=1
                    elif carac in calcification:
                        calcification_acc+=1
                    elif carac in suggestivity:
                        suggestivity_acc+=1
                    
                
    for key, desc in y_hat.items():
        desc=list(filter(None,list(desc.values())))
        desc_other=list(filter(None,list(y[key].values())))
        bool_f,bool_m,bool_e,bool_o,bool_p,bool_s,bool_b=False,False,False,False,False,False,False
        for carac in desc:
            if check_carac(desc_other,carac):
                if carac in shape and not bool_f:
                    bool_f=True
                    num_type_shape_h[word_to_idx_shape[carac]]=num_type_shape_h[word_to_idx_shape[carac]]+1
                elif carac in margin and not bool_m:
                    bool_m=True
                    num_type_margin_h[word_to_idx_margin[carac]]=num_type_margin_h[word_to_idx_margin[carac]]+1
                elif carac in echogenicity and not bool_e:
                    bool_e=True
                    num_type_echogenicity_h[word_to_idx_echogenicity[carac]]=num_type_echogenicity_h[word_to_idx_echogenicity[carac]]+1
                elif carac in orientation and not bool_o:
                    bool_o=True
                    num_type_orientation_h[word_to_idx_orientation[carac]]=num_type_orientation_h[word_to_idx_orientation[carac]]+1
                elif carac in posterior and not bool_p:
                    bool_p=True
                    num_type_posterior_h[word_to_idx_posterior[carac]]=num_type_posterior_h[word_to_idx_posterior[carac]]+1
                # elif carac in halo and not bool_h:
                #     bool_h=True
                #     num_type_halo_h[word_to_idx_halo[carac]]=num_type_halo_h[word_to_idx_halo[carac]]+1
                elif carac in calcification:
                    
                    num_type_calcification_h[word_to_idx_calcification[carac]]=num_type_calcification_h[word_to_idx_calcification[carac]]+1
                elif carac in suggestivity and not bool_s:
                    bool_s=True
                    num_type_suggestivity_h[word_to_idx_suggestivity[carac]]=num_type_suggestivity_h[word_to_idx_suggestivity[carac]]+1
                
                elif carac in birads and not bool_b:
                    bool_b=True
                    num_type_birads_h[word_to_idx_birads[carac]]=num_type_birads_h[word_to_idx_birads[carac]]+1
    
    num_type_shape, num_type_margin, num_type_echogenicity, num_type_orientation, num_type_posterior,num_type_calcification, num_type_suggestivity= list_div(num_type_shape,num_shape), list_div(num_type_margin,num_margin), list_div(num_type_echogenicity,num_echogenicity), list_div(num_type_orientation,num_orientation), list_div(num_type_posterior,num_posterior),list_div(num_type_calcification,num_calcification), list_div(num_type_suggestivity,num_suggestivity)
    num_type_shape_h, num_type_margin_h, num_type_echogenicity_h, num_type_orientation_h, num_type_posterior_h,num_type_calcification_h, num_type_suggestivity_h=list_div(num_type_shape_h,num_shape), list_div(num_type_margin_h,num_margin), list_div(num_type_echogenicity_h,num_echogenicity), list_div(num_type_orientation_h,num_orientation), list_div(num_type_posterior_h,num_posterior),list_div(num_type_calcification_h,num_calcification), list_div(num_type_suggestivity_h,num_suggestivity)
    
    if not no_birads:
        num_type_birads=list_div(num_type_birads,num_birads)
        num_type_birads_h=list_div(num_type_birads_h,len(y_hat))
    
        
    p_casualidad_shape=sum(elememtwise_mul(num_type_shape,num_type_shape_h))
    p_casualidad_margin=sum(elememtwise_mul(num_type_margin,num_type_margin_h))
    p_casualidad_echogenicity=sum(elememtwise_mul(num_type_echogenicity,num_type_echogenicity_h))
    p_casualidad_orientation=sum(elememtwise_mul(num_type_orientation,num_type_orientation_h))
    p_casualidad_posterior=sum(elememtwise_mul(num_type_posterior,num_type_posterior_h))
    # p_casualidad_halo=sum(elememtwise_mul(num_type_halo,num_type_halo_h))
    p_casualidad_calcification=sum(elememtwise_mul(num_type_calcification,num_type_calcification_h))
    p_casualidad_suggestivity=sum(elememtwise_mul(num_type_suggestivity,num_type_suggestivity_h))
    
    if not no_birads:
        p_casualidad_birads=sum(elememtwise_mul(num_type_birads,num_type_birads_h))
    
    acc_shape=zero_div(shape_acc,num_shape)
    acc_margin=zero_div(margin_acc,num_margin)
    acc_echogenicity=zero_div(echogenicity_acc,num_echogenicity)
    acc_orientation=zero_div(orientation_acc,num_orientation)
    acc_posterior=zero_div(posterior_acc,num_posterior)
    # acc_halo=zero_div(halo_acc,num_halo)
    acc_calcification=zero_div(calcification_acc,num_calcification)
    acc_suggestivity=zero_div(suggestivity_acc,num_suggestivity)
    
    if not no_birads:
        acc_birads=zero_div(birads_acc,num_birads)
    if p_casualidad_shape==1:
        k_shape=1
    else:
        k_shape=round(zero_div((acc_shape-p_casualidad_shape),(1-p_casualidad_shape)),2)
    if p_casualidad_margin==1:
        k_margin=1
    else:
        k_margin=round(zero_div((acc_margin-p_casualidad_margin),(1-p_casualidad_margin)),2)
    if p_casualidad_echogenicity==1:
        k_echogenicity=1
    else:
        k_echogenicity=round(zero_div((acc_echogenicity-p_casualidad_echogenicity),(1-p_casualidad_echogenicity)),2)
    if p_casualidad_orientation==1:
        k_orientation=1
    else:
        k_orientation=round(zero_div((acc_orientation-p_casualidad_orientation),(1-p_casualidad_orientation)),2)
    
    if p_casualidad_posterior==1:
        k_posterior=1
    else:
        k_posterior=round(zero_div((acc_posterior-p_casualidad_posterior),(1-p_casualidad_posterior)),2)
    # k_halo=round(zero_div((acc_halo-p_casualidad_halo),(1-p_casualidad_halo)),2)
    if p_casualidad_calcification==1:
        k_calcification=1
    else:
        k_calcification=round(zero_div((acc_calcification-p_casualidad_calcification),(1-p_casualidad_calcification)),2)
    if p_casualidad_suggestivity==1:
        k_suggestivity=1
    else:
        k_suggestivity=round(zero_div((acc_suggestivity-p_casualidad_suggestivity),(1-p_casualidad_suggestivity)),2)

    if not no_birads:
        if p_casualidad_birads==1:
            k_birads=1
        else:
            k_birads=round(zero_div((acc_birads-p_casualidad_birads),(1-p_casualidad_birads)),2)
    if no_birads:
        return k_shape, k_margin, k_orientation, k_echogenicity, k_posterior,k_calcification, k_suggestivity
    correlation={"shape":k_shape, "margin":k_margin,"orientation": k_orientation, "echogenicity":k_echogenicity, "posterior":k_posterior, "calcification":k_calcification,"special cases":k_suggestivity, "birads":k_birads}
    num_descriptor={"shape":num_shape, "margin":num_margin,"orientation": num_orientation, "echogenicity":num_echogenicity, "posterior":num_posterior, "calcification":num_calcification,"special cases":num_suggestivity, "birads":num_birads}
    return {"correlation":correlation,"num_descriptor":num_descriptor}


def dedup_latest_by_user_nodule(data, use_time=False):
    """
    Devuelve dict {(nodule_id, user_id): row} quedándose con la última fila.
    """
    latest = {}
    for row in data:
        key = (row["nodule_id"], row["user_id"])
        prev = latest.get(key)

        if prev is None:
            latest[key] = row
        else:
            if use_time:
                # requiere row["time"] serializado (ideal: ISO string comparable o datetime)
                if row["time"] > prev["time"]:
                    latest[key] = row
            else:
                if row["id"] > prev["id"]:
                    latest[key] = row
    return latest


def build_ratings_by_item(latest_by_pair, field, cat_index):
    """
    latest_by_pair: dict {(nodule_id, user_id): row}
    Devuelve ratings_by_item: dict {nodule_id: [val1, val2, ...]} solo valores válidos
    """
    ratings_by_item = defaultdict(list)
    for (nodule_id, user_id), row in latest_by_pair.items():
        val = row[field]
        if val is None:
            continue
        if val not in cat_index:
            continue
        ratings_by_item[nodule_id].append(val)
    return dict(ratings_by_item)

def fleiss_kappa_variable_from_ratings(ratings_by_item, categories, only_items=None):
    """
    ratings_by_item: {item: [val, val, ...]}
    only_items: si se pasa, calcula SOLO sobre esos items.
    Devuelve (kappa, diagnostics, valid_items_used_set)
    """
    cat_index = {c: i for i, c in enumerate(categories)}
    k = len(categories)

    # Filtra items si hace falta
    items = list(ratings_by_item.keys())
    if only_items is not None:
        items = [i for i in items if i in only_items]

    # Ítems válidos: n_i >= 2
    valid_items = [i for i in items if len(ratings_by_item[i]) >= 2]
    if not valid_items:
        return None, {"reason": "No hay ítems con >=2 evaluadores."}, set()

    total_counts = [0] * k
    total_ratings = 0
    P_sum = 0.0
    ni_list = []

    for item in valid_items:
        vals = ratings_by_item[item]
        n_i = len(vals)
        ni_list.append(n_i)

        counts = [0] * k
        for v in vals:
            counts[cat_index[v]] += 1

        # acumula marginals
        for j in range(k):
            total_counts[j] += counts[j]
        total_ratings += n_i

        # P_i
        num = sum(c * (c - 1) for c in counts)
        P_i = num / (n_i * (n_i - 1))
        P_sum += P_i

    Pbar = P_sum / len(valid_items)
    pj = [c / total_ratings for c in total_counts]
    Pe = sum(p * p for p in pj)

    if Pe == 1.0:
        return None, {"reason": "Pe=1 (degenerado).", "Pbar": Pbar, "Pe": Pe}, set(valid_items)

    kappa = (Pbar - Pe) / (1.0 - Pe)

    diagnostics = {
        "n_items_used": len(valid_items),
        "n_items_with_any_rating": len([i for i in items if len(ratings_by_item[i]) >= 1]),
        "min_raters": min(ni_list),
        "max_raters": max(ni_list),
        "avg_raters": sum(ni_list) / len(ni_list),
        "Pbar": Pbar,
        "Pe": Pe,
        "pj": pj,
    }
    return kappa, diagnostics, set(valid_items)
def delta_fleiss_for_user(
    data_all,                 # desc + desc_others
    user_id,                  # radióloga que consulta
    field,
    categories,
    use_time=False
):
    """
    Devuelve:
    - kappa_all_overlap
    - kappa_without_overlap
    - delta
    - overlap_n (ítems comparables)
    - lost_without_you (ítems que eran válidos con ella pero pasan a <2 sin ella)
    - diagnostics de ambos
    """

    cat_index = {c: i for i, c in enumerate(categories)}

    # Dedup (última instancia)
    latest_all = dedup_latest_by_user_nodule(data_all, use_time=use_time)

    # Construye data_without (quitando a la radióloga) A NIVEL DE PARES ya deduplicados
    latest_without = {
        (nid, uid): row
        for (nid, uid), row in latest_all.items()
        if uid != user_id
    }

    # ratings por item
    ratings_all = build_ratings_by_item(latest_all, field, cat_index)
    ratings_wo  = build_ratings_by_item(latest_without, field, cat_index)

    # sets de ítems válidos (>=2) en cada escenario
    _, _, valid_all = fleiss_kappa_variable_from_ratings(ratings_all, categories)
    _, _, valid_wo  = fleiss_kappa_variable_from_ratings(ratings_wo,  categories)

    overlap = valid_all & valid_wo
    lost_without_you = len(valid_all - valid_wo)

    if not overlap:
        return {
            "kappa_all": None,
            "kappa_without": None,
            "delta": None,
            "overlap_n": 0,
            "lost_without_you": lost_without_you,
            "reason": "No hay ítems válidos comunes (>=2 evaluadores) en ambos escenarios."
        }

    # Calcula kappa en el MISMO set overlap
    k_all, diag_all, _ = fleiss_kappa_variable_from_ratings(ratings_all, categories, only_items=overlap)
    k_wo,  diag_wo,  _ = fleiss_kappa_variable_from_ratings(ratings_wo,  categories, only_items=overlap)

    return {
        "kappa_all": k_all,
        "kappa_without": k_wo,
        "delta": (k_all - k_wo) if (k_all is not None and k_wo is not None) else None,
        "overlap_n": len(overlap),
        "lost_without_you": lost_without_you,
        "diagnostics_all": diag_all,
        "diagnostics_without": diag_wo,
    }





def intercorrelation_Fleiss_fn(desc, desc_others, user_id):
    description_total = desc + desc_others

    correlation = {}
    num_descriptor = {}
    meta = {}

    for field, categories in descriptors.items():
        out = delta_fleiss_for_user(
            data_all=description_total,
            user_id=user_id,
            field=field,
            categories=categories,
            use_time=False,  # pon True si serializas "time"
        )

        # delta redondeada para UI
        correlation[field] = None if out["delta"] is None else round(out["delta"], 2)
        num_descriptor[field] = out["overlap_n"]  # lo que realmente comparas
        meta[field] = {
            "lost_without_you": out["lost_without_you"],
            "kappa_all": None if out["kappa_all"] is None else round(out["kappa_all"], 2),
            "kappa_without": None if out["kappa_without"] is None else round(out["kappa_without"], 2),
        }

    return {"correlation": correlation, "num_descriptor": num_descriptor, "meta": meta}







# def intercorrelation_Fleiss_fn(desc,desc_others):
#     description_total=desc+desc_others
#     correlation={}
#     num_descriptor={}
#     for field,categories in descriptors.items():
#         k1,diagnostic1=fleiss_kappa_from_serialized(description_total,field,categories)
#         print("Todos")
#         print(diagnostic1)
#         k2,diagnostic2=fleiss_kappa_from_serialized(desc_others,field,categories)
#         print("Sin radióloga")
#         print(diagnostic2)
#         correlation[field]=round(k1-k2,2)
#         num_descriptor[field]=diagnostic1["n_items_used"]
#     return {"correlation":correlation,"num_descriptor":num_descriptor}


def fleiss_kappa_from_serialized(data, field, categories, required_raters=None, use_time=False):
    """
    data: lista de dicts (serializer.data)
    field: descriptor ("shape", "margin", etc.)
    categories: lista de categorías válidas
    required_raters: opcional (si quieres forzar n fijo)
    use_time: si True usa 'time' para decidir la última instancia, si no usa 'id'
    """
    
    cat_index = word_to_idx_field[field]
    k=len(categories)

    # 1) DEDUP: (nodule_id, user_id) -> última fila
    latest_by_pair = {}
    for row in data:
        item = row["nodule_id"]
        user = row["user_id"]

        if item is None or user is None:
            continue

        key = (item, user)

        if key not in latest_by_pair:
            latest_by_pair[key] = row
        else:
            # decidir cuál es la "última"

            if row["id"] > latest_by_pair[key]["id"]:
                latest_by_pair[key] = row

    # 2) Construir ratings por nódulo usando SOLO la última instancia
    ratings_by_item = defaultdict(list)

    for (item, user), row in latest_by_pair.items():
        val = row[field]

        if val is None:
            continue  # usuario dejó el descriptor en blanco
        if val not in cat_index:
            continue

        ratings_by_item[item].append(val)

    
    # 3) Calcular kappa con n_i variable
    total_counts = [0] * k
    total_ratings = 0
    P_sum = 0.0
    used_items = 0
    ni_list = []

    for item, vals in ratings_by_item.items():
        n_i = len(vals)
        if n_i < 2:
            continue  # no aporta acuerdo
        ni_list.append(n_i)

        counts = [0] * k
        for v in vals:
            counts[cat_index[v]] += 1

        # acumular para p_j
        for j in range(k):
            total_counts[j] += counts[j]
        total_ratings += n_i

        # P_i
        num = sum(c * (c - 1) for c in counts)
        P_i = num / (n_i * (n_i - 1))

        P_sum += P_i
        used_items += 1

    if used_items == 0:
        return None, {"reason": "No hay ítems con >=2 evaluadores en este descriptor."}

    Pbar = P_sum / used_items
    pj = [c / total_ratings for c in total_counts]
    Pe = sum(p * p for p in pj)

    if Pe == 1.0:
        return None, {"reason": "Pe = 1 (degenerado).", "Pbar": Pbar, "Pe": Pe}

    kappa = (Pbar - Pe) / (1.0 - Pe)

    diagnostics = {
        "n_items_used": used_items,
        "n_items_with_any_rating": len(ratings_by_item),
        "min_raters": min(ni_list) if ni_list else None,
        "max_raters": max(ni_list) if ni_list else None,
        "avg_raters": (sum(ni_list) / len(ni_list)) if ni_list else None,
        "Pbar": Pbar,
        "Pe": Pe,
        "pj": pj,
        "after_dedup_pairs": len(latest_by_pair),
    }
    return round(kappa,2), diagnostics