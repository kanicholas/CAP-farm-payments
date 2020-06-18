import numpy as np
import pandas as pd
from glob import glob

files = glob("output/*translate*.csv")
with open("totals.csv","w+") as out:
    print("cnt,total,total_abs,year",file=out)
    for f in files:
        df = pd.read_csv(f,dtype={"amount_EURO":float})
        df["amount_EURO"] = df["amount_EURO"].fillna(0)
        if "year" in df.columns:
            for year in set(df["year"]):
                tmp = df[df["year"]==year]
                total = sum(tmp["amount_EURO"])
                total_abs = sum(np.abs(tmp["amount_EURO"]))
                print(f"{f[7:9]},{total},{total_abs},{year}",file = out)
        else:
            total = sum(df["amount_EURO"])
            total_abs = sum(np.abs(df["amount_EURO"]))
            year = f[10:-3]
            print(f"{f[7:9]},{total},{total_abs},{year}",file = out)
print("done")
