from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import pandas as pd
import time
from tqdm import tqdm
from easydict import EasyDict

import API_youtube_func as UDF

#=========================================

FILE_NAME = "kakao_0816_2_"

keys = pd.read_csv("./API_KEY.txt")

keys = list(keys)

print("================================")
print("API_KEY_LIST")
print(keys)
print("================================")

def generator(lst):
    yield lst[0]
    yield lst[1]
    yield lst[2]
    yield lst[3]
    yield lst[4]
    yield lst[5]
    yield lst[6]
    yield lst[7]
    yield lst[8]
    yield lst[9]
    yield "DONE"

key_gen = generator(keys)
print("CREAT ITERATOR")

key = next(key_gen)
print(f"Currunt API_KEY is {key}")




####나중에는 직접 지정할 수 있게 만들기
date_param = ['2022-06-14']



from datetime import datetime
from dateutil.relativedelta import relativedelta
st_list = []
end_list = []


for d in date_param:
    date_time_str = str(d) #기준점
    tt = 3 #몇개월 전후?
    date_time_obj = datetime.strptime(date_time_str, '%Y-%m-%d')

    before = date_time_obj - relativedelta(months=tt) # 개월 전
    after = date_time_obj + relativedelta(months=tt) # 개월 후

    #크롤링 시작 날짜 & 끝나는 날짜 정의
    start = str(before)[:10]+'T00:00:00Z'
    end_ = str(after)[:10]+'T00:00:00Z'
    
    st_list.append(start)
    end_list.append(end_)


pagetoken = ''
vid_list = []
vtitle_list = []
chtitle_list = []
vidtime_list = []
dic = {}
#st = '2022-01-01T00:00:00Z'
#end = '2022-01-20T00:00:00Z'

q_list = ['카카오', '카카오모빌리티']
for q in q_list:
    for st, end in zip(st_list, end_list):
        args = EasyDict({"max_results":100, "query":q, "st": st, "end": end})
        print(args.query)
        while True:
            resp = UDF.youtube_search_keyword(args, pagetoken, DEVELOPER_KEY = key)
            npt, v_id, v_title, ch_title, time_, view, like, comcnt = UDF.vid_process(resp)
            vid_list.extend(v_id)
            vtitle_list.extend(v_title)
            chtitle_list.extend(ch_title)
            vidtime_list.extend(time_)
            pagetoken = npt
            if npt == '':
                break
            

viewcnt, likecnt, comcnt = UDF.video_info_collect(vid_list, DEVELOPER_KEY = key)


print("Collect Video Info")

df = pd.DataFrame(
    zip(vid_list, vtitle_list, chtitle_list, vidtime_list, viewcnt, likecnt, comcnt), 
    columns=['videoid','title','channelname', 'time','view','video_like','commentcnt']
)
print(f"SAMPLE OF VIDEO INFO DATA")
print(df.head(10))
print(df.shape)

def to_int(x):
    try:
        x = int(x)
    except:
        print('error')
        x = int(0)
    return x

df.view  = df.view.apply(lambda x : to_int(x))
df.video_like  = df.video_like.apply(lambda x : to_int(x))
df.commentcnt  = df.commentcnt.apply(lambda x : to_int(x))


channel_title = '+'.join(set(chtitle_list[1:]))
df.to_csv(f"../data/{FILE_NAME}video_info.csv")

print(f"DATA SAVED ; length of data is {df.shape}")
print(f"SAVED AS ../data/{FILE_NAME}video_info.csv")

vid_list = df['videoid']

v_dict = {}
for vid, vtitle in zip(df['videoid'], df['title']):
    v_dict[vid] = vtitle


vid_list_c = []
comment_list = []
c_time_list = []
c_id_list = []
reply_list = []
like_list = []
ori_rep_list = []

ec_t = 0



print("START COLLECTING COMMENTS")
for v in tqdm(vid_list):
    print(v_dict[v])
    pagetoken = ''
    try:
        while True:
            try:
                resp = UDF.commentThread(v, pagetoken, DEVELOPER_KEY=key)
            except:
                key = next(key_gen)
                print(f"Change API key to {key}")
                if key == 'DONE':
                    break
                else:
                    resp = UDF.commentThread(v, pagetoken, DEVELOPER_KEY=key)
            npt, videoid, comment, c_time, reply, c_id, like, ori_rep, ec = UDF.cid_process(resp)
            vid_list_c.extend(videoid)
            comment_list.extend(comment)
            c_time_list.extend(c_time)
            c_id_list.extend(c_id)
            reply_list.extend(reply)
            like_list.extend(like)
            ori_rep_list.extend(ori_rep)
            pagetoken = npt
            ec_t += ec
            if npt == 'LAST_PAGE':
                print('last page')
                break
    except:
        print('error in ')
        print(v_dict[v])
        continue
        
print(ec_t)
        
print(f"vid_list_c : {len(vid_list_c)}")

cdf = pd.DataFrame(
    zip(vid_list_c, comment_list,c_id_list, c_time_list, reply_list, like_list, ori_rep_list), 
    columns=['videoid','comment','comment_id', 'comment_time', 'child_reply', 'like', "parent"]
)

print("Comments SAMPLE")
cdf.head(1)
print(cdf.shape)


cdf.to_csv(f"../data/{FILE_NAME}comment.csv")

print(f"CDF SAVED as../data/{FILE_NAME}comment.csv")

print("DONE")

