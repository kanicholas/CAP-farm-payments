# CAP-farm-payments

## How to use code
1. setup the folder structure as described below
2. Download the desired countries and there years from https://data.farmsubsidy.org/latest/ and extract the downloaded files into the input forlder
3. download the required files from this repository and add them into the folder structure
4. run 'translate_condense.py'
5. if desired run either or all for the other codes in any desired order, all final outputs will be placed into 'root'

## folder structure
```
root
├── input
│   └── [input files go here]
├── output
│   └── [interediary files will appear here]
├── key [can be downloaded here]
│   └── nuts
│       └── [nuts - postcode translation files]
├── key.csv
├── translate_condense.py
├── error_percentages.py
├── money_movement.py
├── totals.py
└── [Condensed outputs will appear here]
```
##### NOTE:
folders and the 'key.csv' names need to be kept as stated above for the code to work. further more the nuts files names should not change

## translate_condense.py
this code translates all of the input files scheme into a standard code accross all of our files, this is stored in the 'output' folder, it then condense according to scheme and nuts region for every year and outputs the condensed files into the 'root' folder.

## error_percentages.py
annalyses the intermediary files from 'translate_condense.py' in the 'output' folder and gives the percentages of money in each country that scheme and nuts could not be matched

## money_movement.py
annalyses the intermediary files from 'translate_condense.py' in the 'output' folder and list how much money was moved from one country to the other.
##### NOTE:
each entery appears twice here once for sending and once for reciving

## totals.py
lists the total money within each country for each year.
