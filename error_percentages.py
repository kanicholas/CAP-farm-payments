import pandas as pd
import numpy as np
import csv
from glob import glob


def extract_data(data):
    #get total amount of money
    total = sum(data["amount_EURO"])

    #get amount of money in unmatched NUTS
    total_nuts = sum(data["amount_EURO"][data["NUTS_3"].str.contains("NaN")])

    #get amount of money in unmatched scheme
    total_scheme = sum(data["amount_EURO"][data["translated_scheme"].str.contains("notTranslated")])
    
    #get number of schemes
    num_schemes = 0
    if "scheme" in data.columns:
        num_schemes = len(set(data["scheme"]))
    else:
        num_schemes = len(set(data["scheme_2"]))
    return total,total_nuts,total_scheme,num_schemes

#get all files
files = glob("output/*_translated.csv")

#open output file
with open("missing_money_percentages_abs.csv","w+") as f1:
    #print header
    print("country, total, percent scheme, percent nuts, total (abs), percent scheme (abs), percent nuts (abs),number of schemes, length, year",file=f1)
    #loop over files
    for f in files:
        #get country
        cnt = f[7:9]
    
        #load in file
        data = pd.read_csv(f,dtype={"translated_scheme":str,"amount_EURO":float})
        
        #fix loading nan values
        data["amount_EURO"] = data["amount_EURO"].fillna(0)

        #make absoulte
        data_abs = data.copy()
        data_abs["amount_EURO"] = abs(data_abs["amount_EURO"])
    
        #check that file inclueds year, if not extract year from name
        if "year" in data.columns:
            years = set(data["year"])
            for year in years:
                total,total_nuts,total_scheme,num_schemes= extract_data(data[data["year"]==year])
                abs_total,abs_nuts,abs_scheme,__= extract_data(data_abs[data["year"]==year])
                #print CNT,year,total_money,percentSCHEME,PercentNuts
                print(f"{cnt}, {total}, {total_scheme/total}, {total_nuts/total},{abs_total},{abs_scheme/abs_total},{abs_nuts/abs_total},{num_schemes},{data['year'].shape[0]}, {year}",file=f1)
        else:
            year = f[10:-14]
            total,total_nuts,total_scheme,num_schemes= extract_data(data)
            abs_total,abs_nuts,abs_scheme,__= extract_data(data_abs)
            num_lines = data

            #print CNT,year,total_money,percentSCHEME,PercentNuts
            print(f"{cnt}, {total}, {total_scheme/total}, {total_nuts/total},{abs_total},{abs_scheme/abs_total},{abs_nuts/abs_total},{num_schemes},{data.shape[0]}, {year}",file=f1)
        print(f"{cnt} DONE")
    
print("DONE!")
