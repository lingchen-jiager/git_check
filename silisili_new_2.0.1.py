import urllib.request
import re
import easygui
import requests
import urllib.parse
import os
import time
import sys
import queue
import threading
import post_practice


dizhi=[]
anime_name=[]
url=post_practice.url_needed_first
headers=("User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36")
opener = urllib.request.build_opener()
opener.addheaders=[headers]
data = opener.open(url).read().decode()
# print(data)
shaixuan="/play/.*</em></a></li>"

result1=re.compile(shaixuan).findall(data)

# print(result1)
for i in result1:
    dizhi.append('http://www.silisili.me' + i.split('" target')[0])
    anime_name.append(i.split('</span>')[1].strip("</em></a></li>"))
print(anime_name)

# hebing=dict(zip(anime_name,dizhi))
# print(dizhi)               #silisili播放页的地址

jishu = easygui.enterbox("下载第几集")
jishu = int(jishu)



zhenshijishu = jishu - 1
url=dizhi[zhenshijishu]
req=urllib.request.Request(url)
req.add_header("User-Agent","Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36")
data=urllib.request.urlopen(req).read().decode()
# print(data)

zhengze="<iframe src=\".*frameborder=\"0\""
result = re.compile(zhengze).findall(data)
new_url = result[0].split("\"")[1]
print(new_url)




file_name = anime_name[zhenshijishu]       #下面urlretrie中用到了，文件名称
new_url = new_url

# ****************************************************************************?



threadListSize = 48
queueSize = 96

_exitFlag = 0
_ts_total = 0
_count = 0
_dir=''
_videoName=''
_queueLock = threading.Lock()
_workQueue = queue.Queue(queueSize)
_threadList=[]
for i in range(threadListSize):
    _threadList.append("Thread-"+str(i))
# threadList = ["Thread-1", "Thread-2", "Thread-3"]

class downloadThread (threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
    def run(self):
        # print ("开启线程：" + self.name + '\n', end='')
        download_data(self.q)
        # print ("退出线程：" + self.name + '\n', end='')

# 下载数据
def download_data(q):
    while not _exitFlag:
        _queueLock.acquire()
        if not _workQueue.empty():
            data = q.get()
            _queueLock.release()
            # print ("%s 使用了 %s" % (threadName, data) + '\n', end='')
            url = data
            retry = 3
            while retry:
                try:
                    r = session.get(url, timeout=20)
                    if r.ok:
                        file_name = url.split('/')[-1].split('?')[0]
                        # print(file_name)
                        with open(os.path.join(_dir, file_name), 'wb') as f:
                            f.write(r.content)
                        _queueLock.acquire()
                        global _count
                        _count = _count+1
                        show_progress(_count/_ts_total)
                        _queueLock.release()
                        break
                except Exception as e:
                    print(e)
                    retry -= 1
            if retry == 0 :
                print('[FAIL]%s' % url)
        else:
            _queueLock.release()


# 填充队列
def fillQueue(nameList):
    _queueLock.acquire()
    for word in nameList:
        _workQueue.put(word)
        nameList.remove(word)
        if _workQueue.full():
            break
    _queueLock.release()


def get_session( pool_connections, pool_maxsize, max_retries):
    '''构造session'''
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=pool_connections, pool_maxsize=pool_maxsize, max_retries=max_retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# 展示进度条
def show_progress(percent):
    bar_length=50
    hashes = '#' * int(percent * bar_length)
    spaces = ' ' * (bar_length - len(hashes))
    sys.stdout.write("\rPercent: [%s] %.2f%%"%(hashes + spaces, percent*100))
    sys.stdout.flush()

def start( m3u8_url, dir, videoName):
    global _dir
    global _videoName
    global _ts_total
    if dir and not os.path.isdir(dir):
        os.makedirs(dir)
    _dir=dir
    _videoName=videoName
    r = session.get(m3u8_url, timeout=10)
    if r.ok:
        body = r.content.decode("utf-8",errors="ignore")
        if body:
            ts_list=[]
            body_list=body.split('\n')
            for n in body_list:
                if n and not n.startswith("#"):
                    ts_list.append(urllib.parse.urljoin(m3u8_url, n.strip()))
            if ts_list:
                _ts_total = len(ts_list)
                print('ts的总数量为：'+str(_ts_total)+'个')
                # 下载ts文件
                print('开始下载文件')
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                res=download(ts_list)
                # res=True
                print('')
                print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                if res:
                    # 整合ts文件
                    print('\n开始整合文件')
                    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                    merge_file(ts_list)
                    print('')
                    print(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
                else:
                    print('下载失败')
    else:
        print(r.status_code)

def download(ts_list):
    threads = []
    threadID=1
    # 创建新线程
    for tName in _threadList:
        thread = downloadThread(threadID, tName, _workQueue)
        thread.start()
        threads.append(thread)
        threadID += 1
    ts_list_tem=ts_list.copy()
    fillQueue(ts_list_tem)
    # 等待队列清空
    while not _workQueue.empty():
        if _workQueue.full():
            pass
        else :
            fillQueue(ts_list_tem)
    # 通知线程是时候退出
    global _exitFlag
    _exitFlag = 1
    # 等待所有线程完成
    for t in threads:
        t.join()
    return True

# 将TS文件整合在一起
def merge_file(ts_list):
    index = 0
    outfile = ''
    global _dir
    while index < _ts_total:
        file_name = ts_list[index].split('/')[-1].split('?')[0]
        # print(file_name)
        percent = (index + 1) / _ts_total
        show_progress(percent)
        infile = open(os.path.join(_dir, file_name), 'rb')
        if not outfile:
            global _videoName
            if _videoName=='':
                videoName=file_name.split('.')[0]+'_all'
            outfile = open(os.path.join(_dir, _videoName+'.mp4'), 'wb')
        outfile.write(infile.read())
        infile.close()
        # 删除临时ts文件
        os.remove(os.path.join(_dir, file_name))
        index += 1
    if outfile:
        outfile.close()


def get_real_url( m3u8_url):
    r = session.get(m3u8_url, timeout=10)
    if r.ok:
        body = r.content.decode()
        if body:
            ts_url=''
            body_list=body.split('\n')
            for n in body_list:
                if n and not n.startswith("#"):
                    ts_url=urllib.parse.urljoin(m3u8_url, n.strip())
            if ts_url!='':
                print('真实地址为'+ts_url)
                return ts_url
    else:
        print(r.status_code)

urllist = []
dirlist=[ ]
videoNameList=[]
def main():
    urllist.append(real_m3u8)                  #这里有改动,需要的最终m3u8地址
    dirlist.append("d:/manhua/"+file_name )    #保存的文件夹
    videoNameList.append(file_name)            #文件名
    for i in range(8):
        index = str(i+1)
        print("开始下载第"+index+"个视频,url:"+urllist[i])
        url = urllist[i]
        dir = dirlist[i]
        videoName = videoNameList[i]
        real_url = get_real_url(url)
        global _exitFlag
        global _count
        _count = 0
        _exitFlag = 0
        start(real_url,dir,videoName)




# ********************************************************************************





def get(url,header):#通过真实地址前一层解析出真实地址
    res=requests.get(url,headers=header)
    result=res.content.decode("utf-8")
    # print(result)
    return result
if "m3u8" not in new_url:
    url=new_url
    header = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.119 Safari/537.36"}
    i=get(url,header)             #get函数上方有定义
    print("非m3u8资源，使用urlretrive下载，默认下载到d：/manhua文件夹")
    zhengze1=("<source src=\"http.*\"")
    real_url=re.compile(zhengze1).findall(i)
    print("如果下载失败可能是由于调用了解析接口，这种方式还未处理或者网站下架了资源")
    real_url = real_url[0].split("\"")[1]
    print(real_url)           #*****************这里是非m3u8文件的最终直链
    # video=requests.get(real_url).content
    # fp = open("d:/manhua/5.mp4", 'wb')
    # fp.write(video)
    # fp.close()
    # urllib.request.urlretrieve(real_url,"d:/manhua/"+file_name +".mp4")  #*******************暂时把下载功能取消，利用potplayer播放
    cmd = "{}"  "{}"  "{}"  "{}" "{}" "{}".format("you-get ", "-p ", "g:/potplayer/potplayermini.exe ", "\"", real_url,
                                                  "\"")
    os.system(cmd)
else:
    # print(new_url)                     #************这是真正的m3u8之前的那个网址，可以用get方法得到其中的真实网址
    real_m3u8_before = requests.get(
        new_url).text
    real_m3u8 = re.compile("var url = '.*';").findall(real_m3u8_before)[0].split("'")[1]
    print(real_m3u8)                   #**************************重要：真正的m3u8地址
    cmd = "{}"  "{}"  "{}"  "{}" "{}" "{}".format("you-get ", "-p ", "g:/potplayer/potplayermini.exe ", "\"", real_m3u8,
                                                  "\"")
    os.system(cmd)
    # if __name__ == '__main__':
    #     session = get_session(50, 50, 3)            ##########先不下载，整合potplayer在线看
    #     main()


time.sleep(10)