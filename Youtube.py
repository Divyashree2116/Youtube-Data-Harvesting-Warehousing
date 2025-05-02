from googleapiclient.discovery import build
import pymongo
import psycopg2
import pandas as pd
import streamlit as st


#API key connection
def Api_connect():
    Api_Id = "AIzaSyCxCqQ38-abyWfZUXiFW1-kEvYefq6XEvY"
    
    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name,api_version,developerKey=Api_Id)
    return youtube
youtube = Api_connect()


def get_Channel_info(Channel_id):
    request = youtube.channels().list(
                    part = "snippet,ContentDetails,statistics",
                    id = Channel_id
    )
    response = request.execute()

    for i in response['items']:
        data = dict(Channel_Name=i["snippet"]["title"],
                    Channel_id = i["id"],
                    Subscribers = i["statistics"]["subscriberCount"],
                    Views = i["statistics"]["viewCount"],
                    Total_videos = i["statistics"]["videoCount"],
                    Description = i["snippet"]["description"],
                    Playlist_id = i["contentDetails"]["relatedPlaylists"]["uploads"],
                    )
        return data
    

#get video ids using function to get video ids for a particular channel we can call a funcion witha channel id
def get_videos_ids(Channel_ids):
    video_ids = []
    response = youtube.channels().list(id=Channel_ids,
                                        part="contentDetails").execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_page_token = None

    while True:
            response1 = youtube.playlistItems().list(
                                part="snippet",
                                playlistId=playlist_id,
                                maxResults=50,
                                pageToken=next_page_token).execute()
            for i in range(len(response1['items'])):
                video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
            next_page_token = response1.get('nextPageToken')
            if next_page_token is None:
                break
    return video_ids


#to getinfo about the videos we can use the video ids
def get_video_info(video_ids):
    Video_data=[]
    for Video_Id in video_ids:
        request = youtube.videos().list(
                        part = "snippet,ContentDetails,statistics",
                        id = Video_Id
        )
        video_response = request.execute()
        for i in video_response['items']:
            data = dict(Channel_Name=i["snippet"]['channelTitle'],
                        Channel_id = i["snippet"]['channelId'],
                        Video_id = i["id"],
                        Title = i["snippet"]["title"],
                        Tags = i["snippet"].get("tags"),
                        Thumbnail = i["snippet"]["thumbnails"]["default"]["url"],
                        Description = i["snippet"].get("description"),
                        Published_Date = i["snippet"]["publishedAt"],
                        Duration = i["contentDetails"]["duration"],
                        View_Count = i["statistics"].get("viewCount"),
                        comment_Count = i["statistics"].get("commentCount"),
                        likes = i["statistics"].get("likeCount"),
                        Favorite_Count = i["statistics"]["favoriteCount"],
                        Definition = i["contentDetails"]["definition"],
                        Caption_status = i["contentDetails"]["caption"],
                        )
            Video_data.append(data)
    return Video_data
#to call the above function


#get comment information:
#to get the comments for a particular video we can use the video id
def get_comments_info(video_ids):
    Comment_data = []
    try:
            for Video_Id in video_ids:
                request = youtube.commentThreads().list(
                    part = "snippet",
                    videoId = Video_Id,
                    maxResults = 50
                )
                comment_response = request.execute()

                for item in comment_response['items']:
                    data = dict(Comment = item["snippet"]["topLevelComment"]["id"],
                                Videoid = item['snippet']['topLevelComment']['snippet']['videoId'],
                                Comment_Text = item['snippet']['topLevelComment']['snippet']['textDisplay'],
                                Comment_author = item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                                Comment_Published = item['snippet']['topLevelComment']['snippet']['publishedAt']
                                )               
                    Comment_data.append(data)
    except:
        pass 
    return Comment_data
#to call the above function


def get_playlist_details(Channel_IDs):
    next_page_token = None
    Playlist_data = []
    while True:                                                     
        request = youtube.playlists().list(
                                        part = "snippet,ContentDetails",
                                        channelId = Channel_IDs,
                                        maxResults = 50,
                                        pageToken = next_page_token
                        )
        Playlist_response = request.execute()

        for item in Playlist_response['items']:
                            data = dict(Playlist_id = item["id"],
                                        Playlist_Title = item["snippet"]["title"],
                                        Channel_id = item["snippet"]["channelId"],
                                        Channel_Name = item["snippet"]["channelTitle"],
                                        Published_at= item["snippet"]["publishedAt"],
                                        Video_count = item["contentDetails"]["itemCount"]
                                        )
                            Playlist_data.append(data)
        next_page_token = Playlist_response.get('nextPageToken')
        if next_page_token is None:
            break
    return Playlist_data


# MongoDB connection string
mongo_connection_string = "mongodb+srv://divyashreedhanapathy:beAZNMM9YzUKa4aF@cluster0.800zg58.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = pymongo.MongoClient("mongodb+srv://divyashreedhanapathy:beAZNMM9YzUKa4aF@cluster0.800zg58.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tlsAllowInvalidCertificates=True")
db = client["Youtube_data"]

def channel_details(channel_id):
    ch_details = get_Channel_info(channel_id)
    pl_details = get_playlist_details(channel_id)
    vi_ids = get_videos_ids(channel_id)
    vi_details = get_video_info(vi_ids)
    com_details = get_comments_info(vi_ids)

    coll1 = db["channel_details"]
    coll1.insert_one({"channel_information": ch_details,"playlist_information": pl_details,
                      "video_information": vi_details,"comment_information": com_details})
    
    return "upload completed successfully"
       


#Table creation for channels,playlists,videos,comments:

def channels_table(channel_name_s):
    mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Divya@2004",
        database="youtube_data",
        port="5432")
    cursor = mydb.cursor()


    create_query= '''create table if not exists channels(
                                Channel_Name varchar(100),
                                Channel_id varchar(100) primary key,
                                Subscribers bigint,
                                Views bigint,
                                Total_videos int,
                                Description text,
                                Playlist_id varchar(100) 
                            )'''    
    cursor.execute(create_query)
    mydb.commit()


    single_channel_details=[]
    db=client["Youtube_data"]
    coll1 = db['channel_details']
    for ch_data in coll1.find({"channel_information.Channel_Name":channel_name_s},{"_id":0}):
        single_channel_details.append(ch_data["channel_information"])
    df_single_channel_details = pd.DataFrame(single_channel_details)

    for index, row in df_single_channel_details.iterrows():
        insert_query = """insert into channels(Channel_Name,
                                Channel_id,
                                Subscribers,
                                Views,
                                Total_videos,
                                Description,
                                Playlist_id) 
                            values(%s,%s,%s,%s,%s,%s,%s)"""
        values = (row['Channel_Name'],
                    row['Channel_id'],
                    row['Subscribers'],
                    row['Views'],
                    row['Total_videos'],
                    row['Description'],
                    row['Playlist_id'])

    try:
            cursor.execute(insert_query, values)
            mydb.commit()
        
    except:
            news = f"Your Provided Channel Name {channel_name_s} is already exists"
    return news



def playlists_table(channel_name_s):
    mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Divya@2004",
        database="youtube_data",
        port="5432")
    cursor = mydb.cursor()


    create_query= '''create table if not exists playlists(
                        Playlist_id varchar(100) primary key,
                        Playlist_Title varchar(100),
                        Channel_id varchar(100),
                        Channel_Name varchar(100),
                        Published_at timestamp,
                        Video_count int 
                    )'''    

    cursor.execute(create_query)
    mydb.commit() 

    single_playlists_details=[]
    db=client["Youtube_data"]
    coll1 = db['channel_details']
    for ch_data in coll1.find({"channel_information.Channel_Name": channel_name_s},{"_id":0}):
         single_playlists_details.append(ch_data["playlist_information"])
    df_single_playlists_details = pd.DataFrame(single_playlists_details[0])


    for index, row in df_single_playlists_details.iterrows():
            insert_query = """insert into playlists( Playlist_id,
                                    Playlist_Title,
                                    Channel_id ,
                                    Channel_Name,
                                    Published_at,
                                    Video_count) 
                                values(%s,%s,%s,%s,%s,%s)"""
            
            values = (row['Playlist_id'],
                        row['Playlist_Title'],
                        row['Channel_id'],
                        row['Channel_Name'],
                        row['Published_at'],
                        row['Video_count'])
        
            cursor.execute(insert_query, values)
            mydb.commit()


def Videos_table(channel_name_s):
    mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Divya@2004",
        database="youtube_data",
        port="5432")
    cursor = mydb.cursor()


    create_query= '''create table if not exists Videos(
                        Channel_Name varchar(100),
                        Channel_id varchar(100),
                        Video_id varchar(150)primary key,
                        Title varchar(100),
                        Tags text,
                        Thumbnail varchar(300),
                        Description text,
                        Published_Date timestamp,
                        Duration interval,
                        View_Count bigint,
                        comment_Count int,
                        likes bigint,
                        Favorite_Count int,
                        Definition varchar(100),
                        Caption_status varchar(100)
                    )'''    

    cursor.execute(create_query)
    mydb.commit() 

    single_Video_details=[]
    db=client["Youtube_data"]
    coll1 = db['channel_details']
    for ch_data in coll1.find({"channel_information.Channel_Name":channel_name_s},{"_id":0}):
         single_Video_details.append(ch_data["video_information"])
    df_single_Videos_details = pd.DataFrame(single_Video_details[0])

    for index, row in df_single_Videos_details.iterrows():
            insert_query = """insert into Videos( Channel_Name,
                        Channel_id,
                        Video_id,
                        Title,
                        Tags,
                        Thumbnail,
                        Description,
                        Published_Date,
                        Duration,
                        View_Count,
                        comment_Count,
                        likes,
                        Favorite_Count,
                        Definition,
                        Caption_status)
                    values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""" 
            

            values = (row['Channel_Name'],
                        row[ 'Channel_id'],
                        row['Video_id'],
                        row['Title'],
                        row['Tags'],
                        row['Thumbnail'],
                        row['Description'],
                        row['Published_Date'],
                        row['Duration'],
                        row['View_Count'],
                        row['comment_Count'],
                        row['likes'],
                        row['Favorite_Count'],
                        row['Definition'],
                        row['Caption_status'])
        
            cursor.execute(insert_query, values)
            mydb.commit()



def comments_table(channel_name_s):
    mydb = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="Divya@2004",
        database="youtube_data",
        port="5432")
    cursor = mydb.cursor()

    create_query= '''create table if not exists comments(
                                    Comment varchar(500) primary key,
                                    Videoid varchar(100),
                                    Comment_Text text,
                                    Comment_author varchar(150),
                                    Comment_Published timestamp
                    )'''
                                
    cursor.execute(create_query)
    mydb.commit() 

    single_comments_details=[]
    db=client["Youtube_data"]
    coll1 = db['channel_details']
    for ch_data in coll1.find({"channel_information.Channel_Name":channel_name_s},{"_id":0}):
         single_comments_details.append(ch_data["comment_information"])
    df_single_comments_details = pd.DataFrame(single_comments_details[0])
    

    for index, row in df_single_comments_details.iterrows():
            insert_query = """insert into comments(Comment,
                                Videoid,
                                Comment_Text,
                                Comment_author,
                                Comment_Published) 
                            values(%s,%s,%s,%s,%s)""" 
            
            values = (row['Comment'],
                        row['Videoid'],
                        row['Comment_Text'],
                        row['Comment_author'],
                        row['Comment_Published'])
        
            cursor.execute(insert_query, values)
            mydb.commit()
    #close the connection


def tables(single_channel):

    news = channels_table(single_channel)
    if news:
         return news
    
    else:
        playlists_table(single_channel)
        Videos_table(single_channel)
        comments_table(single_channel)

        return "All tables created successfully"


def show_channels_table():
    ch_list = []
    db=client["Youtube_data"]
    coll1 = db['channel_details']
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_list.append(ch_data["channel_information"])
    df = st.dataframe(ch_list)

    return df

def show_playlists_table():
    pl_list = []
    db=client["Youtube_data"]
    coll1 = db['channel_details']
    for pl_data in coll1.find({},{"_id":0,"playlist_information":1}):
        for i in range(len(pl_data["playlist_information"])):
            pl_list.append(pl_data["playlist_information"][i])
    df1 = st.dataframe(pl_list)

    return df1


def show_Videos_table():
    vi_list = []
    db=client["Youtube_data"]
    coll1 = db['channel_details']
    for vi_data in coll1.find({},{"_id":0,"video_information":1}):
        for i in range(len(vi_data["video_information"])):
            vi_list.append(vi_data["video_information"][i])
    df2 = st.dataframe(vi_list)

    return df2


def show_comments_table():
    com_list = []
    db=client["Youtube_data"]
    coll1 = db['channel_details']
    for com_data in coll1.find({},{"_id":0,"comment_information":1}):
        for i in range(len(com_data["comment_information"])):
                    com_list.append(com_data["comment_information"][i])
    df3 = st.dataframe(com_list)

    return df3


#streamlit code
with st.sidebar:
    st.title(":red[YOUTUBE DATA HARVESTING AND WAREHOUSING]")
    st.header("Skill Take Away")
    st.caption("Python Scripting")
    st.caption("Data collection")
    st.caption("API Integration")
    st.caption("MongoDB")
    st.caption("Data Management using Mongodb and Sql")

channel_id = st.text_input("Enter the Channel ID")
if st.button("collect and store data"):
    ch_ids = []
    db=client["Youtube_data"]
    coll1 = db['channel_details']
    for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        ch_ids.append(ch_data["channel_information"]["Channel_id"])

    if channel_id in ch_ids:
        st.success("Channel Details of the given channel id is already exists")
    
    else:
        insert = channel_details(channel_id)
        st.success(insert)

all_channels = []
db=client["Youtube_data"]    
coll1 = db['channel_details']
for ch_data in coll1.find({},{"_id":0,"channel_information":1}):
        all_channels.append(ch_data["channel_information"]["Channel_Name"])

unique_channel = st.selectbox("Select the Channel",all_channels)

if st.button("Migrate to sql"):
        Tables = tables(unique_channel)
        st.success(Tables)

show_table = st.radio("SELECT THE TABLE FOR VIEW",("CHANNELS","PLAYLISTS","VIDEOS","COMMENTS"))

if show_table == "CHANNELS":
     show_channels_table()

if show_table == "PLAYLISTS":
     show_playlists_table()

if show_table == "VIDEOS":
     show_Videos_table()

if show_table == "COMMENTS":
     show_comments_table()

#sql connection:
mydb = psycopg2.connect(
    host="localhost",
    user="postgres",
    password="Divya@2004",
    database="youtube_data",
    port="5432")
cursor = mydb.cursor()

question = st.selectbox("Select Your Question", ("1. All the videos and the channel name",
                                               "2. channels with most number of videos",
                                               "3. 10 most viewed videos",
                                               "4. comments in each videos",
                                               "5. videos with highest likes",
                                               "6. likes of all videos",
                                               "7. views of each channel",
                                               "8. videos published in the year of 2023",
                                               "9. Average duration of all videos in each channel",
                                               "10. videos with highest number of comments"))
                                
if question == "1. All the videos and the channel name":
    query1 = '''select title as videos,channel_name as channelname from videos'''
    cursor.execute(query1)
    mydb.commit()
    t1 = cursor.fetchall()
    df=pd.DataFrame(t1,columns=["Video Title","Channel Name"])
    st.write(df)

elif question == "2. channels with most number of videos":
    query2 = '''select channel_name as channelname, total_videos as "no_of_videos" from channels
                order by total_videos desc'''
    cursor.execute(query2)
    mydb.commit()
    t2 = cursor.fetchall()
    df2=pd.DataFrame(t2,columns=["channel name","No of videos"])
    st.write(df2)

elif question == "3. 10 most viewed videos":
    query3 = '''select view_count as views, channel_name as channelname, title as videotitle from videos
                where view_count is not null order by view_count desc limit 10'''
    cursor.execute(query3)
    mydb.commit()
    t3 = cursor.fetchall()
    df3=pd.DataFrame(t3,columns=["views", "channel name", "videotitle"])
    st.write(df3)
    
elif question == "4. comments in each videos":
    query4 = '''select comment_count as no_comments, title as videotitle from videos where comment_count is not null'''
    cursor.execute(query4)
    mydb.commit()
    t4 = cursor.fetchall()
    df4 = pd.DataFrame(t4, columns=["No of Comments", "Video Title"])
    st.write(df4)
    
elif question == "5. videos with highest likes":
    query5 = '''select title as videotitle,channel_name as channelname, likes as likecount 
                    from videos where likes is not null order by likes desc'''
    cursor.execute(query5)
    mydb.commit()
    t5 = cursor.fetchall()
    df5=pd.DataFrame(t5,columns=["videotitle","channelname","likecount"])
    st.write(df5)

elif question == "6. likes of all videos":
    query6 = '''select likes as likecount,title as videotitle from videos'''
    cursor.execute(query6)
    mydb.commit()
    t6 = cursor.fetchall()
    df6=pd.DataFrame(t6,columns=["likecount","videotitle"])
    st.write(df6)

elif question == "7. views of each channel":
    query7 = '''select channel_name as channelname,views as totalviews from channels'''
    cursor.execute(query7)
    mydb.commit()
    t7 = cursor.fetchall()
    df7=pd.DataFrame(t7,columns=["channelname","totalviews"])
    st.write(df7)

elif question == "8. videos published in the year of 2023":
    query8 = '''select title as video_title,published_date as videorelease,channel_name as channelname from videos 
            where extract(year from published_date)=2024'''
    cursor.execute(query8)
    mydb.commit()
    t8 = cursor.fetchall()
    df8=pd.DataFrame(t8,columns=["videotitle","published_date","channelname"])
    st.write(df8)
    

elif question == "9. Average duration of all videos in each channel":
    query9 = '''select channel_name as channelname,AVG(duration) as averageduration from videos group by channel_name'''
    cursor.execute(query9)
    mydb.commit()
    t9 = cursor.fetchall()
    df9=pd.DataFrame(t9,columns=["channelname","averageduration"])
    df9

    T9 = []
    for index,row in df9.iterrows():
        channel_title = row["channelname"]
        average_duration = row["averageduration"]
        average_duration_str = str(average_duration)
    T9.append(dict(channeltitle=channel_title, avgduration=average_duration_str))
    df1 = pd.DataFrame(T9)

elif question == "10. videos with highest number of comments":
    query10 = '''select title as videotitle,channel_name as channelname,comment_count as comments from videos where comment_count is not null
                order by comment_count desc'''
    cursor.execute(query10)
    mydb.commit()
    t10 = cursor.fetchall()
    df10=pd.DataFrame(t10,columns=["video title","channel name","comments"])
    st.write(df10)
