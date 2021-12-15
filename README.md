# Salaries scrapper
Salaries scrapper is a tool that scrap Junior Python Developer salaries from job offers on polish websites and then do some magic. 🪄
## What does it do
1. Scrap salaries from polish websites.
2. Calculate the average salary for job offers in Warsaw and for remote job offers.
3. Calculate the average salary for average salaries from second step.
4. Insert date and every calculated average salary (so date + three numbers) to the PGSQL database.
5. Select data for the last 7 days from the PGSQL database.
6. Make a graph using data obtained in fifth step.
7. Upload the graph to the FTP server.
8. Create daily report and if it is run on the first day of the month it also create monthly report.
9. Send report/reports by e-mail.
## How is it run
I have build a pipeline on https://buddy.works/ and salaries scrapper is run automatically every day at 6 a.m. (UTC+1).
## Supported websites
Currently, salaries scrapper support only https://justjoin.it/ website. I think that it is the best website to find a job as a Junior Python Developer.
I am planning to add https://nofluffjobs.com/pl support but it has to wait a bit.
## Graph
The graph can be seen on the site https://www.patrykignaczak.pl/salaries-scrapper/. It looks like this:
![graph](https://user-images.githubusercontent.com/75589318/146238433-71553254-a98d-4aff-bcc2-bd0c61b81136.png)
(This one was made while testing the script so it doesn't contain data for the 7 days)
## Report
Report is send by e-mail using GMail SMTP server. It looks like this:
<img src="https://user-images.githubusercontent.com/75589318/146238850-cb15534f-4c2b-4e5c-bdca-3f951d35aad8.png" alt="drawing" width="50%" height="50%"/>

(Again, this one was made while testing the script so it doesn't contain data for the 7 days)
