from time import sleep
from selenium import webdriver
import psycopg2
import logging
from datetime import datetime

# import matplotlib.pyplot as plt
# import numpy as np

log_file = 'scrapper_' + str(datetime.utcnow().strftime('%Y_%m_%d')) + '.log'
logging.basicConfig(filename=log_file, encoding='utf=8', level=logging.DEBUG, format='%(asctime)s | %(levelname)s'''
                                                                                     ' | %(message)s')
conn = psycopg2.connect(
    host="localhost",
    database="job-offers",
    user="postgres",
    password="password"
)


def scrap_justjoinit(link):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument("window-size=1920,1080")
    browser = webdriver.Chrome(options=options)
    browser.get(link)
    sleep(1)
    browser.execute_script("document.body.style.zoom='20%'")
    sleep(1)
    resp = browser.page_source
    # I want to check offers only in specific region, so I need to discard offers in other cities
    useful_resp = resp.split("Python</span> in other cities")[0]
    return useful_resp


def get_average_salary_justjoinit(offers):
    if 'PLN' in offers:
        offers_divided_by_pln = offers.split(" PLN")
        sum_of_salaries = 0
        counter_of_salaries = 0
        for element in offers_divided_by_pln:
            if element[-1] == "k":
                salary = element[-16:].split(">", 1)[1]
                salary2 = salary.replace("k", "")
                salary = salary2.replace(" ", "")
                salary2 = salary.replace("-", " ")
                salary = salary2.split(" ")
                sum_of_actual_salaries = 0
                for i in range(0, len(salary)):
                    sum_of_actual_salaries = sum_of_actual_salaries + float(salary[i])
                    sum_of_actual_salaries = round(sum_of_actual_salaries, 2)
                mean_of_actual_salaries = round(sum_of_actual_salaries / len(salary), 2)
                sum_of_salaries = sum_of_salaries + mean_of_actual_salaries
                counter_of_salaries = counter_of_salaries + 1
        return round(sum_of_salaries / counter_of_salaries, 2) * 1000
    else:
        return 0


def insert_data(date, warsaw, remote, avg):
    try:
        logging.info("Trying to insert data to PGSQL.")
        sql = """INSERT INTO salaries.justjoinit(date, warsaw, remote, avg) VALUES (%s,%s,%s,%s);"""
        data = (date, warsaw, remote, avg)
        cur = conn.cursor()
        cur.execute(sql, data)
        conn.commit()
        logging.info("Record inserted successfully into justjoinit table.")
    except (Exception, psycopg2.Error) as error:
        logging.error(error)
    finally:
        if conn:
            cur.close()
            conn.close()
            logging.info("Closed PGSQL Connection.")


def process_justjoinit_data():
    junior_python_dev_jobs_offers_in_warsaw = scrap_justjoinit(
        'https://justjoin.it/warszawa/python/junior?tab=with-salary')
    average_junior_python_dev_in_warsaw_salary = get_average_salary_justjoinit(junior_python_dev_jobs_offers_in_warsaw)
    junior_python_dev_jobs_offers_remote_poland = scrap_justjoinit(
        'https://justjoin.it/remote-poland/python/junior?tab=with-salary')
    average_junior_python_dev_remote_poland_salary = get_average_salary_justjoinit(
        junior_python_dev_jobs_offers_remote_poland)
    # logging.info("Got average salary of python dev working remotely in Poland: {}."
    #  .format(average_junior_python_dev_remote_poland_salary))
    if average_junior_python_dev_remote_poland_salary != 0 and average_junior_python_dev_in_warsaw_salary != 0:
        if average_junior_python_dev_remote_poland_salary > average_junior_python_dev_in_warsaw_salary:
            logging.info("SCRAP RESULT: It is better to look for offers in category 'Remote Poland'! Average salary "
                         "is {}zł more. ".format(average_junior_python_dev_remote_poland_salary
                                                 - average_junior_python_dev_in_warsaw_salary))
        else:
            logging.info("SCRAP RESULT: It is better to look for offers based in Warsaw! Average salary is {}zł more. "
                         .format(average_junior_python_dev_in_warsaw_salary
                                 - average_junior_python_dev_remote_poland_salary))
    if average_junior_python_dev_in_warsaw_salary != 0:
        logging.info("SCRAP RESULT: Today the average salary of junior python developer in Warsaw according to offers "
                     "on justjoin.it is {}zł.".format(average_junior_python_dev_in_warsaw_salary))
    if average_junior_python_dev_in_warsaw_salary != 0:
        logging.info("SCRAP RESULT: Today the average salary of junior python developer working remotely in Poland ""ac"
                     "cording to offers on ""justjoin.it is {}.zł"
                     .format(average_junior_python_dev_remote_poland_salary))
    if average_junior_python_dev_in_warsaw_salary != 0 and average_junior_python_dev_remote_poland_salary != 0:
        average_junior_python_dev_salary_on_justjoinit = (average_junior_python_dev_in_warsaw_salary +
                                                          average_junior_python_dev_remote_poland_salary) / 2
    elif average_junior_python_dev_in_warsaw_salary != 0 and average_junior_python_dev_remote_poland_salary == 0:
        average_junior_python_dev_salary_on_justjoinit = average_junior_python_dev_in_warsaw_salary
    elif average_junior_python_dev_in_warsaw_salary == 0 and average_junior_python_dev_remote_poland_salary != 0:
        average_junior_python_dev_salary_on_justjoinit = average_junior_python_dev_remote_poland_salary
    insert_data(datetime.today().strftime('%d-%m-%Y'), average_junior_python_dev_in_warsaw_salary,
                average_junior_python_dev_remote_poland_salary, average_junior_python_dev_salary_on_justjoinit)
    return average_junior_python_dev_salary_on_justjoinit


logging.info("Started job-offers-scrapper.")
average_junior_python_dev_salary_on_justjoinit = process_justjoinit_data()  # I'm looking for a job in Warsaw or for

# Let's scrap other site - nofluffjobs.com/pl! Coming soon...


# def scrap_nofluffjobs(link):
#    browser = webdriver.Chrome()
#    browser.get(link)
#    sleep(5)
#    browser.execute_script("document.body.style.zoom='20%'")
#    sleep(5)
#    resp = browser.page_source
#    return resp
