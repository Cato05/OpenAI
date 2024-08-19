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

def deleteInputFile():
    with open("./input.jsonl", "w") as file:
        file.write("")


def main():
    tasks = []

    for index, row in df.iterrows():
        description = row["Description"]
        task = {
            "custom_id" : f"task-{index}",
            "method" : "POST",
            "url" : "/v1/chat/completions",
            "body" : {
                "model" : "gpt-4o-mini",
                "temperature" : "0.1",
                "response_format" : {
                    "type" : "json_object"
                },
            "messages" :[ 
                {"role" : "system", "content" : system},
                {"role" : "user", "content" : description}
                ],
             },
        }
    tasks.append(task)

    fileName = "data/batchedMovies.jsonl"
    with open(fileName, "w") as file:
        for obj in tasks:
            file.write(json.dumps(obj) + "\n")

    batchFile = client.files.create(
        file=open(fileName, "rb"),
        purpose = "batch"
    )

    batchJob = client.batches.create(
        input_file_id=batchFile.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    








#Description
#We want a program to classify every from the dataset
#Format: json
#Syntax: {
#    categories: ['category1', 'category2', 'category3'],
#    summary: '1-sentence summary'
#        } 

main()