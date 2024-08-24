from dotenv import load_dotenv
import pandas
import json
import openai as Op
import os
import time

start = time.time()

#Loading the dotenv file
load_dotenv()

#Creating client
client = Op.OpenAI(api_key=os.getenv("apiKey"))
#Creating system prompt for the API
systemPrompt = '''Your goal is to categorize the country based on its living indexes which are double type of numbers.
The output format must be a Json object with this form:
{
    Country: "Country's name",
    Living index: Living index,
}
'''

#The path of the dataset
dataPath = "./data/Cost_of_Living_Index_by_Country_2024.csv"
#Loading the csv file
ds = pandas.read_csv(dataPath)
ds.head()

#Function for creating a json object with the API
def categorize(livingExpensePlusRent, country):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,
        response_format={
            "type" : "json_object",
        },

        messages=[
            {"role" : "system", "content" : systemPrompt},
            {"role" : "user", "content" : str(livingExpensePlusRent)+country},
        ]
    )
    return response.choices[0].message.content

#Main program
def main():
    #Looping through the first 10 datas in the csv file
    for _,row in ds[:10].iterrows():
        #Getting the country
        country = row["Country"]
        #Getting the living expense index
        livingExpense = row["Cost of Living Plus Rent Index"]
        #GEtting the froceries index
        groceries = row["Groceries Index"]
        #Creating the json object with the categorize function
        final = categorize(str(livingExpense), country)
        #Printing them out
        print(f"Country: {country},\n Living index: {livingExpense},\n Groceries: {groceries}\n Results: {final}")
        print("------------------------------------------------------------------------------")

    #Creating list for tasks
    tasks = []

    #Looping through the dataset in cause of creating the batch file
    for index, row in ds.iterrows():
        #Getting the 2 datas we need
        datas = str(row["Cost of Living Plus Rent Index"]) + row["Country"]

        #Creating a task
        task = {
            #Giving the task a custom ID
            "custom_id" : f"No.{index}-task",
            #Setting the method
            "method" : "POST",
            #Setting the URL
            "url" : "/v1/chat/completions",
            
            #The chatCompletion part
            "body" : {
                "model" : "gpt-4o-mini",
                "temperature" : 0.1,
                "response_format" : {
                    "type" : "json_object",
                    },

                "messages" : [
                    {"role" : "system", "content" : systemPrompt},
                    {"role" : "user", "content" : datas},
                ]
            }
        }
    #Adding the task to the list
    tasks.append(task)

    #Just to see if everything is okay
    with open("./data/CategorisedCountrys.jsonl", "w") as file:
        for obj in tasks:
            file.write(json.dumps(obj) + "\n")

    #Creating a batchfile
    batchFile = client.files.create(
        file = open("./data/CategorisedCountrys.jsonl", "rb"),
        purpose="batch"
    )

    #Creating the batch
    batch = client.batches.create(
        input_file_id=batchFile.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    #Checking batche's status
    while batch.status not in ["completed", "failed", "cancelled", "expired"]:
        print(f"Current status: {batch.status}, reviewing in 3 seconds...")
        time.sleep(3)
        batch = client.batches.retrieve(batch.id)

    #Just in case we didn't got an output file
    if not batch.output_file_id:
        return print("Fucked up output file")
    
    #Getting the output file's ID
    OutputFileID = batch.output_file_id

    #Getting the content of the output file a.k.a the results
    result = client.files.content(OutputFileID).content
    #Creating a file to store some results
    rf = "data/resultFile.jsonl"
    with open(rf, "wb") as file:
        file.write(result)

    #Creating results list
    results = []

    #Reading the result file
    with open(rf, "r") as file:
        for line in file:
            jsonObject = json.loads(line.strip())
            results.append(jsonObject)

    #Printing out some of the results
    for res in results[:15]:
        #Getting the tasks ID
        taskID = res['custom_id']
        #Gettint the response from the chatCompletion
        result = res['response']['body']['choices'][0]['message']['content']
        #Getting the index of an individual task
        index = taskID.split('-')[0].split('.')[-1]
        #Getting the element on that specific index, a.k.a. the region
        region = ds.iloc[int(index)]
        #Getting the country's name
        country = region["Country"]
        #Getting the cost of Living index
        livingExpense = region["Cost of Living Plus Rent Index"]
        #Getting the groceries index
        groceries = region["Groceries Index"]
        #Printing out the informations
        print(f"Country: {country},\n Living: {livingExpense},\n Groceries: {groceries}\n FinalFormat: {result}")
        print("==============================================================================")


#Running the program
main()
#Runtime check
end = time.time()
runtime = end-start
print(runtime)