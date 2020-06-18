import pandas as pd
import numpy as np
import csv
from glob import glob

files = glob("output/*_translated.csv")
missing_schemes_dict = {}
missing_money_in_post = {}
missing_money_in_scheme = {}
for f in files:
    data = pd.read_csv(f,dtype={"translated_scheme":str})
    data = data[data["translated_scheme"].notna()]
    missing_schemes = data[data["translated_scheme"].str.contains("notTranslated")]
    percent_mon_scheme=0
    try:
        missing_schemes_dict[f[7:9]] = list(set(missing_schemes["scheme"]))
        percent_mon_scheme = np.nansum(missing_schemes["amount_EURO"])/np.nansum(data["amount_EURO"])
    except:
        missing_schemes_dict[f[7:9]] = list(set(missing_schemes["scheme_2"]))
        percent_mon_scheme=np.nansum(missing_schemes["amount_EURO"])/np.nansum(data["amount_EURO"])
    missing_codes = data[data["NUTS_3"].str.contains("nan")]
    percent_mon = np.nansum(missing_codes["amount_EURO"])/np.nansum(data["amount_EURO"])
    missing_money_in_post[f[7:9]]=percent_mon*100
    missing_money_in_scheme[f[7:9]]=percent_mon_scheme*100
    print("unable to match {}% of money in file:{}".format(percent_mon_scheme*100,f))

with open("error_schemes.csv","w") as outfile:
    writer = csv.writer(outfile)
    writer.writerow(list(missing_schemes_dict.keys()))
    writer.writerows(list(missing_schemes_dict.values()))

print("DONE!")
