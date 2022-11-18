# Coded with love by @pedri0 (Pedro Arturo Flores)
"""Scrapes the CFE website for the electricity rates for each state and municipality in Mexico. Given a year"""

from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.ui import Select
import os
import json
from absl import app
from absl import flags

"""FLAGS are used to pass arguments to the script
    --URL: URL of the CFE website
    --YEAR: Year to scrape data from"""
FLAGS = flags.FLAGS
flags.DEFINE_string('YEAR', '2022', 'Year to scrape')
flags.DEFINE_string('URL', 
    'https://app.cfe.mx/Aplicaciones/CCFE/Tarifas/TarifasCRENegocio/Tarifas/GranDemandaMTH.aspx', 
    'Page to scrape')

def state_municipalities_scrape(state_number,url,month_select_name, year='2022', last_month=11):
    """Scrapes the CFE website for the electricity rates for a given state and year

    Args:
        state_number (str or int): number of the state to scrape
        url (str): URL of the CFE website
        month_select_name (str): name of the month selector (HTML attribute)
        year (str, optional): year to scrape data from. Defaults to '2022'.
    Returns:
        pd.DataFrame: Dataframe with the scraped data (concatenated tables for each municipality)
    """
    #create a empty list to store the generated dataframes
    list_of_data_municipality = []
    #create a webdriver object (it uses the microsoft edge driver)
    driver = webdriver.Edge()
    #set implicit wait time
    driver.implicitly_wait(10)
    #get the url
    driver.get(url)

    #find the year dropdown menu and select the year
    year_selection = Select(driver.find_element(By.ID,'ContentPlaceHolder1_Fecha_ddAnio'))
    year_selection.select_by_value(year)

    #find the state dropdown menu and select the given state
    state_selection = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddEstado'))
    state_selection.select_by_value(str(state_number))

    #find the municipality dropdown menu and get the options, values. Always remove the first option (it is a placeholder)
    municip_selection = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddMunicipio'))
    municip_options = [option.text for option in municip_selection.options][1:]
    municip_values = [option.get_attribute("value") for option in municip_selection.options][1:]

    #iterate over the possible values of the months
    for month in range(1,int(last_month)):
        #find the month dropdown menu and select the given month
        month_selection = Select(driver.find_element(By.ID, month_select_name))
        month_selection.select_by_value(str(month))

        #iterate over the possible values (names and indexes) of the municipalities
        for state, municip_index in zip(municip_options,municip_values):
            #find the municipality dropdown menu and select the given municipality by index
            select_mun = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddMunicipio'))
            select_mun.select_by_value(str(municip_index))

            #find the division dropdown menu and get the options, values. Always remove the first option (it is a placeholder)
            select_div = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddDivision'))
            div_options = [option.text for option in select_div.options][1:]
            div_values = [option.get_attribute("value") for option in select_div.options][1:]

            #iterate over the possible values (names and indexes) of the divisions
            for division, division_index in zip(div_options,div_values):
                #find the division dropdown menu and select the given division by index
                select_div = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddDivision'))
                select_div.select_by_value(str(division_index))
                #find the element that contains the table and convert it to a dataframe also 
                #add the state, municipality and division to the dataframe and append it to the list
                try:
                    table = driver.find_element(By.CSS_SELECTOR,"table.table.table-bordered.table-striped")
                    table_html = table.get_attribute('outerHTML')
                    tabular_data = pd.read_html(table_html)[0]
                    tabular_data.columns = ['Tarifa','Descripción','Int. Horario','Cargo','Unidades','Valor']
                    tabular_data['year'] = year
                    tabular_data['month'] = month
                    tabular_data['state'] = state
                    tabular_data['municipality'] = municip_index
                    tabular_data['division'] = division
                    tabular_data['division_value'] = division_index
                    list_of_data_municipality.append(tabular_data)
                #if the table is not found, pass
                except:
                    pass

    #close the driver
    driver.close()
    #concatenate all the dataframes in the list and return it
    scraped_data = pd.concat(list_of_data_municipality, ignore_index=True)
    return scraped_data

def save_scraped_data(data,year='2022',state='aguascalientes'):
    """Saves the scraped data in a csv file

    Args:
        data (pd.DataFrame): Dataframe with the scraped data
        year (str, optional): year of scraped data. Defaults to '2022'.
        state (str, optional): state of scraped data. Defaults to 'aguascalientes'.
    """
    #create a folder to save the data if it does not exist
    state_path = './scraped_data/'+state
    if not os.path.exists(state_path):
        os.makedirs(state_path)
    #save the data in a csv file on the folder
    data.to_csv(state_path+'/'+'scraped_data_'+year+'.csv',index=False)

def main(argv):
    """Main function to run the script

    Args:
        argv (flags.object): flags object with the arguments

    Raises:
        app.UsageError: If the arguments are not correct
    """
    #check if the arguments are correct
    if len(argv)>1:
        raise app.UsageError('Too many command-line arguments.')
    #check year argument and set the month selector name
    if FLAGS.YEAR == '2022':
        month_selector = 'ContentPlaceHolder1_Fecha2_ddMes'
        #if year is 2022, the month selector is different beacuse 2022 is the actual year (not ended yet)
        last_month = 11
    else:
        month_selector = 'ContentPlaceHolder1_MesVerano3_ddMesConsulta'
        last_month = 13
    #load the state dictionary (names and indexes)
    with open('estados_dict.json') as f:
        states = json.load(f)
    #get the state indexes as list
    states_keys = list(states.keys())
    #cut the state name to get the first n elements
    states_keys = states_keys[9:]
    #iterate over the states and scrape the data for each one
    for state_key in states_keys:
        scraped_data = state_municipalities_scrape(state_key, FLAGS.URL, month_selector, FLAGS.YEAR, last_month)
        save_scraped_data(scraped_data,year=FLAGS.YEAR,state=states[state_key])
        print('Scraped data for state: {}'.format(states[state_key]))


if __name__ == '__main__':
    app.run(main)