#EVALUATING CAP PAYMENTS SENT BETWEEN COUNTRIES 
#LAST DATE MODIFIED 15 June 2020
#PRINCIPAL INVESTIGATOR: Kimberly Nicholas, Lund University Centre for Sustainability Studies, kimberly.nicholas@lucsus.lu.se
#PROGRAMMER: Edmund Lehsten, edmund.lehsten@gmail.com 

#Data are reported by country where EU sent the payment. The recipient, however, is sometimes listed in another country. The purpose of this code is to extract from the raw data files payments that went to a country other than the reporting country, and create a file (money_transactions) where these payments are collected for further analysis. This code generates a file where payments are listed twice: both as a payment made from Country A to Country B (listed as a positive amount from Country A in euro) and a payment received by Country B from Country A (payment listed as a negative amount from Country B in euro). Thus the total money sums to zero across all countries. 


from glob import glob
import pandas as pd
import numpy as np

#list of files to analyse
input_files = glob("output/*_translated.csv")

#master dataframe to store all data in
money_transactions = pd.DataFrame()

#loop through files
for in_file in input_files:
    #inform which country is currently running:
    print(in_file)

    #load in file to dataframe
    df = pd.read_csv(in_file,error_bad_lines=False,usecols=["year","NUTS_3","amount_EURO"])

    #remove numbers at the end of nuts codes
    df["NUTS_3"]=df["NUTS_3"].str.strip("\'").str[0:2]

    #condense data by nuts and year, sum amount
    df = df.groupby(["NUTS_3","year"]).sum().reset_index()
    
    #remove entry from same country
    df = df[df["NUTS_3"]!=in_file[7:9].upper()]

    #for all entries where nuts is not country multiply by -1 in order to identify payments that should be deducted from the host country, since these were sent abroad. 
    df["amount_EURO"] *=-1

    #add country column
    df = df.assign(country=(np.array([in_file[7:9].upper() for i in range(df.shape[0])])))

    #rename NUTS_3 column
    df.rename(columns={'NUTS_3': 'from_country'}, inplace=True)

    #add data to master dataframe
    money_transactions = money_transactions.append(df)

#create file for analysis that lists transactions twice, both as sent from Country A to Country B (positive €), as listed in original data; and a new line created here, listing transaction received by Country B from Country A (negative €, hence multiply by -1 to reverse the sign).  
#get all negative values from the transactions
df = money_transactions[money_transactions["amount_EURO"]<0]
#swap from country and to country
df.rename(columns={"from_country":"country","country":"from_country"}, inplace=True)
#swap amount to positive
df["amount_EURO"] *= -1
#append the data to the master
money_transactions = money_transactions.append(df)

#save data
money_transactions.reset_index()
money_transactions.to_csv("money_transactions.csv",index=False)

