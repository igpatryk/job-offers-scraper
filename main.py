from requests_html import HTMLSession

session = HTMLSession()
resp = session.get("https://justjoin.it/warszawa/python/junior?tab=with-salary")
resp.html.render()
divided_by_pln = resp.html.html.split(' PLN')
list_of_salaries = []
for element in divided_by_pln:
    if element[-1]=='k':
        salary = element[-16:].split(">", 1)[1]
        list_of_salaries.append(salary)
print(list_of_salaries)
#for element in list_of_salaries:
#    x = element.split("k")[0]
#    print(str(x))
#    print(str(x).isnumeric())
