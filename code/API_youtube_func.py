#==================================================
#==================================================


from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser
import pandas as pd
import time
from tqdm import tqdm
from easydict import EasyDict

#====================================================
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


#======================================================
def youtube_search(options, pagetoken, DEVELOPER_KEY):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey = DEVELOPER_KEY)
    search_response = youtube.search().list(
    part="id, snippet",
    channelId=options.channelId,
    publishedAfter=options.st,
    publishedBefore=options.end,
    order = 'date',
    pageToken = pagetoken,
    maxResults=50).execute()

    return search_response


def vid_process(resp):
    v_id = []
    v_title = []
    ch_title = []
    view = []
    like = []
    comcnt = []
    time = []
    if 'nextPageToken' in resp.keys():
        npt = resp['nextPageToken']
    else:
        npt = ''
    tnum = resp['pageInfo']['totalResults']
    if tnum != 0:
        for v in resp['items']:
            if v['id']['kind'] == 'youtube#video':
                v_id.append(v['id']['videoId'])
                v_title.append(v['snippet']['title'])
                ch_title.append(v['snippet']['channelTitle'])
                time.append(v['snippet']['publishedAt'])
                #view.append(v['statistics']['viewCount'])
                #like.append(v['statistics']['likecount'])
                #comcnt.append(v['statistics']['commentCount'])
                

        return npt, v_id, v_title, ch_title, time, view, like, comcnt    
    


def video_info_collect(vid_list, DEVELOPER_KEY):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
    vid_list = [vid_list[i:i+50] for i in range(0, len(vid_list), 50)]
    
    viewcnt = []
    likecnt = []
    comcnt = []

    for v in tqdm(vid_list):
        request = youtube.videos().list(
            part= 'statistics',
            id = ','.join(v),
        ).execute()

        for i in request['items']:
            try:
                viewcnt.append(i['statistics']['viewCount'])
            except:
                viewcnt.append('none')
            try:
                likecnt.append(i['statistics']['likeCount'])
            except:
                likecnt.append('none')
            try:
                comcnt.append(i['statistics']['commentCount'])
            except:
                comcnt.append('none')
            
    return viewcnt, likecnt, comcnt




def commentThread(vid, pagetoken, DEVELOPER_KEY):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey= DEVELOPER_KEY)

    request = youtube.commentThreads().list(
        part="id, snippet, replies",
        maxResults=100,
        videoId=vid,
        pageToken =pagetoken,
        order = 'time'
    )
    cth = request.execute()

    return cth


def cid_process(resp):
    videoid = []
    comment = []
    c_time = []
    reply  = []
    c_id = []
    like = []
    ori_rep = []
    error_check = 0
    if 'nextPageToken' in resp.keys():
        npt = resp['nextPageToken']
    else:
        npt = 'LAST_PAGE'
    
    # tnum = resp['pageInfo']['totalResults']
    # pnum = resp['pageInfo']['resultsPerPage']
    for v in resp['items']:
        if v['kind'] == 'youtube#commentThread':
            videoid.append(v['snippet']['topLevelComment']['snippet']['videoId'])
            comment.append(v['snippet']['topLevelComment']['snippet']['textDisplay'])
            c_time.append(v['snippet']['topLevelComment']['snippet']['publishedAt'])
            reply.append(v['snippet']['totalReplyCount'])
            c_id.append(v['snippet']['topLevelComment']['id'])
            like.append(v['snippet']['topLevelComment']['snippet']['likeCount'])
            ori_rep.append('Parent')
            if v['snippet']['totalReplyCount'] > 0:
                try:
                    for reply_item in v['replies']['comments']:
                        r = reply_item['snippet']
                        videoid.append(v['snippet']['topLevelComment']['snippet']['videoId'])
                        comment.append(r['textDisplay'])
                        c_time.append(r['publishedAt'])
                        reply.append(0)
                        c_id.append(v['snippet']['topLevelComment']['id'])
                        like.append(r['likeCount'])
                        ori_rep.append(v['snippet']['topLevelComment']['id'])
                except:
                   error_check += 1

    return npt, videoid, comment, c_time, reply, c_id, like, ori_rep, error_check