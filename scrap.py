import csv
import sqlite3
import re
import os
from datetime import datetime

# CONFIG
CSV_FILE = "riyasewana_cars.csv"
DB_FILE = "database.db"
TABLE_NAME = "cars_cleaned"
LOG_DIR = "logs"

# Browser Setup

# All links Collect
   #next page link
#Car Scrape 
  #Title
  #Price
  #Year
  #Mileage
  #Make
  #Model
  #Gear
  #Fuel Type
  #Engine (cc)
  #Condition
  #Ad Date

#CSV file save
