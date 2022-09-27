import Youtube_crawling_func as YC
import pandas as pd
from tqdm import tqdm
import datetime


keys = pd.read_csv("./API_KEY.txt")
keys = list(keys)
def generator(keys):
    for i in keys:
        yield i
    yield "DONE"

key_gen = generator(keys)
key = next(key_gen)
key = next(key_gen)
print(f"Start wiht {key}")

total = pd.DataFrame()

#시작 날짜
st = '2022-09-01T00:00:00Z'
filename_st = st

for d in tqdm(range(31)):
    dt_st = datetime.datetime.strptime(st, '%Y-%m-%dT%H:%M:%SZ')
    dt_end = dt_st + datetime.timedelta(days = 1)
    end = datetime.datetime.strftime(dt_end, '%Y-%m-%dT%H:%M:%SZ')
    print(f'{st} ~ {end}')
    options = YC.EasyDict({'channelId':'UCcQTRi69dsVYHN3exePtZ1A', "order": 'viewCount', "publishedAfter": st, "publishedBefore": end})

    try:
        df, v_id_list = YC.video_info(options, key)
        cdf = YC.comment(v_id_list, key)
        capdf = YC.captions(v_id_list , df['cap'].to_list())
    except:
        print(f"API key change   {key} ---->")
        key = next(key_gen)
        print(f"---------------->{key}")
        if key == "DONE":
            break
        else:
            print('try with new key')
            df, v_id_list = YC.video_info(options, key)
            cdf = YC.comment(v_id_list, key)
            capdf = YC.captions(v_id_list , df['cap'].to_list())

    finally:
        day = pd.merge(df,cdf, how='left', on='video_id')
        day = pd.merge(day,capdf, how='left', on='video_id')
        total = pd.concat([total, day], axis = 0)
        print(f"day : {day.shape[0]} // total : {total.shape[0]}")
        st = end



total = total.reset_index(drop = True)
total.to_pickle(f"../data/KBS_{filename_st[:10]}_{end[:10]}.pkl")