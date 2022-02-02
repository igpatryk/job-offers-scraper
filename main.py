from time import sleep
from selenium import webdriver
import psycopg2
import logging
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from ftplib import FTP
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log_file = 'scrapper_' + str(datetime.utcnow().strftime('%Y_%m_%d')) + '.log'
logging.basicConfig(filename=log_file, encoding='utf=8', level=logging.DEBUG, format='%(asctime)s | %(levelname)s'''
                                                                                     ' | %(message)s')
logging.getLogger('matplotlib.font_manager').disabled = True


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


def process_justjoinit_data():
    avg_justjoinit = None
    warsaw_offers = scrap_justjoinit('https://justjoin.it/warszawa/python/junior?tab=with-salary')
    avg_warsaw_salary = round(get_average_salary_justjoinit(warsaw_offers), 2)
    remote_offers = scrap_justjoinit('https://justjoin.it/remote-poland/python/junior?tab=with-salary')
    avg_remote_salary = round(get_average_salary_justjoinit(remote_offers), 2)
    if avg_warsaw_salary != 0:
        logging.debug(
            "SCRAP RESULT: Today the average salary of junior python developer in Warsaw according to offers "
            "on justjoin.it is {}zł.".format(avg_warsaw_salary))
    if avg_warsaw_salary != 0:
        logging.debug(
            "SCRAP RESULT: Today the average salary of junior python developer working remotely in Poland ""ac"
            "cording to offers on ""justjoin.it is {}.zł".format(avg_remote_salary))
    if avg_warsaw_salary != 0 and avg_remote_salary != 0:
        avg_justjoinit = round(((avg_warsaw_salary + avg_remote_salary) / 2), 2)
    elif avg_warsaw_salary != 0 and avg_remote_salary == 0:
        avg_justjoinit = avg_warsaw_salary
    elif avg_warsaw_salary == 0 and avg_remote_salary != 0:
        avg_justjoinit = avg_remote_salary
    return avg_warsaw_salary, avg_remote_salary, avg_justjoinit


def insert_data(date_to_insert, warsaw_to_insert, remote_to_insert, avg_to_insert):
    conn = psycopg2.connect(
        host=os.environ.get('pg_host'),
        database=os.environ.get('pg_database'),
        user=os.environ.get('pg_user'),
        password=os.environ.get('pg_password')
    )
    try:
        logging.info("Trying to insert data to PGSQL.")
        sql = """INSERT INTO salaries.justjoinit(date, warsaw, remote, avg) VALUES (%s,%s,%s,%s);"""
        data = (date_to_insert, warsaw_to_insert, remote_to_insert, avg_to_insert)
        cur = conn.cursor()
        cur.execute(sql, data)
        conn.commit()
        logging.info("Record inserted successfully into justjoinit table.")
    except (Exception, psycopg2.Error) as error:
        logging.error(error)


def select_data(sql):
    conn = psycopg2.connect(
        host=os.environ.get('pg_host'),
        database=os.environ.get('pg_database'),
        user=os.environ.get('pg_user'),
        password=os.environ.get('pg_password')
    )
    cur = None
    try:
        query = sql
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        db_dates = []
        db_warsaw = []
        db_remote = []
        db_avg = []
        for row in rows:
            db_dates.append(row[0])
            db_warsaw.append(row[1])
            db_remote.append(row[2])
            db_avg.append(row[3])
        cur.close()
        conn.close()
        return db_dates, db_warsaw, db_remote, db_avg
    except (Exception, psycopg2.Error) as error:
        logging.error(error)
    finally:
        if conn:
            cur.close()
            conn.close()
            logging.info("Closed PGSQL Connection.")


def make_graph(dates_for_graph, warsaw_for_graph, remote_for_graph, avg_for_graph):
    x = np.arange(len(dates_for_graph))
    width = 0.2
    fig, ax = plt.subplots()
    ax.set_facecolor("white")
    ax.set_ylabel('PLN')
    ax.set_title('Junior Python Dev Salary')
    ax.set_xticks(x, dates_for_graph)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#808080", linestyle="dashed")
    warsaw_bar = ax.bar(x - width, warsaw_for_graph, width, color='#F5CABF', label='Warsaw')
    avg_bar = ax.bar(x, avg_for_graph, width, color="#C6F58E", label='Average')
    remote_bar = ax.bar(x + width, remote_for_graph, width, color="#A6B9F5", label='Remote')
    ax.legend()
    ax.bar_label(warsaw_bar, padding=3)
    ax.bar_label(avg_bar, padding=3)
    ax.bar_label(remote_bar, padding=3)
    plt.gcf().set_size_inches(18, 9)
    plt.savefig('graph.png')


def upload_to_ftp():
    ftp = FTP(os.environ.get('ftp_address'))
    ftp.login(user=os.environ.get('ftp_user'), passwd=os.environ.get('ftp_password'))
    ftp.cwd('/patryk/wp-content/uploads/2021/12')
    ftp.encoding = "utf-8"
    with open('graph.png', 'rb') as file:
        ftp.storbinary('STOR graph.png', file)
    ftp.quit()


def create_report(report_remote, report_warsaw, report_avg, monthly):
    mail_from = os.environ.get('smtp_mail')
    mail_to = os.environ.get('my_mail')
    daily_subject = "Daily salaries-scrapper's report"
    daily_body = "Hi! It's me, salaries-scrapper.\n" \
                 "Today:\n" \
                 "- the average salary of Junior Python Developer who works in Warsaw is {}zł.\n" \
                 "- the average salary of Junior Python Developer who works remotely is {}zł.\n" \
                 "- the average of these salaries is {}zł.\n" \
                 "This data was scrapped from justjoin.it website.\n" \
                 "There is a graph for the last 7 days in the attachment, take a look!"\
        .format(report_warsaw, report_remote, report_avg)
    monthly_subject = "Monthly salaries-scrapper's report"
    monthly_body = "Hi! It's me, salaries-scrapper.\n" \
                   "In the previous month:\n" \
                   "- the average salary of Junior Python Developer who works in Warsaw was {}zł.\n" \
                   "- the average salary of Junior Python Developer who works remotely was {}zł.\n" \
                   "- the average of these salaries was {}zł.\n" \
                   "This data was scrapped from justjoin.it website.\n" \
                   "There is a graph for the last one month in the attachment, take a look!"\
        .format(report_warsaw, report_remote, report_avg)
    message = MIMEMultipart()
    message["From"] = mail_from
    message["To"] = mail_to
    if monthly == 0:
        message["Subject"] = daily_subject
        message.attach(MIMEText(daily_body, "plain"))
    else:
        message["Subject"] = monthly_subject
        message.attach(MIMEText(monthly_body, "plain"))
    with open('graph.png', 'rb') as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= graph.png",
    )
    message.attach(part)
    text = message.as_string()
    return text


def send_mail(msg):
    try:
        receiver_mail = os.environ.get('my_mail')
        smtp_mail = os.environ.get('smtp_mail')
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_password = os.environ.get('smtp_password')
        logging.info("Trying to send an email.")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_mail, smtp_password)
            server.sendmail(smtp_mail, receiver_mail, msg)
            server.quit()
    except Exception as e:
        logging.error(e)
    else:
        logging.info("Successfully send an email.")


logging.info("Started job-offers-scrapper.")
# get salaries
avg_warsaw_jjit_salary, avg_remotepl_jjit_salary, avg_overall_jjit_salary = process_justjoinit_data()
# insert salaries into pgsql database with today's date
insert_data(datetime.today().strftime('%Y-%m-%d'), avg_warsaw_jjit_salary,
            avg_remotepl_jjit_salary, avg_overall_jjit_salary)
# select data from pgsql database for latest 7 days
select = "SELECT DISTINCT * from salaries.justjoinit where date >= now() - interval '7' day order by date ASC"
dates, warsaw, remote, avg = select_data(select)
# make a graph
make_graph(dates, warsaw, remote, avg)
# upload file to the ftp
upload_to_ftp()
# create daily report
mail = create_report(avg_remotepl_jjit_salary, avg_warsaw_jjit_salary, avg_overall_jjit_salary, 0)
# send daily report
send_mail(mail)
# monthly report
if datetime.today().strftime('%d') == '01':
    select = "SELECT DISTINCT * from salaries.justjoinit where date >= now() - interval '1 months' order by date ASC"
    dates, warsaw, remote, avg = select_data(select)
    make_graph(dates, warsaw, remote, avg)
    monthly_remote_avg = round((sum(remote) / len(remote)), 2)
    monthly_warsaw_avg = round((sum(warsaw) / len(warsaw)), 2)
    monthly_avg = round((sum(avg) / len(avg)), 2)
    mail = create_report(monthly_remote_avg, monthly_warsaw_avg, monthly_avg, 1)
    send_mail(mail)
logging.info("Stopped job-offers-scrapper.")
