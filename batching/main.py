import openai
from dotenv import load_dotenv
import pandas as pd
import json
import os

#Loading .env file
load_dotenv()

#Variables
datasetPath = "./data/IMDB top 1000.csv"
df = pd.read_csv(datasetPath)
df.head()
#Creating client
client = openai.OpenAI(api_key=os.getenv("apiKey"))
system = '''Your goal is to extract every movie from the given dataset and categorise them by these terms:
    1.: The format must be a json object, like this: {
    categories: ['category1', 'category2', 'category3'],
    summary: '1-sentence summary'
        }
    2.: For categories choose the most relevant genres and don't give more than 4 categorie to a movie.
    3.: Summerise the movie's description into a one sentence summary'''


def getGenres(description):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,
        response_format={
            "type" : "json_object"
        },
        messages=[
            {"role" : "system", "content" : system},
            {"role" : "user", "content" : description}
        ]
    )
    return response.choices[0].message.content



def main():
    for _,row in df[:5].iterrows():
        description = row['Description']
        title = row['Title']
        result = getGenres(description)
        print(f"Title \t Overview \t Result \t")
        print("====================================")
        print(f"{title} \n {description} \n {result}")












#Description
#We want a program to classify every from the dataset
#Format: json
#Syntax: {
#    categories: ['category1', 'category2', 'category3'],
#    summary: '1-sentence summary'
#        } 

main()