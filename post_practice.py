import urllib.request
import urllib.parse
import re
import easygui
url ="http://www.silisili.me/e/search/index.php"
raw_postdata = {'show':'title','tbname':'movie','tempid':'1','keyboard':'史莱姆','button':'搜索'}         #这个是在fiddler中查看到的
raw_postdata["keyboard"]=easygui.enterbox("输入要搜索的动漫，注意字不能错哦",default="进击的巨人")
postdata=urllib.parse.urlencode(raw_postdata).encode('utf-8')
req = urllib.request.Request(url,postdata)
req.add_header("User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36")
data = urllib.request.urlopen(req).read().decode()
# print(data)           #搜索时post之后返回的数据
search_data = re.compile('<h3><a href="/anime.*</a></h3>').findall(data)
search_data_name = []
search_data_url = []
j = 0
for i in search_data:
    search_data_url.append("http://www.silisili.me/anime"+search_data[j].split("anime")[1].split('.html')[0]+ ".html")
    search_data_name.append(search_data[j].split('">')[1].split('</a><')[0])
    j+=1

name_choice=easygui.multchoicebox(msg="选择你需要的结果，注意只能选择一个哦", title='搜索结果', choices=search_data_name)  #名字显示并选择，注意这里只能选择一个
# print(name_choice)     #搜索结果中名字的列表
choice_location=search_data_name.index(name_choice[0])      #查询选择的结果在名字列表中处于第几个，然后在url列表中调用该参数
# print(choice_location)
url_needed_first = search_data_url[choice_location]
# print(url_needed_first)   #最终需要的url