#import terminals

import googleapiclient.discovery 
from googleapiclient.discovery   import build
import pandas as pd
 
import pymongo
from   pymongo import MongoClient
import psycopg2
import streamlit as st 



#Api key connection

def Api_connect():
    Api_Id="AIzaSyDDNtgyFUNKg716vRmsQ2NimzgmNl8FuOc"
    
    api_service_name="youtube"
    api_version="v3"

    youtube=build(api_service_name,api_version,developerKey= Api_Id)

    return youtube

youtube=Api_connect()




#1 get channel information(functions)
#get channel information
def get_channel_info(channel_id):
    
    request = youtube.channels().list(
                part = "snippet,ContentDetails,Statistics",
                id = channel_id
    )
    response=request.execute()
    

    
    
    for i in response['items']:
        data=dict(Channel_Name = i["snippet"]["title"],
                    Channel_Id = i["id"],
                    subscribers= i["statistics"]["subscriberCount"],
                    Views = i["statistics"]["viewCount"],
                    Total_Videos = i["statistics"]["videoCount"],
                    Channel_Description = i["snippet"]["description"],
                    Playlist_Id = i["contentDetails"]["relatedPlaylists"]["uploads"])
    return data






#2 get full video_ids
#get video ids
def get_video_ids(channel_id):
    video_ids=[]
    response=youtube.channels().list(id=channel_id, 
                                  part='contentDetails').execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    
    while True:
        response1 = youtube.playlistItems().list( 
                                           part = 'snippet',
                                           playlistId = playlist_id, 
                                           maxResults = 50,
                                           pageToken = next_page_token).execute()
        
        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = response1.get('nextPageToken')
        
        if next_page_token is None:
            break
    return video_ids





#3 get video information
def get_video_info(video_ids):
    video_data = []
    for video_id in video_ids:
        request = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id= video_id)
        response = request.execute()
        
        for item in response["items"]:
            data = dict(Channel_Name = item['snippet']['channelTitle'],
                        Channel_Id = item['snippet']['channelId'],
                        Video_Id = item['id'],
                        Title = item['snippet']['title'],
                        Tags = item['snippet'].get('tags'),
                        Thumbnail = item['snippet']['thumbnails']['default']['url'],
                        Description = item['snippet']['description'],
                        Published_Date = item['snippet']['publishedAt'],
                        Duration = item['contentDetails']['duration'],
                        Views = item['statistics']['viewCount'],
                        Likes = item['statistics'].get('likeCount'),
                        Comments = item['statistics'].get('commentCount'),
                        Favorite_Count = item['statistics']['favoriteCount'],
                        Definition = item['contentDetails']['definition'],
                        Caption_Status = item['contentDetails']['caption']
                        )
            video_data.append(data)
    return video_data








#4 All comment details:function
#get comment information
def get_comment_info(video_ids):
        Comment_data = []
        try:
                for video_id in video_ids:
                        request = youtube.commentThreads().list(
                                part = "snippet",
                                videoId = video_id,
                                maxResults = 50
                        )
                        response = request.execute()
                        
                        for item in response["items"]:
                                data = dict(
                                        Comment_Id = item["snippet"]["topLevelComment"]["id"],
                                        Video_Id = item["snippet"]["topLevelComment"]["snippet"]["videoId"],
                                        Comment_Text = item["snippet"]["topLevelComment"]["snippet"]["textOriginal"],
                                        Comment_Author = item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                                        Comment_Published = item["snippet"]["topLevelComment"]["snippet"]["publishedAt"])
                                Comment_data.append(data)
        except:
                pass
                
        return Comment_data
 







#5 get playlist ids

def get_playlist_details(channel_id):
       next_page_token=None
       All_data=[]
       while True:
              request = youtube.playlists().list(
                         part='snippet,contentDetails',
                         channelId=channel_id,
                         maxResults=50,
                         pageToken=next_page_token

                )
              response=request.execute()
               
    
    
              for item in response['items']: 
                     data=dict(Playlist_Id=item['id'],
                                Title=item['snippet']['title'],
                                Channel_Id=item['snippet']['channelId'],
                                Channel_Name=item['snippet']['channelTitle'],
                                PublishedAt=item['snippet']['publishedAt'],
                                Video_Count=item['contentDetails']['itemCount'])
                     All_data.append(data)


               
              next_page_token=response.get('nextPageToken')
              if next_page_token is None:
                     break
        
       return All_data







#upload to mongodb
client=pymongo.MongoClient("mongodb://localhost:27017")
db=client["youtube_data"]




def channel_details(channel_id):
    ch_details=get_channel_info(channel_id)
    pl_details=get_playlist_details(channel_id)
    vi_ids=get_video_ids(channel_id)
    vi_details=get_video_info(vi_ids)
    com_details=get_comment_info(vi_ids)
    
    coll1=db["channel_details"]
    coll1.insert_one({"channel_information":ch_details,"playlist_information":pl_details,"video_information":vi_details,
                     "comment_information":com_details})
    
    return "upload completed successfully"







# 1 table creation



def channels_table():
        mydb = psycopg2.connect(host="localhost",
                        user="postgres",
                        password="mukundh",
                        database= "youtube_data",
                        port = "5432"
                        )
        cursor = mydb.cursor()

        drop_query = '''drop table if exists channels'''
        cursor.execute(drop_query)
        mydb.commit()

        try:
                create_query = '''create table if not exists channels(Channel_Name varchar(100),
                                                                Channel_Id varchar(100) primary key, 
                                                                Subscribers bigint, 
                                                                Views bigint,
                                                                Total_Videos int,
                                                                Channel_Description text,
                                                                Playlist_Id varchar(80))'''
                cursor.execute(create_query)
                mydb.commit()

        except:
                print("Channels table already created")



        ch_list=[]
        db=client["youtube_data"]
        coll1=db["channel_details"]
        for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
                ch_list.append(ch_data["channel_information"])
        df=pd.DataFrame(ch_list)



        mydb = psycopg2.connect(host="localhost",
                        user="postgres",
                        password="mukundh",
                        database= "youtube_data",
                        port = "5432"
                        )
        cursor = mydb.cursor()



        for     index,row in df.iterrows():
                insert_query = '''insert into  channels(Channel_Name,
                                                Channel_Id,
                                                Subscribers,
                                                Views,
                                                Total_Videos,
                                                Channel_Description,
                                                Playlist_Id)

                                                values(%s,%s,%s,%s,%s,%s,%s)'''
                        
                values=(row['Channel_Name'],
                        row['Channel_Id'],
                        row['subscribers'],
                        row['Views'],
                        row['Total_Videos'],
                        row['Channel_Description'],
                        row['Playlist_Id'])
                
                try:
                
                        cursor.execute(insert_query,values)            
                        mydb.commit()

                except:
                        print("Channels values are already inserted")






#2 playlist Table creation

def playlist_table():
        mydb = psycopg2.connect(host="localhost",
                                        user="postgres",
                                        password="mukundh",
                                        database="youtube_data",
                                        port="5432")
        cursor=mydb.cursor()

        drop_query='''drop table if exists playlists'''
        cursor.execute(drop_query)
        mydb.commit()


        create_query='''create table if not exists playlists(Playlist_Id varchar(300) primary key,
                                                             Title varchar(200), 
                                                             Channel_Id varchar(100), 
                                                             Channel_Name varchar(100),
                                                             PublishedAt timestamp,
                                                             Video_Count int
                                                             )'''

        cursor.execute(create_query)
        mydb.commit()




        pl_list=[]
        db=client["youtube_data"]
        coll1=db["channel_details"]
        for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
          for i in range(len(pl_data["playlist_information"])):
                        pl_list.append(pl_data["playlist_information"][i])
        df1 = pd.DataFrame(pl_list)




        mydb = psycopg2.connect(host="localhost",
                                        user="postgres",
                                        password="mukundh",
                                        database="youtube_data",
                                        port = "5432")
        cursor = mydb.cursor()

                        
        for index,row in df1.iterrows():
                insert_query='''insert into playlists(Playlist_Id,
                                                      Title,
                                                      Channel_Id,
                                                      Channel_Name,
                                                      PublishedAt,
                                                      Video_Count
                                                        )

                                                        values(%s,%s,%s,%s,%s,%s)'''            
                        
                values =(row['Playlist_Id'],
                        row['Title'],
                        row['Channel_Id'],
                        row['Channel_Name'],
                        row['PublishedAt'],
                        row['Video_Count']
                                )
                                        
                                                
                cursor.execute(insert_query,values)
                mydb.commit()  




                                        


#3 videos table creation

def videos_table():
    
    mydb = psycopg2.connect(host="localhost",
                    user="postgres",
                    password="mukundh",
                    database="youtube_data",
                    port = "5432"
                    )
    cursor = mydb.cursor()
        
    drop_query = '''drop table if exists videos'''
    cursor.execute(drop_query)
    mydb.commit()

    create_query = '''create table if not exists videos(Channel_Name varchar(300),
                                                        Channel_Id varchar(300),
                                                        Video_Id varchar(100) primary key, 
                                                        Title varchar(250), 
                                                        Tags text,
                                                        Thumbnail varchar(200),
                                                        Description text, 
                                                        Published_Date timestamp,
                                                        Duration interval, 
                                                        Views bigint, 
                                                        Likes bigint,
                                                        Comments int,
                                                        Favorite_Count int, 
                                                        Definition varchar(100), 
                                                        Caption_Status varchar(100) 
                                                            )''' 
                            
    cursor.execute(create_query)             
    mydb.commit()


    vi_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
                    vi_list.append(vi_data["video_information"][i])
    df2 = pd.DataFrame(vi_list)



    mydb = psycopg2.connect(host="localhost",
                    user="postgres",
                    password="mukundh",
                    database= "youtube_data",
                    port = "5432"
                    )
    cursor = mydb.cursor()

    for index, row in df2.iterrows():
            insert_query='''insert into videos (Channel_Name,
                                                Channel_Id,
                                                Video_Id, 
                                                Title, 
                                                Tags,
                                                Thumbnail,
                                                Description, 
                                                Published_Date,
                                                Duration, 
                                                Views, 
                                                Likes,
                                                Comments,
                                                Favorite_Count, 
                                                Definition, 
                                                Caption_Status 
                                                )
                        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            
            values = (row['Channel_Name'],
                    row['Channel_Id'],
                    row['Video_Id'],
                    row['Title'],
                    row['Tags'],
                    row['Thumbnail'],
                    row['Description'],
                    row['Published_Date'],
                    row['Duration'],
                    row['Views'],
                    row['Likes'],
                    row['Comments'],
                    row['Favorite_Count'],
                    row['Definition'],
                    row['Caption_Status'])
                                
            
            cursor.execute(insert_query,values)
            mydb.commit()







        
#4.comment table creation


def comments_table():

    mydb=psycopg2.connect(host="localhost",
                        user="postgres",
                        password="mukundh",
                        database= "youtube_data",
                        port = "5432")
    cursor=mydb.cursor()



    drop_query='''drop table if exists comments'''
    cursor.execute(drop_query)
    mydb.commit()




    create_query='''create table if not exists comments(Comment_Id varchar(300) primary key,
                                                        Video_Id varchar(200),
                                                        Comment_Text text, 
                                                        Comment_Author varchar(200),
                                                        Comment_Published timestamp
                                                        )'''
    cursor.execute(create_query)
    mydb.commit()






    com_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
                    com_list.append(com_data["comment_information"][i])                                  
    df3=pd.DataFrame(com_list)






    mydb=psycopg2.connect(host="localhost",
                            user="postgres",
                            password="mukundh",
                            database= "youtube_data",
                            port = "5432")
    cursor=mydb.cursor()











    for index, row in df3.iterrows():
                insert_query = '''insert into comments (Comment_Id,
                                                        Video_Id ,
                                                        Comment_Text,
                                                        Comment_Author,
                                                        Comment_Published
                                                        )
                                                
                                                    values (%s, %s, %s, %s, %s)'''
                
                values = (
                    row['Comment_Id'],
                    row['Video_Id'],
                    row['Comment_Text'],
                    row['Comment_Author'],
                    row['Comment_Published']
                )
                
                cursor.execute(insert_query,values)
                mydb.commit()






#Tables creation(check)

def tables():
    channels_table()
    playlist_table()
    videos_table()
    comments_table()

    return "Tables Created successfully"







def show_channels_table():
    ch_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"] 
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df=st.dataframe(ch_list)
    return df
        




def show_playlists_table():
        pl_list=[]
        db=client["youtube_data"]
        coll1 =db["channel_details"]
        for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
                for i in range(len(pl_data["playlist_information"])):
                    pl_list.append(pl_data["playlist_information"][i])
        df1=st.dataframe(pl_list)
        return df1






def show_videos_table():
    vi_list=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    df2=st.dataframe(vi_list)
    return df2





def show_comments_table():
    com_list=[]
    db=client["youtube_data"]
    coll1 =db["channel_details"]
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
            com_list.append(com_data["comment_information"][i])
    df3=st.dataframe(com_list)
    return df3






#streamlit
with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("SKILL TAKE AWAY")
    st.caption('Python scripting')
    st.caption("Data Collection")
    st.caption("MongoDB")
    st.caption("API Integration")
    st.caption(" Data Managment using MongoDB and SQL")


channel_id=st.text_input("Enter the Channel id")

#channels output values

if st.button("Collect and Store data"):
    ch_ids=[]
    db=client["youtube_data"]
    coll1=db["channel_details"]
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_ids.append(ch_data["channel_information"]["Channel_Id"])

    if channel_id in ch_ids:
        st.success("Channel details of the given channel id is already exists")

    else:
        insert=channel_details(channel_id)
        st.success(insert)


if st.button("Migrate to SQL"):
    Table=tables()
    st.success(Table)
    
show_table=st.radio("select the table for view",("channels","playlists","videos","comments"))

if show_table=="channels":
    show_channels_table()
elif show_table=="playlists":
    show_playlists_table()
elif show_table=="videos":
    show_videos_table()
elif show_table=="comments":
    show_comments_table()



    


    
#SQL connection(questions and answers)

mydb = psycopg2.connect(host="localhost",
            user="postgres",
            password="mukundh",
            database= "youtube_data",
            port = "5432"
            )
cursor = mydb.cursor()
    
question = st.selectbox(
    'Please Select Your Question',
    ('1. All the videos and the Channel Name',
     '2. Channels with most number of videos',
     '3. 10 most viewed videos',
     '4. Comments in each video',
     '5. Videos with highest likes',
     '6. likes of all videos',
     '7. views of each channel',
     '8. videos published in the year 2022',
     '9. average duration of all videos in each channel',
     '10. videos with highest number of comments'))


if question=='1. All the videos and the Channel Name':
    query1='''select Title as videos, Channel_Name as ChannelName from videos'''
    cursor.execute(query1)
    mydb.commit()
    t1=cursor.fetchall()
    df=pd.DataFrame(t1, columns=["Video Title","Channel Name"])
    st.write(df)




elif question=="2. Channels with most number of videos":
    query2 ='''select Channel_Name as ChannelName,Total_Videos as no_Videos from channels order by total_Videos desc'''
    cursor.execute(query2)
    mydb.commit()
    t2=cursor.fetchall()
    df2=pd.DataFrame(t2, columns=["Channel Name","No of Videos"])
    st.write(df2)



elif question=='3. 10 most viewed videos':
    query3 = '''select Views as views , Channel_Name as ChannelName,title as videotitle from videos 
                        where Views is not null order by views desc limit 10;'''
    cursor.execute(query3)
    mydb.commit()
    t3=cursor.fetchall()
    df3=pd.DataFrame(t3,columns=["views","channel Name","videotitle"])
    st.write(df3)




elif question == '4. Comments in each video':
    query4 = '''select Comments as no_comments ,title as videotitle from videos where Comments is not null'''
    cursor.execute(query4)
    mydb.commit()
    t4=cursor.fetchall()
    df4=pd.DataFrame(t4, columns=["no_comments", "videotitle"])
    st.write(df4)



elif question == '5. Videos with highest likes':
    query5 = '''select title as videotitle, channel_name as channelname, likes as likescount from videos 
                        where likes is not null order by likes desc;'''
    cursor.execute(query5)
    mydb.commit()
    t5 = cursor.fetchall()
    df5=pd.DataFrame(t5, columns=["videotitle","channelname","likecount"])
    st.write(df5)


elif question == '6. likes of all videos':
    query6 = '''select likes as likeCount,title as videotitle from videos;'''
    cursor.execute(query6)
    mydb.commit()
    t6 = cursor.fetchall()
    df6=pd.DataFrame(t6, columns=["likecount","videotitle"])
    st.write(df6)



elif question == '7. views of each channel':
    query7 = '''select channel_name as channelname, Views as totalviews from channels'''
    cursor.execute(query7)
    mydb.commit()
    t7=cursor.fetchall()
    df7=pd.DataFrame(t7, columns=["channel name","total views"])
    st.write(df7)



elif question == '8. videos published in the year 2022':
    query8 = '''select title as video_title, Published_Date as videorelease, Channel_Name as ChannelName from videos 
                where extract(year from Published_Date) = 2022;'''
    cursor.execute(query8)
    mydb.commit()
    t8=cursor.fetchall()
    df8=pd.DataFrame(t8,columns=["Name", "Video Publised On", "ChannelName"])
    st.write(df8)



elif question == '9. average duration of all videos in each channel':
    query9='''select channel_name as Channelname, AVG(duration) as averageduration from videos group BY channel_name'''
    cursor.execute(query9)
    mydb.commit()
    t9=cursor.fetchall()
    df9=pd.DataFrame(t9, columns=["channelname", "averageduration"])

    T9=[]
    for index, row in df9.iterrows():
        channel_title=row["channelname"]
        average_duration=row["averageduration"]
        average_duration_str=str(average_duration)
        T9.append(dict(channeltitle=channel_title ,averageduration=average_duration_str))
    df9=pd.DataFrame(T9)
    st.write(df9)





elif question == '10. videos with highest number of comments':
    query10='''select title as videotitle, channel_name as channelname, comments as comments from videos 
                        where comments is not null order by comments desc'''
    cursor.execute(query10)
    mydb.commit()
    t10=cursor.fetchall()
    df10=pd.DataFrame(t10, columns=["video title", "channel name", "comments"])
    st.write(df10)


