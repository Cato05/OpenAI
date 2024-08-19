import openai
from dotenv import load_dotenv
import pandas as pd
import json
import os
import time

#Loading .env file
load_dotenv()

#Variables
datasetPath = "./data/IMDB top 1000.csv"
df = pd.read_csv(datasetPath)
df.head()
#Creating client
client = openai.OpenAI(api_key=os.getenv("apiKey"))
#Creating system prompt
system = '''Your goal is to extract every movie from the given dataset and categorise them by these terms:
    1.: The format must be a json object, like this: {
    categories: ['category1', 'category2', 'category3'],
    summary: '1-sentence summary'
        }
    2.: For categories choose the most relevant genres and don't give more than 4 categorie to a movie.
    3.: Summerise the movie's description into a one sentence summary'''

#Getting the Json Object of the movies
def getGenres(description):
    #Creating chat completion
    response = client.chat.completions.create(
        #Specifing model
        model="gpt-4o-mini",
        temperature=0.1,
        #Ensuring that the output will be a jsonObject
        response_format={
            "type" : "json_object"
        },
        #Technically telling the "AI" what to do
        messages=[
            {"role" : "system", "content" : system},
            {"role" : "user", "content" : description}
        ]
    )
    #Selecting the most possible choice
    return response.choices[0].message.content

#In case I want to delete the input.jsonl file
def deleteInputFile():
    with open("./input.jsonl", "w") as file:
        file.write("")

#Main program
def main():
    #Looping thorugh the csv and getting the description and the title of the movies, so the program can work with it
    for _, row in df[:5].iterrows():
        #Getting the description of the movie from the csv
        description = row['Description']
        #Getting the title of the movie from the csv
        title = row['Title']
        #Getting the JsonObject that we need
        result = getGenres(description)
        #Printing so we know it didn't mess up something
        print(f"TITLE: {title}\nOVERVIEW: {description}\n\nRESULT: {result}")
        print("\n\n----------------------------\n\n")

#Creating the batch

    #Creating tasks list for the batches
    tasks = []

    #Looping through the csv file and creating
    for index, row in df.iterrows():
        #Getting the description of the movie
        description = row["Description"]
        #Creating a single task
        task = {
            #Creating an ID for every individual task
            "custom_id" : f"task-{index}",
            #Specifing the method
            "method" : "POST",
            #Specifing the url (must be the same as endpoint)
            "url" : "/v1/chat/completions",
            #The same as chat completion
            #Telling the "AI" what to do
            "body" : {
                "model" : "gpt-4o-mini",
                "temperature" : 0.1,
                "response_format" : {
                    "type" : "json_object"
                },
            "messages" :[ 
                {"role" : "system", "content" : system},
                {"role" : "user", "content" : description}
                ],
             },
        }
    #Appending one task to the tasks list
    tasks.append(task)

    #Creating a file to see everything went fine until now
    fileName = "data/batchedMovies.jsonl"
    with open(fileName, "w") as file:
        for obj in tasks:
            file.write(json.dumps(obj) + "\n")

    #Creating batchfile
    batchFile = client.files.create(
        file=open(fileName, "rb"),
        purpose = "batch"
    )

    #Creating the batch itself
    batchJob = client.batches.create(
        #Giving the batchFile's ID
        input_file_id=batchFile.id,
        #Specifing the end point
        endpoint="/v1/chat/completions",
        #Specifing the completion window
        completion_window="24h"
    )
    #Checking batch status
    while batchJob.status not in ["failed", "completed", "cancelled", "expired"]:
        print(f"Current status is: {batchJob.status}\n Checkin' again in 3 seconds....................")
        time.sleep(3)
        batchJob = client.batches.retrieve(batchJob.id)
    #Just to go for sure printing out the output file's ID
    print(batchJob.output_file_id)
    #Creating a variable for the output file's ID
    resultFileId =batchJob.output_file_id
    #Checking if there is an output file ID (ran into some headaching errors while writing this code)
    if not resultFileId:
        return print("Result file fucked up")
    
    #Getting the output file's content, the result of the batch
    result = client.files.content(resultFileId).content

    #Specifing the file's name which we will save the results in
    resultFileName = "./data/results.jsonl"

    #Writing into that file
    with open(resultFileName, "wb") as file:
        file.write(result)
    
    #Creating a list for all the results
    results = []

    #Getting some of the results into the console
    with open(resultFileName, "r") as file:
        #Looping through every line in the file
        for line in file:
            #Creating a variable for the JsonObject which is in the results file
            jsonObject = json.loads(line.strip())
            #Appending that very result to the results list
            results.append(jsonObject)

    #Looping thorugh the results 5 times
    for res in results[:5]:
        #Getting the ID
        taskId = res["custom_id"]
        #Getting the index by splitting the given string, specified at line 77
        index = taskId.split("-")[-1]
        #Getting the result's body
        result= res['response']['body']['choices'][0]['message']['content']
        #Getting the movie that is next
        movie = df.iloc[int(index)]
        #Getting the movie's description
        description = movie["Description"]
        #Getting the movie's title
        title = movie["Title"]
        #Printing out the data we got from the results file
        print(f"TITLE: {title}\nOVERVIEW: {description}\n\nRESULT: {result}")
        print("\n\n----------------------------\n\n")








#Description
#We want a program to classify every movie from the dataset
#Format: json
#Syntax: {
#    categories: ['category1', 'category2', 'category3'],
#    summary: '1-sentence summary'
#        } 

main()