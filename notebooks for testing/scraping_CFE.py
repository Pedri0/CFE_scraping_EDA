from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from selenium.webdriver.support.ui import Select
import os
import json


def state_municipalities_scrape(state_number,url,year='2022'):

    #webdriver.Edge(executable_path='./msedgedriver.exe')
    list_of_data_municipality = []
    driver = webdriver.Edge()
    driver.implicitly_wait(10)
    driver.get(url)

    year_selection = Select(driver.find_element(By.ID,'ContentPlaceHolder1_Fecha_ddAnio'))
    year_selection.select_by_value(year)

    state_selection = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddEstado'))
    state_selection.select_by_value(str(state_number))

    municip_selection = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddMunicipio'))
    municip_options = [option.text for option in municip_selection.options][1:]
    municip_values = [option.get_attribute("value") for option in municip_selection.options][1:]

    for month in range(1,11):
        month_selection = Select(driver.find_element(By.ID,'ContentPlaceHolder1_Fecha2_ddMes'))
        month_selection.select_by_value(str(month))

        for state, municip_index in zip(municip_options,municip_values):
            select_mun = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddMunicipio'))
            select_mun.select_by_value(str(municip_index))

            select_div = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddDivision'))
            div_options = [option.text for option in select_div.options][1:]
            div_values = [option.get_attribute("value") for option in select_div.options][1:]

            for division, division_index in zip(div_options,div_values):
                select_div = Select(driver.find_element(By.ID,'ContentPlaceHolder1_EdoMpoDiv_ddDivision'))
                select_div.select_by_value(str(division_index))
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
                except:
                    pass

    driver.close()
    scraped_data = pd.concat(list_of_data_municipality, ignore_index=True)
    return scraped_data

def save_scraped_data(data,year='2022',state='aguascalientes'):
    state_path = './scraped_data/'+state
    if not os.path.exists(state_path):
        os.makedirs(state_path)
    data.to_csv(state_path+'/'+'scraped_data_'+year+'.csv',index=False)



if __name__ == '__main__':
    URL = 'https://app.cfe.mx/Aplicaciones/CCFE/Tarifas/TarifasCRENegocio/Tarifas/GranDemandaMTH.aspx'

    with open('estados_dict.json') as f:
        states = json.load(f)

    states_keys = list(states.keys())
    states_keys = states_keys[9:]

    for state_key in states_keys:
        scraped_data = state_municipalities_scrape(state_key,URL)
        save_scraped_data(scraped_data,year='2022',state=states[state_key])
        print('Scraped data for state: {}'.format(states[state_key]))
