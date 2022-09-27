#==================================================
#==================================================


from apiclient.discovery import build
from apiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi
from oauth2client.tools import argparser

import pandas as pd
import time
from tqdm import tqdm
from easydict import EasyDict


#====================================================
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
#DEVELOPER_KEY = 'AIzaSyDMJBGYEes948hTgUJQ2gBebaCg7Cb_jQs'


#======================================================


def youtube_search_query(options, pagetoken , key):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey=key)

    search_response = youtube.search().list(
        part="id, snippet",
        q=options.query,
        publishedAfter=options.publishedAfter,
        publishedBefore=options.publishedBefore,
        order = 'viewCount',
        pageToken = pagetoken,
        maxResults=50
    ).execute()

    return search_response

#by channelID
def youtube_search(options, pagetoken, key):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey = key)
    search_response = youtube.search().list(
        part="id, snippet",
        channelId=options.channelId,
        publishedAfter=options.publishedAfter,
        publishedBefore=options.publishedBefore,
        order = 'viewCount',
        pageToken = pagetoken,
        maxResults=50
    ).execute()

    return search_response



def search_process(resp):
    v_id = []

    if 'nextPageToken' in resp.keys():
        npt = resp['nextPageToken']
    else:
        npt = ''
    
    tnum = resp['pageInfo']['totalResults']
    pnum = resp['pageInfo']['resultsPerPage']
    
    for v in resp['items']:
        if v['id']['kind'] == 'youtube#video':
                v_id.append(v['id']['videoId'])
            
            
    return npt, v_id



def video_info_collect(vid_list, key):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey=key)
    vid_list = [vid_list[i:i+50] for i in range(0, len(vid_list), 50)]
    
    viewcnt = []
    likecnt = []
    comcnt = []
    cap = []
    time = []
    ch_id = []
    vtitle = []
    vdescript = []
    ctitle = []

    for v in vid_list:
        request = youtube.videos().list(
            part= 'snippet, statistics, contentDetails',
            id = ','.join(v),
        ).execute()
        test =request
        for i in request['items']:
            time.append(i['snippet']['publishedAt'])
            ch_id.append(i['snippet']['channelId'])
            vtitle.append(i['snippet']['title'])
            vdescript.append(i['snippet']['description'])
            ctitle.append(i['snippet']['channelTitle'])
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
            try:
                if i['contentDetails']['caption'] == 'true':
                    cap.append('cap')
                elif i['contentDetails']['caption'] == 'false':
                    cap.append('nocap')
            except:
                cap.append('nocap')
                
    return viewcnt, likecnt, comcnt, cap, time, ch_id, vtitle, vdescript, ctitle


def commentThread(vid, pagetoken, key):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,developerKey=key)

    request = youtube.commentThreads().list(
        part="id, snippet, replies",
        maxResults=50,
        videoId=vid,
        pageToken = pagetoken,
        order = 'relevance'
    )
    cth = request.execute()

    return cth


def video_info(options, key):
    pagetoken = ''
    v_id_list = []
    
    dic = {}
    while True:
        resp = youtube_search(options, pagetoken, key)
        npt, v_id = search_process(resp)
        v_id_list.extend(v_id)
        pagetoken = npt
        
        if npt == '':
            break
        

    viewcnt, likecnt, comcnt, cap, time_list, ch_id_list, vtitle_list, vdescript_list, ctitle_list = video_info_collect(v_id_list, key)

    df = pd.DataFrame(zip(v_id_list, time_list, ch_id_list, vtitle_list, vdescript_list, ctitle_list, viewcnt, likecnt, comcnt, cap), columns=['video_id', 'time', 'channel_id', 'video_title', 'video_description', 'channel_title','view','like','commentcnt', 'cap'])

    return df, v_id_list


def cid_process(resp):
    videoid = []
    comment = []
    c_time = []
    reply  = []
    c_id = []
    c_author = []
    like = []
    ori_rep = []
    error_check = 0

    if 'nextPageToken' in resp.keys():
        npt = resp['nextPageToken']
    else:
        npt = ''
    
    tnum = resp['pageInfo']['totalResults']
    pnum = resp['pageInfo']['resultsPerPage']
    
    for v in resp['items']:
        if v['kind'] == 'youtube#commentThread':
            videoid.append(v['snippet']['topLevelComment']['snippet']['videoId'])
            comment.append(v['snippet']['topLevelComment']['snippet']['textDisplay'])
            c_time.append(v['snippet']['topLevelComment']['snippet']['publishedAt'])
            c_author.append(v['snippet']['topLevelComment']['snippet']['authorDisplayName'])
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
                        c_author.append(r['authorDisplayName'])
                        reply.append(0)
                        c_id.append(reply_item['id'])
                        like.append(r['likeCount'])
                        ori_rep.append(v['snippet']['topLevelComment']['id'])
                except:
                   error_check += 1
            
        
    return npt, videoid, comment, c_time, reply, c_id, c_author, like, ori_rep, error_check


def comment(v_id_list, key):
    pagetoken = ''
    vid_list_c = []
    comment_list = []
    c_time_list = []
    c_id_list = []
    reply_list = []
    c_author_list = []
    like_list = []
    ori_rep_list = []


    for v in v_id_list:
        try:
            while True:
                resp = commentThread(v, pagetoken, key)
                npt, videoid, comment, c_time, reply, c_id, c_author,like, ori_rep, error_check = cid_process(resp)
                vid_list_c.extend(videoid)
                comment_list.extend(comment)
                c_time_list.extend(c_time)
                c_id_list.extend(c_id)
                pagetoken = npt
                reply_list.extend(reply)
                c_author_list.extend(c_author)
                like_list.extend(like)
                ori_rep_list.extend(ori_rep)
                # if error_check > 0:
                #     print(error_check)
                if npt == '':
                    break
        except:
            continue
    
    cdf = pd.DataFrame(zip(vid_list_c, comment_list, c_id_list, reply_list, c_time_list, c_author_list, like_list, ori_rep_list), columns=['video_id','comment','comment_id', 're_reply','comment_time', 'author', 'c_like', 'ori_rep'])
    
    return cdf  

def captions(vid_list, cap):
    caption_list = []
    for v, c in zip(vid_list, cap):
        ind_cap = ''
        if c == 'cap':
            try:
                trans = YouTubeTranscriptApi.get_transcript(v, languages = ['ko'])
                for t in trans:
                    ind_cap += t['text']
                caption_list.extend([ind_cap])
            except:
                caption_list.extend(['no cap'])
                
        else:
            caption_list.extend(['no cap'])
    
    capdf = pd.DataFrame(zip(vid_list, caption_list), columns=['video_id','captiontext'])

    return capdf