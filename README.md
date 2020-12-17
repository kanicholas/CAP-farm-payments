# CAP-farm-payments

## How to use code
1. Setup the folder structure as described below
2. Download the desired countries and there years from https://data.farmsubsidy.org/latest/ and extract the downloaded files into the input forlder
3. Download the required files from this repository and add them into the folder structure
4. Run 'translate_condense.py'
5. If desired, run either or all for the other codes in any desired order. All final outputs will be placed into 'root'

## folder structure
```
root
├── input
│   └── [input files go here]
├── output
│   └── [intermediary files will appear here]
├── key [can be downloaded here]
│   └── nuts
│       └── [nuts - postcode translation files]
├── key.csv
├── translate_condense.py
├── error_list.py
├── error_percentages.py
├── money_movement.py
├── totals.py
└── [Condensed outputs will appear here]
```
##### NOTE:
Folders and the 'key.csv' names need to be kept as stated above for the code to work. Furthermore, the NUTS filenames should not change.

## translate_condense.py
This code translates all of the input files scheme into a standard code accross all of our files. This is stored in the 'output' folder. It then condenses according to scheme and NUTS region for every year and outputs the condensed files into the 'root' folder.

## error_list.py
Analyses the intermediate files from 'translate_condense.py' in the 'output' folder and ouputs a list of schemes that were not matched. Note that in the output .csv the headers need to be transposed.

## error_percentages.py
Analyses the intermediate files from 'translate_condense.py' in the 'output' folder and gives the percentages of money in each country that scheme and NUTS could not be matched.

## money_movement.py
Analyses the intermediate files from 'translate_condense.py' in the 'output' folder and list how much money was moved from one country to another.
##### NOTE:
Each entry appears twice here: once for sending and once for receiving.

## totals.py
Lists the total money within each country for each year.
