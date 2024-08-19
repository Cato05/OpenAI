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
    for _, row in df[:5].iterrows():
        description = row['Description']
        title = row['Title']
        result = getGenres(description)
        print(f"TITLE: {title}\nOVERVIEW: {description}\n\nRESULT: {result}")
        print("\n\n----------------------------\n\n")
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
    batch_job = client.batches.retrieve(batchJob.id)
    print(batch_job)
    resultFileId = batch_job.error_file_id or batch_job.output_file_id
    result = client.files.content(resultFileId).content

    resultFileName = "./data/results.jsonl"

    with open(resultFileName, "wb") as file:
        file.write(result)
    
    results = []

    with open(resultFileName, "r") as file:
        for line in file:
            jsonObject = json.loads(line.strip())
            results.append(jsonObject)

    for res in results[:5]:
        taskId = res["custom_id"]
        index = taskId.split("-")[-1]
        result= res["response"]["body"]['choices']["0"]["message"]["content"]
        movie = df.iloc[int(index)]
        description = movie["Description"]
        title = movie["Title"]
        print(f"TITLE: {title}\nOVERVIEW: {description}\n\nRESULT: {result}")
        print("\n\n----------------------------\n\n")







#Description
#We want a program to classify every from the dataset
#Format: json
#Syntax: {
#    categories: ['category1', 'category2', 'category3'],
#    summary: '1-sentence summary'
#        } 

main()