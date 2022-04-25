import numpy as np
import pandas as pd
from scipy import stats


# converts json to data frame
def json_to_df(json_data):
    dic = {'submitter_ID':[],'project_ID':[],'measure':[],'level1_perc':[],'level2_cate':[]}
    percentage = []
    for i in range(len(json_data['data'])):
        dic['submitter_ID'].append(json_data['data'][i]['submitter_id'])
        dic['project_ID'].append(json_data['data'][i]['project_id'])
        dic['measure'].append(json_data['data'][i]['measure'])
        dic['level1_perc'].append(json_data['data'][i]['level1']['overall_percentage'])
        dic['level2_cate'].append(list(json_data['data'][i]['level2']['categories'].keys()))
        for j in dic['level2_cate'][len(dic['level2_cate'])-1]:
            percentage.append(json_data['data'][i]['level2']['categories'][j]['percentage'])
            
    df = pd.DataFrame.from_dict(dic).explode('level2_cate')
    df.reset_index(inplace=True, drop=True)
    df['percentage']= pd.Series(percentage)
    
    two_way = pd.DataFrame(df.groupby(['measure','level2_cate'])['percentage'].apply(list))
    
    return(two_way)

# remove by smallest distance
def reduce_by_distance(arr, end_len):
    while len(arr) > end_len:
        arr = sorted(arr)
        dist = [arr[ind]-arr[ind-1] for ind, x in enumerate(arr)][1:]
        minimum = dist.index(min(dist))
        if minimum == 0:
            arr.pop(0)
        elif minimum == len(arr)-2:
            arr.pop()
        else:
            first = arr[minimum]-arr[minimum-1]
            second = arr[minimum+1]-arr[minimum+2]
            if first < second:
                arr.pop(minimum)
            else:
                arr.pop(minimum+1)
    return(arr)

def disclaimer(two_way, Var_0):
    dist = []
    l = []
    for i in two_way['percentage']:
        l.append(len(i))
    if min(l) < 30:
        dist.append("insufficient sample size")
    if len(set(l))>1:
        dist.append("unpaired data")
    if Var_0 == True:
        dist.append("0 Variance")
    return(dist)

# calculates correlation between all combination
def analyze_two_way(two_way, min_len = 2):
    dic = []
    Var_0 = False
    for i in range(len(two_way)):
        if len(two_way.iloc[i]['percentage'])<min_len:
            continue
        for j in range(i+1,len(two_way)):
            if len(two_way.iloc[j]['percentage'])<min_len:
                continue
            elif len(two_way.iloc[i]['percentage'])<len(two_way.iloc[j]['percentage']):
                new = reduce_by_distance(two_way.iloc[j]['percentage'], len(two_way.iloc[i]['percentage']))
                cor = stats.spearmanr(two_way.iloc[i]['percentage'],new).correlation
                if pd.isnull(cor) == False:
                    dic.append([two_way.iloc[i].name[1],two_way.iloc[i].name[0],two_way.iloc[j].name[1],two_way.iloc[j].name[0],cor])
                else:
                    Var_0 = True
            elif len(two_way.iloc[j]['percentage'])<len(two_way.iloc[i]['percentage']):
                new = reduce_by_distance(two_way.iloc[i]['percentage'], len(two_way.iloc[j]['percentage']))
                cor = stats.spearmanr(new,two_way.iloc[j]['percentage']).correlation
                if pd.isnull(cor) == False:
                    dic.append([two_way.iloc[i].name[1],two_way.iloc[i].name[0],two_way.iloc[j].name[1],two_way.iloc[j].name[0],cor])
                else:
                    Var_0 = True
            else:
                cor = stats.spearmanr(two_way.iloc[i]['percentage'],two_way.iloc[j]['percentage']).correlation
                if pd.isnull(cor) == False:
                    dic.append([two_way.iloc[i].name[1],two_way.iloc[i].name[0],two_way.iloc[j].name[1],two_way.iloc[j].name[0],cor])
                else:
                    Var_0 = True
    return(dic, Var_0)

def lambda_handler(event, context):
    if event['data']=={}:
        return("empty_project")
    else:
        two_way = json_to_df(event)
        cor, var_0 = analyze_two_way(two_way)
        dist = disclaimer(two_way, var_0)
        res = {'correlation':cor, 'disclaimer': dist}
        return(res)
