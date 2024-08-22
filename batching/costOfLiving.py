from dotenv import load_dotenv
import pandas
import json
import openai as Op
import os
import time

start = time.time()

load_dotenv()

client = Op.OpenAI(api_key=os.getenv("apiKey"))
systemPrompt = '''Your goal is to categorize the country based on its living indexes which are double type of numbers.
The output format must be a Json object with this form:
{
    Country: "Country's name",
    Living index: Living index,
}
'''
dataPath = "./data/Cost_of_Living_Index_by_Country_2024.csv"
ds = pandas.read_csv(dataPath)
ds.head()

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

def main():
    for _,row in ds[:10].iterrows():
        country = row["Country"]
        livingExpense = row["Cost of Living Plus Rent Index"]
        groceries = row["Groceries Index"]
        final = categorize(str(livingExpense), country)
        print(f"Country: {country},\n Living index: {livingExpense},\n Groceries: {groceries}\n Results: {final}")
        print("------------------------------------------------------------------------------")

    tasks = []

    for index, row in ds.iterrows():
        datas = str(row["Cost of Living Plus Rent Index"]) + row["Country"]

        task = {
            "custom_id" : f"No.{index}-task",
            "method" : "POST",
            "url" : "/v1/chat/completions",

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
    tasks.append(task)

    with open("./data/CategorisedCountrys.jsonl", "w") as file:
        for obj in tasks:
            file.write(json.dumps(obj) + "\n")

    batchFile = client.files.create(
        file = open("./data/CategorisedCountrys.jsonl", "rb"),
        purpose="batch"
    )

    batch = client.batches.create(
        input_file_id=batchFile.id,
        endpoint="/v1/chat/completions",
        completion_window="24h"
    )

    while batch.status not in ["completed", "failed", "cancelled", "expired"]:
        print(f"Current status: {batch.status}, reviewing in 3 seconds...")
        time.sleep(3)
        batch = client.batches.retrieve(batch.id)

    if not batch.output_file_id:
        return print("Fucked up output file")
    
    OutputFileID = batch.output_file_id

    result = client.files.content(OutputFileID).content
    rf = "data/resultFile.jsonl"
    with open(rf, "wb") as file:
        file.write(result)

    results = []

    with open(rf, "r") as file:
        for line in file:
            jsonObject = json.loads(line.strip())
            results.append(jsonObject)
    for res in results[:15]:
        taskID = res['custom_id']
        result = res['response']['body']['choices'][0]['message']['content']
        index = taskID.split('-')[0].split('.')[-1]
        region = ds.iloc[int(index)]
        country = region["Country"]
        livingExpense = region["Cost of Living Plus Rent Index"]
        groceries = region["Groceries Index"]
        print(f"Country: {country},\n Living: {livingExpense},\n Groceries: {groceries}\n FinalFormat: {result}")
        print("==============================================================================")


#Külön fájlba bekérni a batch error file contentjét

main()
end = time.time()
runtime = end-start
print(runtime)