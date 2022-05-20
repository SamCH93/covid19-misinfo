def read_table(filename, datadir='./out', levels=None):
    import pandas as pd
    import os
    file = os.path.join(datadir, filename)
    if levels is None:
        levels = 0
        with open(file, 'r') as fd:
            for i in fd.readline().split(','):
                if i: break
                else: levels += 1
    df = pd.read_csv(file, index_col=list(range(levels)))
    return df

def import_datadict(datadir='./dat', filename='orb_datadict.txt'):
    '''Imports the data dictionary for raw survey data.
    See questions and field names in /doc/orb_questionnaire.pdf

    Args:
        datadir (:obj:`str`): name of directory where dictionary is located
        filename (:obj:`str`): name of dictionary file (.txt)

    Returns:
        A :obj:`dict` containing keys:
        * 'dict' which maps to a :obj:`dict` of field names (:obj:`str') mapped to a :obj:`dict` of values (:obj:`str`) mapped to recoded-vaues (:obj:`int`)
        * 'desc' which maps to a :obj:`dict` of field names (:obj:`str') mapped to their descriptions (:obj:`str`)
    '''
    import os
    filepath = os.path.join(datadir, filename)
    with open(filepath, encoding='utf-8') as fd: data = fd.readlines()
    data = [d for d in data if d.strip()]
    for i in range(len(data)):
        if data[i][0]!='\t': data[i] = [x.strip() for x in data[i].split(':')]
        else: data[i] = [data[i].strip()]
    dmap = {}
    text = {}
    curr = ''
    multi = ''
    for d in data:
        if len(d)==1:
            tmp = d[0].split('\t')
            if len(tmp)==2:
                if tmp[0][0]=='[':
                    curr = tmp[0][1:-1]
                    desc = tmp[1].strip()
                    text[curr] = desc
                    dmap[curr] = dmap[multi].copy()
                else:
                    dmap[curr][tmp[1]] = int(tmp[0])
        elif len(d)>1:
            if d[0][0]=='[':
                curr = d[0][1:-1]
                desc = d[1].strip()
                text[curr] = desc
                dmap[curr] = {}
            elif d[0]!='Values':
                curr = d[0]
                desc = d[1].strip()
                text[curr] = desc
                dmap[curr] = {}
                multi = curr
    #rectify some encoding issues
    errata = {'DREL':{'Other Christian:':'Other Christian:\xa0'},
              'DPOLUK':{'Other:':'Other:\xa0'}
                }
    #recoding extra variables of age categories and treatment (ANTI) or control (PRO) group
    extras = {'imageseen':{'ANTI US':1, 'PRO US':0, 'ANTI UK':1, 'PRO UK':0}, 
              'agerecode':{ '18-24':1, '25-34':2, '35-44':3, '45-54':4, '55-64':5, '65+':6}}
    for key in errata:
        if key in dmap:
            for label in errata[key]:
                if label in dmap[key]:
                    dmap[key][errata[key][label]] = dmap[key][label]
                    del dmap[key][label]
    for key in extras: dmap[key] = extras[key]
    return {'dict':dmap,'desc':text}

def import_data(datadir='./dat', filename='orb_200918.sav'):
    '''Reads a survey SPSS file and returns a :obj:`pd.DataFrame`.
    See questions and field names in /doc/orb_questionnaire.pdf

    Args:
        datadir (:obj:`str`): name of directory where SPSS file is located
        filename (:obj:`str`): name of the SPSS file (.sav)

    Returns:
        A :obj:`pd.DataFrame` containing field names as columns and record as rows, with values recoded 
    '''
    import os
    import pandas as pd
    filepath = os.path.join(datadir, filename)
    if filepath[-4:] == '.sav': df = pd.read_spss(filepath)
    else: df = pd.read_csv(filepath)
    for att in list(df):
        try: df[att].str.strip('\xa0') #funny encoding issue
        except: pass
    return df

def transform_data(df, dd, country='UK', group=None, minimal=True, save=''):
    '''Cleans, recodes and transforms raw survey data.
    See questions and field names in /doc/orb_questionnaire.pdf

    Args:
        df (:obj:`pd.DataFrame`): contains raw survey data (see return value of ``import_data()``)
        dd (:obj:`dict`): contains data dictionary for the raw survey data (see return value of ``import_datadict()``)
        country (:obj:`str`=`{'UK', 'US'}`: name of country of interest; default=`UK`
        group (:obj:`int`=`{0, 1}`): name of the experiment group, where `0` is for control and `1` is for treatment; default=`None` (imports all samples)
        save (:obj:`str`): filepath to save the processed data (as a .csv) and data dictionary (as a .pkl); default='' (does not save anything)

    Returns:
        A size-2 :obj:`tuple` containing
        * A :obj:`pd.DataFrame` containing field names as columns and record as rows of the transformed data
        * A :obj:`dict` of field names (:obj:`str`) mapped to a :obj:`dict` of recoded-values (:obj:`int`) mapped to value-names (:obj:`str`)
    '''
    #define all socio-demographic variables of interest
    if minimal:
        demo = {'UK': {'agerecode':'Age', 'DGEN':'Gender', 'DEDUUK':'Education_UK', 'DEMP':'Employment', 'DREL':'Religion', 
                      'DPOLUK':'Political_UK', 'DETHUK':'Ethnicity_UK', 'DINCUK':'Income_UK'},
                'USA': {'agerecode':'Age', 'DGEN':'Gender', 'DEDUUS':'Education_US', 'DEMP':'Employment', 'DREL':'Religion',
                        'DPOLUS':'Political_US', 'DETHUS':'Ethnicity_US', 'DINCUS':'Income_US'}}
    else:
        demo = {'UK': {'agerecode':'Age', 'DGEN':'Gender', 'DEDUUK':'Education_UK', 'DEMP':'Employment', 'DREL':'Religion', 
                      'DPOLUK':'Political_UK', 'DETHUK':'Ethnicity_UK', 'DINCUK':'Income_UK', 'DGEOUK':'Region'},
                'USA': {'agerecode':'Age', 'DGEN':'Gender', 'DEDUUS':'Education_US', 'DEMP':'Employment', 'DREL':'Religion',
                        'DPOLUS':'Political_US', 'DETHUS':'Ethnicity_US', 'DINCUS':'Income_US', 'DGEOUS':'Region'}}
    
    #define recoding of socio-demographics
    var_encoding = {'Gender':{(1,):'Male', (2,):'Female', (3, 4):'Other'},
                    'Education_US':{(1, 2):'Level-0', (3,):'Level-1', (4,):'Level-2', (5,):'Level-3', (6,):'Level-4', (7, 8):'Other'}, 
                    'Education_UK':{(1,):'Level-0', (2, 3):'Level-1', (5,):'Level-2', (6,):'Level-3', (7,):'Level-4', (4, 8, 9):'Other'}, 
                    'Employment':{(1, 2):'Employed', (3,):'Unemployed', (4,):'Student', (6,):'Retired', (5, 7, 8):'Other'},
                    'Religion':{(1, 2, 3):'Christian', (4,):'Jewish', (6,):'Muslim', (9,):'Atheist', (5, 7, 8, 10):'Other'},
                    'Political_US':{(1,):'Republican', (2,):'Democrat', (3, 4, 5):'Other'},
                    'Political_US_ind':{(1,):'Republican', (2,):'Democrat', (3, 4):'Other'},
                    'Political_UK':{(1,):'Conservative', (2,):'Labour', (3,):'Liberal-Democrat', (4,):'SNP', (5,6,7):'Other'},
                    'Ethnicity_US':{(1,):'White', (2,):'Hispanic', (3,):'Black', (5,):'Asian', (4, 6, 7, 8):'Other'},
                    'Ethnicity_UK':{(1, 2, 3):'White', (4, 11):'Black', (5, 6, 7, 8, 9, 10):'Asian', (12, 13):'Other'},
                    'Income_US':{(1,):'Level-0', (2, 3):'Level-1', (4, 5): 'Level-2', (6, 7, 8, 9):'Level-3', (10,):'Level-4', (11,):'Other'},
                    'Income_UK':{(1,):'Level-0', (2,):'Level-1', (3,):'Level-2', (4, 5,):'Level-3', (6, 7, 8, 9, 10):'Level-4', (11,):'Other'}
                   }
    
    #rename other survey variables of interest to make them human-comprehendable
    metrics_any = {'QINFr1': 'Nobody', 'QINFr2': 'Myself', 'QINFr3': 'Family inside HH', 'QINFr4': 'Family outside HH', 
                   'QINFr5': 'Close friend', 'QINFr6': 'Colleague'}    
    metrics_knl = {'QKNLr1': 'Washing hands', 'QKNLr2': 'Staying indoors for Self', 'QKNLr3': 'Staying indoors for Others', 
                   'QKNLr4': 'Spread before symptoms', 'QKNLr5': 'R-Number', 'QKNLr6': 'Treatments already exist', 'QKNLr7': 'Wearing masks'}
    metrics_cov = {'QCOVVCIr3': 'COVID-19 Vax Importance', 'QCOVVCIr1': 'COVID-19 Vax Safety', 'QCOVVCIr2': 'COVID-19 Vax Efficacy', 
                   'QCOVVCIr4': 'COVID-19 Vax Compatibility', 'QCOVVCIr5': 'Contract via COVID-19 Vax', 'QCOVVCIr6': 'COVID-19 Vax benefits outweigh risks'}
    metrics_vci = {'QVCIr1': 'Vax Importance', 'QVCIr2': 'Vax Safety', 'QVCIr3': 'Vax Efficacy', 'QVCIr4': 'Vax Compatibility'}
    metrics_aff = {'QCOVAFFr1': 'Mental health', 'QCOVAFFr2': 'Financial stability', 'QCOVAFFr3': 'Daily disruption', 'QCOVAFFr4': 'Social disruption'}
    trust = {'UK': {'QSRCUKr1': 'Television', 'QSRCUKr2': 'Radio', 'QSRCUKr3': 'Newspapers', 'QSRCUKr4': 'Govt. Briefings', 
                    'QSRCUKr5': 'National Health Authorities', 'QSRCUKr6': 'International Health Authorities', 'QSRCUKr7': 'Healthcare Workers', 
                    'QSRCUKr8': 'Scientists', 'QSRCUKr9': 'Govt. Websites', 'QSRCUKr10': 'Social Media', 'QSRCUKr11': 'Celebrities', 'QSRCUKr12': 'Search Engines', 
                    'QSRCUKr13': 'Family and friends', 'QSRCUKr14': 'Work Guidelines', 'QSRCUKr15': 'Other', 'QSRCUKr16': 'None of these'},
             'USA': {'QSRCUSr1': 'Television', 'QSRCUSr2': 'Radio', 'QSRCUSr3': 'Newspapers', 'QSRCUSr4': 'White House Briefings', 'QSRCUSr5':'State Govt. Briefings', 
                     'QSRCUSr6': 'National Health Authorities', 'QSRCUSr7': 'International Health Authorities', 'QSRCUSr8':'Healthcare Workers', 
                     'QSRCUSr9': 'Scientists', 'QSRCUSr10': 'Govt. Websites', 'QSRCUSr11': 'Social Media', 'QSRCUSr12': 'Celebrities', 'QSRCUSr13': 'Search Engines', 
                     'QSRCUSr14': 'Family and friends', 'QSRCUSr15': 'Work Guidelines', 'QSRCUSr16': 'Other', 'QSRCUSr17': 'None of these'}}
    reasons = {'QCOVSELFWHYr1': 'Unsure if safe', 'QCOVSELFWHYr2': 'Unsure if effective', 'QCOVSELFWHYr3': 'Not at risk', 'QCOVSELFWHYr4': 'Wait until others',
               'QCOVSELFWHYr5': "Won't be ill", 'QCOVSELFWHYr6': 'Other effective treatments', 'QCOVSELFWHYr7': 'Already acquired immunity',
               'QCOVSELFWHYr8': 'Approval may be rushed', 'QCOVSELFWHYr9': 'Other', 'QCOVSELFWHYr10': 'Do not know'}
    metrics_img = {'QPOSTVACX_Lr': 'Vaccine Intent', 'QPOSTBELIEFX_Lr': 'Agreement', 'QPOSTTRUSTX_Lr': 'Trust', 
                   'QPOSTCHECKX_Lr': 'Fact-check', 'QPOSTSHARE_Lr': 'Share'}
    social_atts = {'QSOCTYPr': 'used', 'QSOCINFr': 'to receive info', 'QCIRSHRr': 'to share info'}
    if minimal:
        other_atts = {'QSOCUSE':'Social media usage', 
                      'QPOSTSIM':'Seen such online content',
                      'QCOVSELF':'Vaccine Intent for self (Pre)', 
                      'QPOSTCOVSELF':'Vaccine Intent for self (Post)',
                      'QCOVOTH':'Vaccine Intent for others (Pre)', 
                      'QPOSTCOVOTH':'Vaccine Intent for others (Post)', 
                      'imageseen':'Group'}
    else:
        other_atts = {'QSHD':'Shielding',
                      'QSOCUSE':'Social media usage', 
                      'QCOVWHEN':'Expected vax availability',
                      'QPOSTSIM':'Seen such online content',
                      'QPOSTFRQ':'Frequency of such online content',
                      'Q31b':'Engaged with such online content',
                      'QCOVSELF':'Vaccine Intent for self (Pre)', 
                      'QPOSTCOVSELF':'Vaccine Intent for self (Post)',
                      'QCOVOTH':'Vaccine Intent for others (Pre)', 
                      'QPOSTCOVOTH':'Vaccine Intent for others (Post)', 
                      'imageseen':'Group'}
             
    def expand_socc(code):
        names = ['Facebook', 'Twitter', 'YouTube', 'WhatsApp', 'Instagram', 'Pinterest', 'LinkedIN', 'Other', 'None of these']
        out = {}
        for k in code:
             for i in range(len(names)): out['%s%i'%(k, i+1)] = '%s %s'%(names[i], code[k])
        return out
    
    def demo_map(code):
        fwd, bwd = {}, {}
        for key in code:
            fwd[key] = dict(zip(code[key].values(), range(1, len(code[key])+1)))
            bwd[key] = dict(zip(range(1, len(code[key])+1), code[key].values()))
        return fwd, bwd
    
    def expand_imgc(code, num=5):
        out = {}
        for i in range(num):
            for c in code:
                out['%s%i'%(c, i+1)] = 'Image %i:%s'%(i+1, code[c])
        return out
             
    def expand_code(code):
        new = {}
        for key in code:
            new[key] = {}
            for k, v in code[key].items():
                for i in k: new[key][i] = v
        return new
    
    metrics_img = expand_imgc(metrics_img)
    social_atts = expand_socc(social_atts)
    var_fwd, var_bwd = demo_map(var_encoding)
    var_encoding = expand_code(var_encoding)    
    
    if minimal: atts = []
    else: atts = list(metrics_any.keys())+list(metrics_knl.keys())+list(metrics_cov.keys())+list(metrics_vci.keys())+list(metrics_aff.keys())+list(social_atts.keys())
    atts += list(trust[country].keys())+list(reasons.keys())+list(metrics_img.keys())
    atts += list(other_atts.keys())+list(demo[country].keys())
    
    def recode_treatment(x): return int('ANTI' in x)
            
    def recode_bools(x): return int('NO TO:' not in x)
        
    def recode_likert(x, inverse=False):
        if inverse: m = {'Strongly agree': -2, 'Tend to agree': -1, 'Tend to disagree': 1, 'Strongly disagree': 2, 'Do not know': 0}
        else: m = {'Strongly agree': 2, 'Tend to agree': 1, 'Tend to disagree': -1, 'Strongly disagree': -2, 'Do not know': 0}
        return m[x]
    
    def recode_likert_num(x, inverse=False):
        if inverse: m = [-2,-1,0,1,2,0]
        else: m = [2,1,0,-1,-2,0]
        return m[x-1]
    
    def recode_age(x):
        if x>118: x = 118
        return (x-18)/100
    
    if group is None:
        idx = df['country']==country
        if country=='UK': idx = idx & ((df['imageseen']=='PRO UK')|(df['imageseen']=='ANTI UK')) #Country field is unreliable, has a bug
        elif country=='USA': idx = idx & ((df['imageseen']=='PRO US')|(df['imageseen']=='ANTI US'))
    else:
        if country=='UK': idx = df['imageseen']==group+' UK'
        elif country=='USA': idx = df['imageseen']==group+' US'    
    
    df_new = df.loc[idx,atts]
    dd_new = {}
    
    if not minimal:
        for key in metrics_any:
            df_new[key] = df_new[key].apply(recode_bools)
            df_new.rename(columns={key:'Know anyone:%s'%metrics_any[key]}, inplace=True)
            dd_new['Know anyone:%s'%metrics_any[key]] = {1:'Checked', 0:'Unchecked'}
        for key in metrics_knl:
            df_new[key] = df_new[key].apply(recode_likert)
            df_new.rename(columns={key:'COVID-19 Knowledge:%s'%metrics_knl[key]}, inplace=True)
            dd_new['COVID-19 Knowledge:%s'%metrics_knl[key]] = {2:'Strongly agree',1:'Tend to agree',0:'Do not know',-1:'Tend to disagree',-2:'Strongly disagree'}
        for key in metrics_cov:
            df_new[key] = df_new[key].apply(recode_likert)
            df_new.rename(columns={key:'COVID-19 VCI:%s'%metrics_cov[key]}, inplace=True)
            dd_new['COVID-19 VCI:%s'%metrics_cov[key]] = {2:'Strongly agree',1:'Tend to agree',0:'Do not know',-1:'Tend to disagree',-2:'Strongly disagree'}
        for key in metrics_vci:
            df_new[key] = df_new[key].apply(recode_likert)
            df_new.rename(columns={key:'General VCI:%s'%metrics_vci[key]}, inplace=True)
            dd_new['General VCI:%s'%metrics_vci[key]] = {2:'Strongly agree',1:'Tend to agree',0:'Do not know',-1:'Tend to disagree',-2:'Strongly disagree'}
        for key in metrics_aff:
            df_new[key] = df_new[key].apply(recode_likert)
            df_new.rename(columns={key:'COVID-19 Impact:%s'%metrics_aff[key]}, inplace=True)
            dd_new['COVID-19 Impact:%s'%metrics_aff[key]] = {2:'Strongly agree',1:'Tend to agree',0:'Do not know',-1:'Tend to disagree',-2:'Strongly disagree'}
        for key in social_atts:
            df_new[key] = df_new[key].apply(recode_bools)
            df_new.rename(columns={key:'Social:%s'%social_atts[key]}, inplace=True)
            dd_new['Social:%s'%social_atts[key]] = {1:'Checked', 0:'Unchecked'}
             
    for key in trust[country]:
        df_new[key] = df_new[key].apply(recode_bools)
        df_new.rename(columns={key:'Trust:%s'%trust[country][key]}, inplace=True)
        dd_new['Trust:%s'%trust[country][key]] = {1:'Checked', 0:'Unchecked'}
    for key in reasons:
        df_new[key] = df_new[key].apply(recode_bools)
        df_new.rename(columns={key:'Reason:%s'%reasons[key]}, inplace=True)
        dd_new['Reason:%s'%reasons[key]] = {1:'Checked', 0:'Unchecked'}    
    for key in metrics_img:
        df_new.replace({key: dd['dict'][key]}, inplace=True)
        df_new[key] = df_new[key].apply(recode_likert_num)
        df_new.rename(columns={key:metrics_img[key]}, inplace=True)
        dd_new[metrics_img[key]] = {2:'Strongly agree',1:'Tend to agree',0:'Do not know',-1:'Tend to disagree',-2:'Strongly disagree'}

        
    df_new.replace({att: dd['dict'][att] for att in other_atts if att!='imageseen'}, inplace=True)
    for att in other_atts:
        df_new.rename(columns={att:other_atts[att]}, inplace=True)
        if att!='imageseen': dd_new[other_atts[att]] = dict(zip(dd['dict'][att].values(), dd['dict'][att].keys()))
    
    df_new.replace({key: dd['dict'][key] for key in demo[country] if key not in ['agerecode', 'DGEOUK', 'DGEOUS']}, inplace=True)
    df_new.rename(columns=demo[country], inplace=True)
    df_new.replace(var_encoding, inplace=True)
    df_new.replace(var_fwd, inplace=True)
    for att in demo[country]:
        if demo[country][att] in var_fwd: dd_new[demo[country][att].split('_')[0]] = var_bwd[demo[country][att]]
        else:
            df_new.replace({demo[country][att]: dd['dict'][att]}, inplace=True)
            dd_new[demo[country][att]] = {b: a for (a, b) in dd['dict'][att].items()}
    df_new['Treatment'] = df_new['Group'].apply(recode_treatment)
    del df_new['Group']
    dd_new['Treatment'] = {0: 'Control', 1:'Treatment'}
    df_new.rename(columns={i:i.split('_')[0] for i in list(df_new)}, inplace=True)
    if save:
        df_new.to_csv('%s.csv'%save)
        import pickle, json
        with open('%s.pkl'%save, 'wb') as fp: pickle.dump(dd_new, fp)
        with open('%s.json'%save, 'w') as fp: json.dump(dd_new, fp)
    return df_new, dd_new

def import_transformed_data(filepath=''):
    '''Reads the transformed survey data.
    See questions and field names in /doc/orb_questionnaire.pdf, and refer to recoding in ``transform_data()``

    Args:
        filepath (:obj:`str`): filepath to read the processed data (without the .csv/.pkl suffix)

    Returns:
        A size-2 :obj:`tuple` containing
        * A :obj:`pd.DataFrame` containing field names as columns and record as rows of the transformed data
        * A :obj:`dict` of field names (:obj:`str`) mapped to a :obj:`dict` of recoded-values (:obj:`int`) mapped to value-names (:obj:`str`)
    '''
    import pandas as pd
    import pickle
    df = pd.read_csv('%s.csv'%filepath, index_col=0)
    with open('%s.pkl'%filepath, 'rb') as fp: dd = pickle.load(fp)
    return df, dd

def get_socdem_counts(df, dd, by='Treatment'):
    '''Returns counts of different socio-demographics broken down by a variable of interest.

    Args:
        df (:obj:`pd.DataFrame`): contains transformed data (see return value of ``transform_data()``, ``import_transformed_data()``)
        dd (:obj:`dict`): contains data dictionary for transformed data (see return value of ``transform_data()``, ``import_transformed_data()``)
        by (:obj:`str`): variable of interest; default='Treatment' (returns distribution of demographics across the 2 experiment groups)

    Returns:
        A :obj:`pd.DataFrame` with 2-level index whose outer index corresponds to soc-demo name, inner index to soc-demo value, and columns correspond to % and counts across categories of variable of interest
    '''
    import pandas as pd
    atts = ['Age', 'Gender', 'Education', 'Employment', 'Religion', 'Political', 'Ethnicity', 'Income', 'Social media usage']
    out = []
    for idx, d in df.groupby(by):
        out.append({})
        for att in atts:
            tmp = d[att].value_counts().loc[list(dd[att].keys())]
            tmp.index = dd[att].values()
            tmp.name = '%s (N)'%dd[by][idx]
            tmp_perc = (100*tmp/tmp.sum()).round(1)
            tmp_perc.name = '%s (%%)'%dd[by][idx]
            out[-1][att] = pd.concat([tmp, tmp_perc], axis=1)
        out[-1] = pd.concat(out[-1], axis=0)
    out = pd.concat(out, axis=1)
    return out

def count_attribute(df, att, by_att=None, norm=False, where=None, dd={}, plot=False, att_lab='', by_att_lab='', title='', dpi=90):
    '''Returns counts of any variable of interest, possibly conditioned on a second variable.

    Args:
        df (:obj:`pd.DataFrame`): contains transformed data (see return value of ``transform_data()``, ``import_transformed_data()``)
        att (:obj:`str`): primary variable of interest
        by_att (:obj:`str`): secondary variable of interest to condition counts of the first one on; default=`None`
        norm (:obj:`bool`): whether to normalise the counts to indicate Pr(att); if by_att is not `None` then counts are normalized such that summing Pr(att|by_att) over by_att gives 1
        where (:obj:`list` of size-2 :obj:`tuple` of (:obj:`str`, :obj:`int`)): extra variables to subset the samples on where the tuple encodes a (variable-name, value) pair; default=[]
        dd (:obj:`dict`): contains data dictionary for transformed data (see return value of ``transform_data()``, ``import_transformed_data()``) for sorting counts by given variable-ordering; default={}
        plot (:obj: `bool`): whether to plot the counts; default=`False`
        att_lab (:obj:`str`): if plotting, label for y-axis (primary variable); default=`''`
        by_att_lab (:obj:`str`): if plotting, label for legend (secondary variable); default=`''`
        title (:obj:`str`): if plotting, plot title; default=`''`
        dpi (:obj:`int`): if plotting, dpi for figure; default=90

    Returns:
        A :obj:`pd.DataFrame`/:obj:`pd.Series` whose index corresponds to att and columns to by_att
    '''
    if where is not None:
        if not isinstance(where, list): where = [where]
        for w in where:
            if w[1] is None: df = df[df[w[0]].isnull()]
            else: df = df[df[w[0]]==w[1]]
    if by_att is None: counts = df[att].value_counts()
    else:
        from pandas import concat
        groups = df[[att, by_att]].groupby(by_att)
        names = list()
        counts = list()
        for name, group in groups:
            names.append(name)
            counts.append(group[att].value_counts())
        counts = concat(counts, axis=1, keys=names, sort=True)
        if dd:
            if by_att in dd:
                counts = counts[dd[by_att].keys()]
                counts.rename(columns=dd[by_att], inplace=True)
    counts.fillna(0, inplace=True)
    if norm: counts = counts/counts.values.sum(0)
    if dd:
        if att in dd:
            counts = counts.loc[dd[att].keys()]
            counts.rename(index=dd[att], inplace=True)
    if plot:
        import matplotlib.pyplot as plt
        from seaborn import countplot
        plt.figure(dpi=dpi)
        order, hue_order = None, None
        if dd:
            if by_att is not None and by_att in dd and att in dd:
                df = df[[att,by_att]]
                df = df.replace({att: dd[att], by_att: dd[by_att]})
                hue_order = dd[by_att].values()
                order = dd[att].values()
            else:
                if att in dd:
                    df = df[[att]]
                    df = df.replace({att: dd[att]})
                    order = dd[att].values()
        if by_att is None: countplot(y=att, data=df, order=order)
        else: countplot(y=att, hue=by_att, data=df, order=order, hue_order=hue_order)
        plt.gca().set_xlabel('Count')
        if att_lab: plt.gca().set_ylabel(att_lab)
        if by_att_lab: plt.gca().get_legend().set_title(by_att_lab)
        if not title and where is not None: title = ', '.join([str(w[0])+' = '+str(w[1]) for w in where])
        plt.title(title)
        plt.show()        
    return counts

def stats(fit, statistics=['mean', '2.5%', '97.5%', 'n_eff', 'Rhat'], digits=2, exclude_lp=True, save=''):
    import pandas as pd
    sumobj = fit.summary()
    params = list(sumobj['summary_rownames'])
    stats = list(sumobj['summary_colnames'])
    out = pd.DataFrame(sumobj['summary'], index=params, columns=stats)
    if exclude_lp: out.drop(index='lp__', inplace=True)
    if statistics: out = out[statistics]
    roundmap = dict([(key, 0) if key=='n_eff' else (key, digits) for key in out])
    out = out.round(roundmap)
    out = out.rename(columns={'mean':'Mean', 'n_eff':'ESS'})
    if 'n_eff' in statistics: out = out.astype({'ESS':int})
    if save: out.to_csv('%s.csv'%save)
    return out

def stats_impact(fit, save=''):
    import numpy as np
    from .bayesoc import Outcome, Model
    import pandas as pd
    m = 2
    k = 4
    def foo(x): return np.diff(np.hstack([0, np.exp(x)/(1+np.exp(x)), 1]))
    df = Model(Outcome()).get_posterior_samples(fit=fit)
    prob = []
    names = ['Yes, definitely', 'Unsure, lean yes', 'Unsure, lean no', 'No, definitely not']
    for i in range(1, m+1):
        alpha = df[['alpha[%i,%i]'%(i, j) for j in range(1, k)]].values
        p = []
        for a in alpha: p.append(foo(a))
        p = np.vstack(p)
        prob.append(pd.DataFrame(p, columns=names))
    prob.append(prob[1]-prob[0])
    groups = ['Pre Exposure', 'Post Exposure', 'Post-Pre']
    out = pd.concat({groups[i]: prob[i].describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']] for i in range(len(groups))})
    if save: out.to_csv('%s.csv'%save)
    return out

def stats_impact_causal(fit, save=''):
    import numpy as np
    from .bayesoc import Outcome, Model
    import pandas as pd
    m = 2
    k = 4
    def foo(x): return np.diff(np.hstack([0, np.exp(x)/(1+np.exp(x)), 1]))
    df = Model(Outcome()).get_posterior_samples(fit=fit)
    prob_full, prob = [], []
    dfs_full, dfs = [], [[], [], []]
    names = ['Yes, definitely', 'Unsure, lean yes', 'Unsure, lean no', 'No, definitely not']
    p_pre = [foo(x) for x in df[['alpha_pre[%i]'%j for j in range(1, k)]].values]
    for i in range(1, m+1):
        alpha_pre = df[['alpha_pre[%i]'%j for j in range(1, k)]].values
        beta = np.hstack([np.zeros((df.shape[0],1)), df[['beta[%i]'%i]].values*df[['delta[%i,%i]'%(i, j) for j in range(1, k)]].values.cumsum(axis=1)])
        alpha = df[['alpha[%i,%i]'%(i, j) for j in range(1, k)]].values
        p_full, p = [], []
        for (p_p, a, b) in zip(p_pre, alpha, beta):
            p.append(np.array([foo(a-b_) for b_ in b]))
            p_full.append((p_p[:,np.newaxis]*p[-1]).sum(axis=0))
        prob_full.append(np.vstack(p_full))
        prob.append(np.dstack(p))
        dfs_full.append(pd.DataFrame(prob_full[-1], columns=names).describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']])
        for j in range(k):
            dfs[i-1].append(pd.DataFrame(prob[-1][j].T, columns=names).describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']])
    diff_full = prob_full[1] - prob_full[0]
    diff = prob[1]-prob[0]
    dfs_full.append(pd.DataFrame(diff_full, columns=names).describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']])
    dfs_full.append(pd.DataFrame(p_pre, columns=names).describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']])
    for i in range(k):
        dfs[-1].append(pd.DataFrame(diff[i].T, columns=names).describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']])
    groups = ['Control', 'Treatment', 'Treatment-Control', 'Baseline']
    out = pd.concat({groups[i]: pd.concat({names[j]: dfs[i][j] for j in range(len(names))}) for i in range(len(groups)-1)})
    out_full = pd.concat({groups[i]: dfs_full[i] for i in range(len(groups))})
    if save:
        out.to_csv('%s_CATE.csv'%save)
        out_full.to_csv('%s_ATE.csv'%save)
    return {'ATE':out_full, 'CATE':out}

def multi2index(index, suffix=''):
    att_cat = {}
    for att in index:
        if ':' in att[0]:
            key, val = tuple(att[0].split(':'))
            if key in att_cat:
                att_cat[key]['idx'].append(att)
                att_cat[key]['val'].append(val+suffix)
            else: att_cat[key] = {'idx': [att], 'val': [val+suffix]}
        else:
            if att[0] in att_cat:
                att_cat[att[0]]['idx'].append(att)
                att_cat[att[0]]['val'].append(att[1]+suffix)
            else: att_cat[att[0]] = {'idx': [att], 'val': [att[1]+suffix]}
    return att_cat

def plot_stats(df, demos=False, oddsratio=True, fig=None, ax=None, ax_outer=None, fignum=1, figidx=0, figsize=2, stack_h=True, 
    title='', subtitle=[], xlabel='', subxlabel=[], tick_suffix='', label_suffix='', label_text='', ylabel=True, bars=False, factor=0.4, 
    signsize=10, ticksize=10, labelsize=10, titlesize=12, subtitlesize=12, hspace=0.3, wspace=0.05, widespace=1, align_labels=False, 
    title_loc=0.0, label_loc=0.0, highlight=False, show=True, capitalize=False, identical_counts=False, save='', fmt='pdf'):
    if not isinstance(df, list): df = [df]
    if isinstance(subtitle, str): subtitle = [subtitle]*len(df)
    if isinstance(subxlabel, str): subxlabel = [subxlabel]*len(df)
    import matplotlib.pyplot as plt
    import numpy as np
    cols = len(df)
    dem = ['Age', 'Gender', 'Education', 'Employment', 'Religion', 'Political', 'Ethnicity', 'Income']
    for i in range(cols):
        atts = list(df[i].index)
        if not isinstance(atts[0], tuple):
            from pandas import concat
            df[i] = concat({'tmp': df[i]})
            atts = list(df[i].index)
            ylabel = False
    if not demos: atts = [i for i in atts if i[0] not in dem]
    att_cat = multi2index(atts, tick_suffix)
    rows = len(att_cat)
    rows_per = [len(att_cat[k]['idx']) for k in att_cat]
    if fig is None:
        if fignum>1:
            if stack_h:
                fig = plt.figure(dpi=180, figsize=(figsize*(cols*fignum+(fignum-1)*widespace), factor*sum(rows_per)))
                grid = fig.add_gridspec(nrows=1, ncols=fignum, wspace=widespace/cols)
                ax = np.empty((rows, cols*fignum), dtype=object)
                ax_outer = np.empty(fignum, dtype=object)
                for i in range(fignum):
                    ax_outer[i] = fig.add_subplot(grid[i], frame_on=False, xticks=[], yticks=[])
                    inner = grid[i].subgridspec(nrows=rows, ncols=cols, hspace=hspace/sum(rows_per), wspace=wspace, height_ratios=rows_per)
                    for j in range(rows):
                        for k in range(cols): ax[j,i*cols+k] = fig.add_subplot(inner[j, k])
            else:
                fig = plt.figure(dpi=180, figsize=(figsize*cols, factor*(sum(rows_per)*fignum+(fignum-1)*widespace)))
                grid = fig.add_gridspec(nrows=fignum, ncols=1, hspace=widespace/sum(rows_per))
                ax = np.empty((rows*fignum, cols), dtype=object)
                ax_outer = np.empty(fignum, dtype=object)
                for i in range(fignum):
                    ax_outer[i] = fig.add_subplot(grid[i], frame_on=False, xticks=[], yticks=[])
                    inner = grid[i].subgridspec(nrows=rows, ncols=cols, hspace=hspace/sum(rows_per), wspace=wspace, height_ratios=rows_per)
                    for j in range(rows):
                        for k in range(cols): ax[i*rows+j,k] = fig.add_subplot(inner[j, k])
        else:
            fig, ax = plt.subplots(nrows=rows, ncols=cols, dpi=180, figsize=(figsize*cols, factor*sum(rows_per)), gridspec_kw={'hspace':hspace, 'wspace':wspace, 'height_ratios': rows_per}, squeeze=False)
            ax_outer = [fig.add_subplot(111, frame_on=False, xticks=[], yticks=[])]
    names = list(att_cat.keys())
    def plot_bars(ax, tmp, ticks=[], right=False, base=False):
        num = tmp.shape[0]
        if highlight: colors = ['k' if tmp['2.5%'][tmp.index[i]]<oddsratio<tmp['97.5%'][tmp.index[i]] else 'r' for i in range(num)]
        else: colors = 'k'
        if base:
            if bars: ax.barh(y=list(range(num+1, num+2-base, -1))+list(range(num+1-base, 0, -1)), width=tmp['mean'].values, xerr=np.vstack([(tmp['mean']-tmp['2.5%']).values, (tmp['97.5%']-tmp['mean']).values]), color='salmon')
            else: ax.errorbar(x=tmp['mean'].values, y=list(range(num+1, num+2-base, -1))+list(range(num+1-base, 0, -1)), xerr=np.vstack([(tmp['mean']-tmp['2.5%']).values, (tmp['97.5%']-tmp['mean']).values]), ecolor=colors, marker='o', color='k', ls='')
            ax.text(0, num+2-base, 'REFERENCE', size=ticksize)
        else:
            if bars: ax.barh(y=range(num, 0, -1), width=tmp['mean'].values, xerr=np.vstack([(tmp['mean']-tmp['2.5%']).values, (tmp['97.5%']-tmp['mean']).values]), color='salmon')
            else: ax.errorbar(x=tmp['mean'].values, y=range(num, 0, -1), xerr=np.vstack([(tmp['mean']-tmp['2.5%']).values, (tmp['97.5%']-tmp['mean']).values]), ecolor=colors, marker='o', color='k', ls='')
        if bars and highlight:
            for i in range(num):
                lb, ub = tmp['2.5%'][tmp.index[i]], tmp['97.5%'][tmp.index[i]]
                if not (lb<oddsratio<ub):
                    if lb<0: ax.text(lb, num-i, '*', size=signsize)
                    else: ax.text(ub, num-i, '*', size=signsize)
        else: ax.set_ylim(1-0.5, num+0.5)
        if ticks:
            t = range(1, num+1)
            if capitalize: ticks = [x.capitalize() if not x.isupper() else x for x in ticks]
        else: t = []
        ax.axvline(oddsratio, ls=':', color='gray')
        ax.yaxis.set_ticklabels(reversed(ticks))
        ax.yaxis.set_ticks(t)
        if right: ax.yaxis.tick_right()
    
    for i in range(rows):
        for j in range(cols):
            if stack_h: u, v = i, cols*figidx+j
            else: u, v = rows*figidx+i, j
            if j==0:
                plot_bars(ax[u,v], df[j].loc[att_cat[names[i]]['idx']], att_cat[names[i]]['val'])
                if ylabel: ax[u,v].set_ylabel(names[i]+label_suffix, fontweight='bold', fontsize=labelsize)
            elif j==cols-1:
                try:
                    if identical_counts: c = list(map(lambda y: str(int(y)), df[0]['counts'][att_cat[names[i]]['idx']].values))
                    else: c = [', '.join(list(map(lambda y: str(int(y)), x))) for x in np.array([df[k]['counts'][att_cat[names[i]]['idx']].values for k in range(cols)]).T]
                except: c = []
                plot_bars(ax[u,v], df[j].loc[att_cat[names[i]]['idx']], c, right=True)
            else: plot_bars(ax[u,v], df[j].loc[att_cat[names[i]]['idx']])
            if i==0 and subtitle and (stack_h or not(figidx)): ax[u,v].set_title(subtitle[j], fontsize=subtitlesize)
            if i==rows-1 and subxlabel: ax[u,v].set_xlabel(subxlabel[j], fontsize=labelsize)

    if align_labels: fig.align_ylabels()
    if title: ax_outer[figidx].set_title(title, fontweight='bold', fontsize=titlesize, y=1+title_loc)
    if label_text and (stack_h or not(figidx)): ax_outer[figidx].text(1+label_loc, 1.01, label_text, size=subtitlesize, transform=ax_outer[figidx].transAxes)    
    if xlabel and (stack_h or figidx==fignum-1): ax_outer[figidx].set_xlabel(xlabel)
    #plt.subplots_adjust(hspace=hspace, wspace=wspace)
    #fig.tight_layout()
    if save: plt.savefig('%s.%s'%(save, fmt), dpi=180, bbox_inches='tight')
    if show: plt.show()
    return fig, ax, ax_outer

def plot_causal_flow(df, title='', save='', fmt='pdf'):
    def plot_sankey(group):
        import plotly.graph_objects as go
        src, tgt, val = [], [], []
        labs = ['Yes, definitely', 'Unsure, lean yes', 'Unsure, lean no', 'No, definitely not']*2
        for i in range(4):
            for j in range(4, 8):
                src.append(i)
                tgt.append(j)
                val.append(df['CATE'].loc[(group,labs[i],labs[j]), 'mean']*df['ATE'].loc[('Baseline',labs[i]), 'mean'])
        fig = go.Figure(data=[go.Sankey( 
        node = dict(pad=15, thickness=40, line=dict(color='salmon', width=0.5), color='salmon',
                    label=['[%i] %s'%(round(100*y), x) for x, y in zip(labs[:4], df['ATE'].loc['Baseline', 'mean'])]+['%s [%i]'%(x, round(100*y)) for x, y in zip(labs[4:], df['ATE'].loc[group, 'mean'])]),
        link = dict(source=src, target=tgt, value=val))])
        fig.update_layout(title_text='%s %s'%(title, group), font_size=20)
        fig.show()
        if save: fig.write_image('%s_%s.%s'%(save, group, fmt), scale=4)
    plot_sankey('Treatment')
    plot_sankey('Control')

def stats_socdem(fit, dd, df, atts=[], causal=True, group=None, oddsratio=True, save=''):
    import numpy as np
    import pandas as pd
    from .bayesoc import Dim, Outcome, Model
    import matplotlib.pyplot as plt
    cats = ['Age', 'Gender', 'Education', 'Employment', 'Religion', 'Political', 'Ethnicity', 'Income']
    if isinstance(atts, str): atts = [atts]
    for att in atts: cats += [x for x in list(df) if x[:len(att)]==att]
    outs = ['Vaccine Intent for self (Pre)', 'Vaccine Intent for self (Post)', 'Treatment']
    bases = [1]*len(cats) #default reference category for all socio-demographics
    bases[2] = 5 #reference category for education
    bases[7] = 5 #reference category for income
    tmp = Model(Outcome())
    if causal:
        stats = {'Control':{}, 'Treatment':{}, 'Treatment-Control':{}}
        counts = {'Control':{}, 'Treatment':{}, 'Treatment-Control':{}}
    else:
        stats = {}
        counts = {}
    def foo(x): return np.exp(x)
    def getcounts(cat, base, group=None):        
        vals = np.sort(list(dd[cat].keys()))
        if group is None: counts = df[cat].value_counts().loc[vals]
        else: counts = df[df['Treatment']==group][cat].value_counts().loc[vals]
        counts.index = [dd[cat][k] for k in vals]
        return counts.iloc[list(range(base-1))+list(range(base, len(vals)))]
    def summarize(stats, counts):
        if oddsratio: stats = stats.apply(foo)
        stats = stats.describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']]
        stats.drop('chain', inplace=True)
        stats.index = counts.index
        return stats
    def mergecats(stats, counts):
        stats = pd.concat(stats)
        counts = pd.concat(counts)
        counts.name = 'counts'
        return stats.merge(counts.to_frame(), left_index=True, right_index=True)
    for cat, base in zip(cats, bases):
        dim = Dim(name=cat)
        if causal:
            for idx, key in zip([1, 2], ['Control', 'Treatment']):
                counts[key][cat] = getcounts(cat, base, idx-1)
                stats[key][cat] = tmp.get_posterior_samples(pars=['beta_%s[%i,%i]'%(dim.name, idx, i+1) for i in range(len(dd[cat]))], contrast='beta_%s[%i,%i]'%(dim.name, idx, base), fit=fit)
                stats[key][cat].columns = ['beta_%s[%i]'%(dim.name, i+1) for i in range(len(dd[cat])) if i!=base-1]+['chain']
            stats['Treatment-Control'][cat] = stats['Treatment'][cat] - stats['Control'][cat]
            counts['Treatment-Control'][cat] = counts['Treatment'][cat] + counts['Control'][cat]
            for key in stats: stats[key][cat] = summarize(stats[key][cat], counts[key][cat])
        else:
            counts[cat] = getcounts(cat, base, group)
            stats[cat] = tmp.get_posterior_samples(pars=['beta_%s[%i]'%(dim.name, i+1) for i in range(len(dd[cat]))], contrast='beta_%s[%i]'%(dim.name, base), fit=fit)
            stats[cat] = summarize(stats[cat], counts[cat])
    if causal: out = pd.concat({key: mergecats(stats[key], counts[key]) for key in stats})
    else: out = mergecats(stats, counts)
    if save: out.to_csv('%s.csv'%save)
    return out

def mean_image_perceptions(df, melt=True, save=''):
    import pandas as pd
    metrics = ['Vaccine Intent', 'Agreement', 'Trust', 'Fact-check', 'Share']
    gmap = {0: 'Control', 1:'Treatment'}
    vmap = {i-2: 'p[%i]'%(i+1) for i in range(5)}
    out = {}
    for group, d in df.groupby('Treatment'):
        scores_all = {}
        for i in range(5):
            scores = {}
            for m in metrics:
                tmp = d['Image %i:%s'%(i+1, m)].value_counts().sort_index()
                tmp = tmp/tmp.sum()
                scores[m] = tmp.rename(vmap)            
            if melt: scores_all[i+1] = pd.concat(scores).to_frame('mean')
            else: scores_all[i+1] = pd.DataFrame(scores)
        out[gmap[group]] = pd.concat(scores_all)
    out = pd.concat(out)
    if save: out.to_csv('%s.csv'%save)
    return out

def plot_image_perceptions(df, ylab=[], label_image=False, imagewise=False, legend_space=0.2, legend_loc=(0.5, 0.5), labelsize=12, legendsize=12, figsize=2, save='', fmt='pdf'):
    import numpy as np
    import matplotlib.pyplot as plt
    import matplotlib
    
    if not isinstance(df, list): df = [df]
    questions = {'Vaccine Intent': 'Raises vaccine intent', 'Agreement': 'Agree with information', 'Trust': 'Have trust in', 'Fact-check': 'Will fact-check', 'Share': 'Will share'}
    categories = dict(zip(['p[%i]'%(i+1) for i in range(5)], ['Strongly disagree', 'Somewhat disagree', 'Neither', 'Somewhat agree', 'Strongly agree']))
    
    def survey(results, category_names, ax=None):
        """
        Parameters
        ----------
        results : dict
            A mapping from question labels to a list of answers per category.
            It is assumed all lists contain the same number of entries and that
            it matches the length of *category_names*.
        category_names : list of str
            The category labels.
        """
        # Ref: https://matplotlib.org/3.1.1/gallery/lines_bars_and_markers/horizontal_barchart_distribution.html
        labels = list(results.keys())
        data = np.array(list(results.values()))
        data_cum = data.cumsum(axis=1)
        category_colors = plt.get_cmap('RdYlBu')(np.linspace(0.15, 0.85, data.shape[1]))

        if ax is None: fig, ax = plt.subplots(dpi=90, figsize=(5, 5))
        ax.invert_yaxis()
        ax.xaxis.set_visible(False)
        if not label_image: ax.set_yticks([])
        ax.set_xlim(0, np.sum(data, axis=1).max())

        for i, (colname, color) in enumerate(zip(category_names, category_colors)):
            widths = data[:, i]
            starts = data_cum[:, i] - widths
            ax.barh(labels, widths, left=starts, height=0.5, label=colname, color=color)
            xcenters = starts + widths / 2
            r, g, b, _ = color
            text_color = 'white' if r * g * b < 0.5 else 'dimgray'
            for y, (x, c) in enumerate(zip(xcenters, widths)):
                ax.text(x, y, str(int(100*c)), ha='center', va='center', color=text_color)
        return ax
    
    nrows = len(df)
    fig = plt.figure(dpi=180, figsize=(figsize*5, figsize*(nrows+legend_space)), constrained_layout=not(label_image))
    grid = fig.add_gridspec(nrows=2, ncols=1, hspace=0, height_ratios=[nrows, legend_space])
    inner = grid[0].subgridspec(nrows=nrows, ncols=5)
    ax = np.empty((nrows, 5), dtype=object)
    ax_outer = fig.add_subplot(grid[1], frame_on=False, xticks=[], yticks=[])
    for i in range(nrows):
        for j in range(5): ax[i,j] = fig.add_subplot(inner[i, j])
    if imagewise:
        for p in range(nrows):
            for i in range(5):
                results = {questions[j]: df[p]['mean'][(i+1, j)][list(categories.keys())].values for j in questions}
                results['Raises Vaccine Intent'] = results['Raises Vaccine Intent'][::-1]
                survey(results, categories.values(), ax[p,i])
                if p==0: ax[p,i].set_title('Image %i'%(i+1))
                if i==0 and ylab: ax[p,i].set_ylabel(ylab[p], fontsize=labelsize, fontweight='bold')
    else:
        for p in range(nrows):
            flag = True
            for j, a in zip(questions, ax[p]):
                if j=='Vaccine Intent': results = {'Img %i'%(i+1): df[p]['mean'][(i+1, j)][list(categories.keys())].values[::-1] for i in range(5)}
                else: results = {'Img %i'%(i+1): df[p]['mean'][(i+1, j)][list(categories.keys())].values for i in range(5)}
                survey(results, categories.values(), a)
                if p==0: a.set_title(questions[j])
                if flag and ylab:
                    a.set_ylabel(ylab[p], fontsize=labelsize, fontweight='bold')
                    flag = False
    if label_image: plt.tight_layout()
    handles, labels = ax[0,0].get_legend_handles_labels()
    ax_outer.legend(handles=handles, labels=labels, ncol=5, bbox_to_anchor=legend_loc, loc='center', fontsize=legendsize, shadow=False, edgecolor='white')
    #plt.tight_layout()
    if save: plt.savefig('%s.%s'%(save, fmt), dpi=180, bbox_inches='tight')
    plt.show()

def stats_image_impact(fit, oddsratio=False, plot=False, num_metrics=5, num_images=5, save=''):
    import numpy as np
    import pandas as pd
    from .bayesoc import Outcome, Model
    tmp = Model(Outcome())
    pars = ['beta_img[%i]'%(i+1) for i in range(num_metrics)]
    if plot: tmp.plot_posterior_pairs(fit=fit, pars=pars)
    pars2 = ['gamma[%i]'%(i+1) for i in range(num_images)]
    df = tmp.get_posterior_samples(pars=pars, fit=fit)
    def foo(x): return np.exp(x)
    if oddsratio: out = df[pars].apply(foo).merge(tmp.get_posterior_samples(pars=pars2, fit=fit)[pars2], left_index=True, right_index=True).describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']]
    else: out = df[pars].merge(tmp.get_posterior_samples(pars=pars2, fit=fit)[pars2], left_index=True, right_index=True).describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']]
    if save: out.to_csv('%s.csv'%save)
    return out

def stats_similar_content(fit, save=''):
    import numpy as np
    from .bayesoc import Outcome, Model
    import pandas as pd
    m = 2
    k = 4
    def foo(x): return np.diff(np.hstack([0, np.exp(x)/(1+np.exp(x)), 1]))
    df = Model(Outcome()).get_posterior_samples(fit=fit)
    def get_p(kind='pre'):
        beta = [[np.zeros((df.shape[0], 1)), df['beta_%s[%i]'%(kind, i)].values[:,np.newaxis]] for i in range(1, m+1)]
        alpha = [df[['alpha_%s[%i,%i]'%(kind, i, j) for j in range(1, k)]].values for i in range(1, m+1)]
        if kind=='post':
            for i in range(1, m+1):
                beta[i-1][0] = np.hstack([np.zeros((df.shape[0], 1)), df['beta[%i]'%i].values[:,np.newaxis]*df[['delta[%i,%i]'%(i, j) for j in range(1, k)]].values])
                beta[i-1][1] = beta[i-1][1] + beta[i-1][0]
        p = [[], []]
        for i in range(m):
            for (a, b0, b1) in zip(alpha[i], beta[i][0], beta[i][1]): p[i].append(np.stack([[foo(a-b) for b in b0], [foo(a-b) for b in b1]]))
            p[i] = np.stack(p[i])
            if kind=='pre': p[i] = p[i][:,:,0,:]
        return p
    p = {k:get_p(k) for k in ['pre', 'post']}
    p['post marg'] = [(p['pre'][i][:,:,:,np.newaxis]*p['post'][i]).sum(2) for i in range(m)]
    for k in p:
        for i in range(m): p[k][i] = np.concatenate([p[k][i], (p[k][i][:,1,:] - p[k][i][:,0,:])[:,np.newaxis,:]], axis=1)
        p[k].append(p[k][1]-p[k][0])
    names = ['Yes, definitely', 'Unsure, lean yes', 'Unsure, lean no', 'No, definitely not']
    label = ['Not seen', 'Seen', 'Seen-Not seen']
    group = ['Control', 'Treatment', 'Treatment-Control']
    kind = {'pre': 'Pre-exposure', 'post marg': 'Post-exposure'}
    out = pd.concat({kind[key]: pd.concat({group[i]: pd.concat({label[j]: pd.DataFrame(p[key][i][:,j], columns=names).describe(percentiles=[0.025, 0.975]).T[['mean', '2.5%', '97.5%']] for j in range(len(label))}) for i in range(len(group))}) for key in ['pre', 'post marg']})
    if save: out.to_csv('%s.csv'%save)
    return out

def collapse_df(df, perc=False, fmt=None, save=''):
    import pandas as pd
    out = []
    if not isinstance(fmt, list): fmt = [fmt]*df.shape[0]
    if 'mean' in list(df):
        for (f, x), (lb, ub) in zip(zip(fmt, df['mean'].values), zip(df['2.5%'].values, df['97.5%'].values)):
            if perc: out.append('%.1f (%.1f, %.1f)'%(100*x, 100*lb, 100*ub))
            else:
                if f=='.1f': out.append('%.1f (%.1f, %.1f)'%(x, lb, ub))
                elif f=='i': out.append('%i (%i, %i)'%(x, lb, ub))
                else: out.append('%.2f (%.2f, %.2f)'%(x, lb, ub))
    else:
        for f, (lb, ub) in zip(fmt, zip(df['min'].values, df['max'].values)):
            if perc: out.append('%.1f, %.1f'%(100*lb, 100*ub))
            else:
                if f=='.1f': out.append('%.1f, %.1f'%(lb, ub))
                elif f=='i': out.append('%i, %i'%(lb, ub))
                else: out.append('%.2f, %.2f'%(lb, ub))
    out = pd.Series(out, index=df.index)
    if save: out.to_csv('%s.csv'%save)
    return out

def unstack_df(df, by_first=False, save=''):
    def order(index):
        row, col = [], []
        if by_first:
            for i in index:
                if len(i)==2:
                    if i[-1] not in row: row.append(i[-1])
                elif i[1:] not in row: row.append(i[1:])
                if i[0] not in col: col.append(i[0])
        else:
            for i in index:
                if len(i)==2:
                    if i[0] not in row: row.append(i[0])
                elif i[:-1] not in row: row.append(i[:-1])
                if i[-1] not in col: col.append(i[-1])
        return row, col
    r, c = order(df.index)
    if by_first:
        import pandas as pd
        out = pd.concat({i: df.loc[i] for i in c}, axis=1)
    else: out = df.unstack().loc[r, c]
    if save: out.to_csv('%s.csv'%save)
    return out

def subset_df(df, atts, reset=False, save=''):
    import pandas as pd
    if isinstance(atts, (str, tuple)): atts = [atts]
    if isinstance(atts[0], str):
        index = multi2index(df.index)
        subidx, subval = [], []
        for att in atts:
            if att in index:
                subidx += index[att]['idx']
                subval += index[att]['val']
        out = df.loc[subidx]
        if reset:
            out['index'] = subval
            out.set_index('index', verify_integrity=True, inplace=True)
            # del out.index.name
            out = out.rename_axis(None, axis=0)
    else:
        if isinstance(df, pd.core.frame.DataFrame) and len(df.index[0])==len(atts[0]): out = pd.DataFrame.from_dict({att: df.loc[att] for att in atts}, orient='index')
        else: out = pd.concat({att: df.loc[att] for att in atts})
    if save: out.to_csv('%s.csv'%save)
    return out

def combine_idx(multiindex_l, multiindex_r):
    index_l = multi2index(multiindex_l)
    index_r = multi2index(multiindex_r)
    index_lr = []
    for idx in index_l:
        index_lr += index_l[idx]['idx']
        if idx in index_r:
            for x in index_r[idx]['idx']:
                if x not in index_lr: index_lr.append(x)
    for idx in index_r:
        if idx not in index_l: index_lr += index_r[idx]['idx']
    return index_lr

def combine_dfs(df_l, df_r, lsuffix='(1)', rsuffix='(2)', multi=True, axis=1, atts=[], reset=True, retain_order=True, fillna='-', save=''):
    if multi or axis==0:
        import pandas as pd
        df = pd.concat({lsuffix: df_l, rsuffix: df_r}, axis=axis)
    if not multi:
        if axis==1: df = df_l.join(df_r, lsuffix=' '+lsuffix, rsuffix=' '+rsuffix, how='outer')
        else:
            idx = zip(df.index, (map(lambda x: ('%s %s'%(x[1], x[0]),)+x[2:], df.index)))
            df = pd.DataFrame.from_dict({new: df.loc[old] for old, new in idx}, orient='index')
    if retain_order and axis==1: df = df.loc[combine_idx(df_l.index, df_r.index)]
    if atts: df = subset_df(df, atts, reset=reset)
    if fillna: df.fillna(fillna, inplace=True)
    if save: df.to_csv('%s.csv'%save)
    return df

def organize_df(df, perc=False, fmt=None, unstack=False, by_first=False, atts=[]):
    tmp = collapse_df(df, perc=perc, fmt=fmt)
    if unstack and isinstance(df.index[0], tuple) and len(df.index[0])>2: tmp = unstack_df(tmp, by_first=by_first)
    if atts: tmp = subset_df(tmp, atts=atts)
    return tmp
