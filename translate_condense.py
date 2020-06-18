#ALIGNING RAW CAP SPENDING FILES WITH CAP SCHEMES AND LOCATIONS IN NUTS REGIONS 
#LAST DATE MODIFIED 11 June 2020
#PRINCIPAL INVESTIGATOR: Kimberly Nicholas, Lund University Centre for Sustainability Studies, kimberly.nicholas@lucsus.lu.se
#PROGRAMMER: Edmund Lehsten, edmund.lehsten@gmail.com 


#Make folder on computer which contains all files downloaded from Eurostat listing postcode and NUTS3. These files should not be renamed and should all be in the same folder. Set the variable nuts_folder under user variables to equal this folder's location.

#Note filenames of raw data must be in standard Farmsubsidy.org format, that is, a two-letter country code + underscore + year(s) + .csv. For example, "at_2015.csv" or "dk_2014_2015.csv" 


#Import libraries, some need installation
from glob import glob
import pandas as pd
import numpy as np
import re
import logging
import subprocess
from string import digits
#install libraries here if not already on your system (panda, glob) using pip

#user variables:
scheme_key_loc = "key.csv" #translation file for nuts codes
input_folder = "input" #folder name where input files are stored
output_folder = "output" #folder where outputs should be placed 
nuts_folder = "key/nuts" #folder where nuts files are stored

#Define conversion rate from different currencies to euro for different years
conversion_rate_to_euro = {"2014":{"EUR":1.0,"CZK":0.03632,"DKK":0.134142,"GBP":1.2411,"HRK":0.1310,"HUF":0.003240,"PLN":0.2390,"SEK":0.10995,"BGN":0.5113},
        "2015":{"EUR":1.0,"CZK":0.03666,"DKK":0.134072,"GBP":1.3785,"HRK":0.1313,"HUF":0.003227,"PLN":0.2391,"SEK":0.10693,"BGN":0.5113},
        "2016":{"EUR":1.0,"CZK":0.03699,"DKK":0.134315,"GBP":1.2239,"HRK":0.1328,"HUF":0.003211,"PLN":0.2292,"SEK":0.10566,"BGN":0.5113},
        "2017":{"EUR":1.0,"CZK":0.03800,"DKK":0.134433,"GBP":1.1413,"HRK":0.1340,"HUF":0.003234,"PLN":0.2349,"SEK":0.10381,"BGN":0.5113}}

#configure error logging system on debug mode (log everything)
logging.basicConfig(level=logging.DEBUG)

#####PART 1: CAP SCHEME NAME TRANSLATION 

#key.csv file contains translations between scheme name used in raw data files from Member States to appropriate master code for schemes classified by purpose
key = pd.read_csv(scheme_key_loc,dtype=np.str)

#lists all headers, corrects spacing or formatting errors by restructuring names 
key.columns = [i if not i[0:4] == "Note" else i[-2:]+" Notes" for i in key.columns]

#make dataframe scheme_df 
#extract country names in key.csv
#add data from key.csv, stack on top of each other (converting from wide to long format).
#Note that key.csv is a simplified version of the Rosetta Stone, with only columns for code and original scheme name for each country. See full Rosetta Stone file for more detail on translations and notes.   
scheme_df = pd.DataFrame(columns=["original","code"])
first = True
countries = list({i[:2] for i in key.columns[1:]})
for country in {i[:2] for i in key.columns[1:]}:
    columns = [k for k in key.columns if k[0:2] == country]
    columns.append("code")
    temp = key[columns]
    temp.columns = [i if not "original" in i else "original" for i in temp.columns]
    #add column with country code
    temp["cnt"] = country.lower()
    scheme_df = scheme_df.append(temp[["original","code","cnt"]],ignore_index=True)

#Optional line to remove spacing errors, quotation marks, unseen errors at beginning/end of text where needed
scheme_df["original"] = scheme_df["original"].str.strip(" \"'")

#generate dictionary to convert original scheme name to standardized code, remove duplicates and blank lines
scheme_dic = scheme_df.groupby(["cnt","original"],squeeze=True)["code"].first()


#function: input original scheme name, returns the master scheme name. Makes sure is string, removes any quotation marks, goes through dictionary and looks up what official scheme it corresponds to, removes messiness. 
#key error: if cannot find something, logs warning with unknown scheme, returns scheme name which was not translated. 
#converts function so it can take a vector of inputs and return a vector of outputs (each column is one vector)
def translate_scheme(cnt,scheme):
    """
    ---Input---
    [str] scheme - the scheme to be translated
    
    ---output--
    [str] master scheme - the master scheme it is translated to, returns notTranslated followed by the scheme if it was unable to translate scheme
    """
    try:
        if scheme == np.nan:
            return "notTranslated:"
        scheme = str(scheme)
        #remove line to not strip punctuation at beginning and end
        scheme = scheme.strip("\"' ")
        return str(scheme_dic[cnt.lower(),scheme])
    except KeyError:
        #logging.warning("unknown scheme: {}".format(scheme))
        return "notTranslated:"+scheme
    except ValueError:
        #logging.warning("unable to translate: {}".format(scheme))
        return "notTranslated:"+scheme
    except TypeError:
        return "notTranslated:"
scheme_translate_vector = np.vectorize(translate_scheme)

#####PART TWO: POSTAL CODES 
#define global values required for translate_postcode method
last_country = "" #variable to store the name of the last country loaded into the nuts dataframe (used to avoid unnecessary reloading)
nuts_df = pd.DataFrame() #nuts dataframe variable storing a mapping for the current country postcodes to the local nuts codes

#DEFINE REGULAR EXPRESSIONS FOR COUNTRY-SPECIFIC POSTAL CODE PATTERNS

#compile all regular expression matches to increase speed:
#some countries have multiple conventions for encoding postal codes. the following defines variables based on string pattern matching.  
pattern = re.compile("^[A-Za-z][A-Za-z]-([0-9])+")
nl_pattern1 = re.compile("^[0-9]{4} ?[A-Za-z]{2}")
nl_pattern2 = re.compile("^[0-9]{3,4}$")
mt_pattern1 = re.compile("^[a-zA-z]{3}[0-9]{0,4}$")
lu_pattern1 = re.compile("[0-9]+")
be_pattern1 = re.compile("BE[0-9][0-9][0-9]")
gb_pattern1 = re.compile("[A-Za-z][0-9]{1,2}")
gb_pattern2 = re.compile("[A-Za-z]{2}[0-9]{1,2}")
sk_pattern1 = re.compile("^[0-9]{4}$")
sk_pattern2 = re.compile("^[0-9]{5}$")

#define method for translation of postcodes (takes in postal code and country, returns NUTS region code)
def translate_postcode(code,country):
    """
    ---input---
    [str] code - country postalcode
    [str] country - 2-letter country code for origin of postcode
    ---output--
    [str] Nuts3 code for the location of the country code
    """
    global last_country,nuts_df
    code = str(code)
    #formatting of postal codes:
    #test for starting with country code
    if pattern.match(code):  #contains country code (ie, starts with two capital letters followed by a row of numbers):
        country = code[0:2] #if yes, change country to the code at start of string
        code = code[3:]  #then remove country letters at start of string

    #lower case country code:
    country = country.lower()

    #format all postcodes into standard format for lookup process, using the RegEx patterns defined above to check if string matches given expression 
    if country == "es":
        #code = "".join(["0" if i < 5 - len(code) else code[i-len(code)-1] for i in range(5)])
        code = code[0:2]
    elif country == "nl" :
        if nl_pattern1.match(code) or nl_pattern2.match(code):
            code = code[0:3]
    elif country == "mt":
        if mt_pattern1.match(code):
            code = code[0:3]
    elif country == "lu":
        if lu_pattern1.match(code):
            code = "L-"+code
    elif country == "be":
        if be_pattern1.match(code):
            return code
    elif country == "gb":
        if gb_pattern1.match(code):
            code = code[0]
        elif gb_pattern2.match(code):
            code=code[0:2]
    elif country == "cy":
        return "CY000"
    elif country == "sk":
        if sk_pattern1.match(code):
            code = "0"+code
        if sk_pattern2.match(code):
            code = code[:3]+" "+code[3:]


    #load appropriate mapping of postal codes to NUTS
    #load new NUTS translation if previous country is different
    #folder nuts_folder contains all files downloaded from Eurostat listing postcode and NUTS3 
    country = country.lower()
    if  last_country != country:
        nuts_file = glob(nuts_folder+"/pc*_"+country+"_*")
        if len(nuts_file)>1:
            logging.warning("More than one possible nuts file found, taking first:\n",nuts_file)
        elif len(nuts_file)==1:
            nuts_file = nuts_file[0]
            nuts_df = pd.read_csv(nuts_file,sep=";",dtype={"CODE":np.str})
            last_country = country
        else:
            logging.warning("unable to find nuts file for country code:{}".format(country))
            return country.upper()+"nan" #This applies eg to 3 codes in the US
        
        #format countries that require adjustment for correct processing (pt, nl, gb, es)
        if country == "pt":
            t = nuts_df["CODE"].str[:4]
            nuts_df = nuts_df.assign(CODE=t)
            nuts_df.drop_duplicates(subset="CODE",inplace=True)
        elif country == "nl" or country == "mt":
            t = nuts_df["CODE"].str[0:3]
            nuts_df = nuts_df.assign(CODE=t)
            nuts_df.drop_duplicates(subset="CODE",inplace=True)
        elif country == "gb" or country == "es":
            t = nuts_df["CODE"].str[0:2]
            nuts_df = nuts_df.assign(CODE=t)
            nuts_df.drop_duplicates(subset="CODE",inplace=True)

        #use postal code to index NUTS regions, specified for current country
        nuts_df.set_index("CODE",inplace=True)
            
    #determine NUTS code for given postal code, give "NaN" if not found
    try:
        return nuts_df.loc[code,"NUTS_3"]
    except KeyError:
        #logging.warning("unable to locate {} for country {}".format(code,country))
        
        return country.upper()+"NaN"
#vectorize to apply over entire column of data 
postcode_translate_vector = np.vectorize(translate_postcode)

#### PART THREE: CURRENCY CONVERSION TO EUROS
#Method to look up conversion rate for current currency, make a new column with the appropriate conversion rate, multiply the original amount by the appropriate conversion
def get_conversion_rate(currency,year,rate_dictionary):
    """
---input---
[str] currency - the currency to convert from
[int] year - the year of the conversion
[dic] rate dictionary - the rate dictionary to use
"""
    #try to look up the conversion rate in the dictionary for the specific year, if not found then log a warning and assume conversion rate is in euro
    try:
        return rate_dictionary[str(year)][currency]
    except KeyError:
        logging.warning("unknown conversion rate for currency: {}".format(currency))
        return 1

#vectorise method to apply on entire column of data
get_conversion_rate_vector = np.vectorize(get_conversion_rate)



input_files = glob(input_folder+"/*")#list all files in input 
for in_file in input_files:
    logging.info("started file: {}".format(in_file))#log which file is being used
    
    skiplines=[] #list to store all the lines that are redundant
    with open(in_file,"r") as lines:
        header = lines.readline().strip() #get the first line in the file
        for i,line in enumerate(lines): #loop through remaining lines 
            line = line.strip()
            if line == header: #if line is the same as the first add its line number to the lines that need to be skipped (this prevents errors)
                skiplines.append(i+1)
    if len(skiplines)>0:
        logging.warning(f"skipped {len(skiplines)} lines in {in_file} ")

    #load in file
    df = pd.read_csv(in_file,skiprows=skiplines,dtype={"amount":np.float32,"recipient_postcode":np.str,"country":np.str,"scheme":np.str,"scheme_2":np.str})

    #remove 2013-2014 from lv to avoid double counting
    if "lv_2014_2015" in in_file:
        logging.info(f"removing 2013-2014 schemes from {in_file}")
        df = df[df["scheme"]!="2013-2014"]


    #match NUTS
    nuts = None #nuts column var
    cnt = None #country column global var
    try:
        cnt = df["country"] #try to get country column, if that fails (i.e. does not exist) get country for file name
    except KeyError:
        cnt = np.array([in_file[6:8] for i in range(df.shape[0])])#some files do not list a country column, in this case take the country name from input filename 
        logging.warning("file: {} contains no country column".format(in_file)) #log a warning about this
    
    try:
        nuts = postcode_translate_vector(df["recipient_postcode"],cnt) #take vector of recipient postal code, give vector for country, generate vector for NUTS

    except KeyError:
        nuts = np.array([i+"NaN" for i in cnt]) #add NUTS vector to end of table 
    df = df.assign(NUTS_3 = nuts)


    #match scheme
    try:
        cnt = np.array([in_file[6:8] for i in range(df.shape[0])])
        scheme = scheme_translate_vector(cnt,df["scheme"])
        df = df.assign(translated_scheme=scheme)#assign to new column, translated schemes

    except KeyError:
	#since Romania in 2014-2015 file has called the scheme column scheme_2 check if we are in that file and then use that instead
        if "ro_2014_15.csv" in in_file:
            logging.info("file contains scheme_2 instead of scheme, change name accordingly...")
            scheme = scheme_translate_vector("ro",df["scheme_2"])
            df = df.assign(translated_scheme=scheme)
        else:
            scheme = np.array(["missing_data" for i in range(df.shape[0])])
            df = df.assign(translated_scheme=scheme)
            logging.warning("unable to locate scheme in {}".format(in_file))
    
    #add year column if missing to ensure accurate currency conversion and file compression. This assumes filenames are always formatted with year starting on 9th character and running until the end of the filename, until the last 4 characters ".csv"  
    if not "year" in df.columns:
        year = np.array([in_file[9:-4] for i in range(df.shape[0])])
        df = df.assign(year=year)

    #convert currency using conversion rates. Note data for Poland 2015 is hard-coded here because it did not declare a currency, but was determined to be reported in zloty by comparison with reported EU data:
    convert_rate = None
    try:
        convert_rate = get_conversion_rate_vector(df["currency"],df["year"],conversion_rate_to_euro) #generate vector of conversion rates 
    except KeyError:#if no currency column detected, set conversion to 1 (this assumes value given is already in Euros)
        if "pl_2015.csv" in in_file:
            convert_rate = conversion_rate_to_euro["2015"]["PLN"]
        else:
            convert_rate = 1
        logging.warning("file: {} contains no currency column".format(in_file))
    amount_in_euro = df["amount"] *convert_rate  #termwise multiplication of 2 vectors, 1 for original amount and 1 for conversion rate to Euros
    df = df.assign(amount_EURO = amount_in_euro) #assign this vector to main data 

    #save new dataframe to outputs
    df.to_csv(output_folder+"/"+in_file[6:-4]+"_translated.csv",sep=",",index=False)
 #output file that now contains new columns with NUTS, scheme and Euros

####PART FIVE: COMPRESS DATA ACROSS NUTS AND SCHEMES ####
#once the above is complete for all countries, finalize raw data format to condensed data for analysis 

#load in output files, focus on columns
input_files = glob(output_folder+"/*_translated.csv") #find files that have been translated to have data we want 
condensed_data = pd.DataFrame() #make an empty dataframe to hold condensed data 

logging.info("started condensing files") #tell user file condensing is underway! 

for in_file in input_files:
    #load in output file only consider columns : year, NUTS_3, translated_scheme, and amount_EURO
    df = pd.read_csv(in_file,error_bad_lines=False,usecols=["year","NUTS_3","translated_scheme","amount_EURO"])
    #condense data by summing up all entries which have the same year,nuts and scheme:
    df = df.groupby(["year","NUTS_3","translated_scheme"]).sum().reset_index()
    #add condensed data to a master df:
    condensed_data = condensed_data.append(df)

#determine all years present:
logging.info("starting saving condensed tables")
for year in  {i for i in condensed_data["year"]}:
    
    #mask according to year
    msk = condensed_data["year"] == year

    #get relevant data
    year_data = condensed_data[msk].drop(columns="year")
    
    #pivot table opperation 
    output = pd.pivot_table(year_data,values="amount_EURO", index=["translated_scheme"],columns=["NUTS_3"], aggfunc=np.sum)

    #save the final version of the output
    output.to_csv(output_folder+"condensed_"+str(year)+".csv",index=True)

#ALL DONE :)
