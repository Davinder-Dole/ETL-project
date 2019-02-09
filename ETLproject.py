#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import json
import ast
import csv
from sqlalchemy import create_engine
import sqlalchemy


# ### Connect to local database

# In[2]:


rds_connection_string = "root:root@127.0.0.1/movie_db"
engine = create_engine(f'mysql://{rds_connection_string}')


# # Defining Functions

# In[3]:


def clean(x):
        if hasattr(x, '__iter__'):
            return ''.join([i if 32 < ord(i) < 128 else " " for i in x])
        else:
            return x


# # Movies Metadata

# importing the csv file & creating the DataFrame

# In[4]:


csv_file = "movies_dataset/movies_metadata.csv"
df = open(csv_file,encoding="utf-8")
reader=csv.DictReader(df)
movies_metadata_df =(pd.DataFrame(list(reader)))
movies_metadata_df.count()
movies_metadata_df=movies_metadata_df.applymap(clean)
movies_metadata_df.head()
movies_metadata_df.count()


# In[ ]:


#clean the dataFrame & removing unwanted columns
new_movies_metadata_df=movies_metadata_df[['id','imdb_id','budget','adult','original_language','original_title','title','overview','popularity','release_date','revenue','runtime','status','tagline','video','vote_average','vote_count']]
new_movies_metadata_df=new_movies_metadata_df.rename(columns={'id':'tmdbid'})
new_movies_metadata_df=new_movies_metadata_df.drop_duplicates(subset="tmdbid")
new_movies_metadata_df.count()


# In[ ]:


#create "movies" table in MySQl 
new_movies_metadata_df.to_sql(name='movies', con=engine, if_exists='replace',index=False)


# In[ ]:


#Assign primary key to "tmdbid" & delete bad rows
with engine.begin() as conn:
    conn.execute('delete from movies where tmdbid=1997 or tmdbid=2012 or tmdbid=2014')
    conn.execute('ALTER TABLE  movies MODIFY tmdbid varchar(20) primary key')


# # Credits 

# In[ ]:


csv_file = "movies_dataset/credits.csv"
df = open(csv_file,encoding="utf-8")
reader=csv.DictReader(df)
credits_df=pd.DataFrame(list(reader))
print(credits_df.count())
credits_df.head()


# # Cast

# In[ ]:


# convert "cast" dictionary to List
cast=[]
for index,row in credits_df.iterrows():
    temp_cast=ast.literal_eval(row['cast'])
    for c in temp_cast:
        c['tmdbid']=row['id']
    cast.extend(temp_cast)  


# In[ ]:


cast_df=pd.DataFrame(cast)
print(cast_df.count())
cast_df.head()


# In[ ]:


new_cast_df=cast_df[['cast_id','character','credit_id','gender','id','tmdbid','name','order','profile_path']].copy()
new_cast_df=new_cast_df.drop_duplicates(subset="credit_id")
new_cast_df=new_cast_df.applymap(clean)
new_cast_df.head()


# In[ ]:


new_cast_df.to_sql(name='cast', con=engine, if_exists='replace',index=True)


# In[ ]:


#Assign primary key to "credit_id" & foreign key to "tmdb" references to table "movies"
with engine.begin() as conn:
    conn.execute('ALTER TABLE cast MODIFY credit_id varchar(50) primary key')
    conn.execute('delete from cast where tmdbid not in (select tmdbid from movies)')
    conn.execute('ALTER TABLE cast modify tmdbid varchar(20), ADD FOREIGN KEY (tmdbid) REFERENCES movies(tmdbid)')


# In[ ]:


pd.read_sql_query('select * from cast', con=engine)


# # Crew

# In[ ]:


# convert "cast" dictionary to List
crew=[]
for index,row in credits_df.iterrows():
    temp_crew=ast.literal_eval(row['crew'])
    for c in temp_crew:
        c['tmdbid']=row['id']
    crew.extend(temp_crew)  


# In[ ]:


crew_df=pd.DataFrame(crew)
print(crew_df.count())
crew_df.head()


# In[ ]:


crew_df=crew_df.drop_duplicates(subset="credit_id")
crew_df=crew_df.applymap(clean)
crew_df.count()
crew_df.head()


# In[ ]:


crew_df.to_sql(name='crew', con=engine, if_exists='replace',index=False)


# In[ ]:


#Assign primary key to "credit_id" & foreign key to "tmdb" references to table "movies"
with engine.begin() as conn:
    conn.execute('delete from crew where tmdbid not in (select tmdbid from movies)')
    conn.execute('ALTER TABLE crew MODIFY credit_id varchar(50) primary key')
    conn.execute('ALTER TABLE crew modify tmdbid varchar(20), ADD FOREIGN KEY (tmdbid) REFERENCES movies(tmdbid)')


# # Keywords

# In[5]:


csv_file = "movies_dataset/keywords.csv"
keywords_df = pd.read_csv(csv_file)
print(keywords_df.count())
keywords_df.head()


# In[6]:


# convert "keyword" dictionary to List
keyword=[]
for index,row in keywords_df.iterrows():
    temp_word=ast.literal_eval(row['keywords'])
    for c in temp_word:
        c['tmdbid']=row['id']
    keyword.extend(temp_word) 


# In[7]:


keyword_df=pd.DataFrame(keyword)
keyword_df=keyword_df.rename(columns={'id':'keyword_id'})
keyword_df=keyword_df.applymap(clean)
print(keyword_df.count())
keyword_df.head()


# ### defining unique keywords in database

# In[33]:


unique_keyword_df=keyword_df.drop_duplicates(subset="keyword_id")
unique_keyword_df=unique_keyword_df[['keyword_id','name']]
unique_keyword_df=unique_keyword_df.applymap(clean)
unique_keyword_df.head()


# In[17]:


unique_keyword_df.to_sql(name='unique_keywords', con=engine, if_exists='replace',index=False)


# In[18]:


with engine.begin() as conn:
    conn.execute('ALTER TABLE unique_keywords MODIFY keyword_id double primary key')


# ### Keywords used for movies

# In[19]:


keyword_df.head(10000).to_sql(name='keywords_for_movies', con=engine, if_exists='replace',index=False)


# In[21]:


with engine.begin() as conn:
    conn.execute('ALTER TABLE keywords_for_movies MODIFY keyword_id double, ADD FOREIGN KEY (keyword_id) REFERENCES unique_keywords(keyword_id)')
    conn.execute('ALTER TABLE keywords_for_movies modify tmdbid varchar(20), ADD FOREIGN KEY (tmdbid) REFERENCES movies(tmdbid)')


# # Movies Metadata- Genres

# In[22]:


genres=[]
for index,row in movies_metadata_df.iterrows():
    temp_genres=ast.literal_eval(row['genres'])
    for c in temp_genres:
        c['tmdbid']=row['id']
    genres.extend(temp_genres)  


# In[23]:


genres_df=pd.DataFrame(genres)
new_genres_df=genres_df.drop_duplicates(subset="id")
new_genres_df=new_genres_df[['id','name']]
new_genres_df=new_genres_df.applymap(clean)
genres_df.head()


# In[24]:


new_genres_df.head(10000).to_sql(name='unique_genres', con=engine, if_exists='replace',index=False)
with engine.begin() as conn:
    conn.execute('ALTER TABLE unique_genres MODIFY id double primary key')


# In[27]:


genres_df.to_sql(name='genres_for_movies', con=engine, if_exists='replace',index=False)
with engine.begin() as conn:
    conn.execute('ALTER TABLE genres_for_movies MODIFY id double, ADD FOREIGN KEY (id) REFERENCES unique_genres(id)')
   # conn.execute('ALTER TABLE genres_for_movies modify tmdbid varchar(20), ADD FOREIGN KEY (tmdbid) REFERENCES movies(tmdbid)')


# # Links

# In[28]:


csv_file = "movies_dataset/links.csv"
df = open(csv_file,encoding="utf-8")
reader=csv.DictReader(df)
links_df=pd.DataFrame(list(reader))
print(links_df.count())


# In[34]:


links_df.to_sql(name='id_link', con=engine, if_exists='replace',index=False)


# assigning primary key to movieID column

# In[38]:


with engine.begin() as conn:
    conn.execute('delete from id_link where tmdbID not in (select tmdbid from movies)')
    conn.execute('ALTER TABLE id_link MODIFY movieID varchar(20) primary key')
    conn.execute('ALTER TABLE id_link modify tmdbID varchar(20), ADD FOREIGN KEY (tmdbID) REFERENCES movies(tmdbid)')


# # Ratings

# In[4]:


csv_file = "movies_dataset/ratings.csv"
ratings_df = pd.read_csv(csv_file)
print(ratings_df.count())


# In[15]:


rating_df=ratings_df.head(1000)
rating_df=rating_df.sort_values(by=['movieId'],ascending=True)
rating_df.head()


# In[16]:


rating_df.to_sql(name='rating', con=engine, if_exists='replace',index=False)


# In[18]:


with engine.begin() as conn:
    conn.execute('ALTER TABLE rating modify movieId varchar(20), ADD FOREIGN KEY (movieId) REFERENCES id_link(movieId)')


# In[ ]:




