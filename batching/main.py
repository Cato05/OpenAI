import openai
from dotenv import load_dotenv
import os

#Loading .env file
def configure():
    load_dotenv()

def main():
    configure()
    #Creating client
    client = openai.OpenAI(api_key=os.getenv("apiKey"))
    batchInputFile = os.getenv("batchInputFileID")

    client.batches.create(
        input_file_id = batchInputFile,
        endpoint = "/v1/chat/completions",
        completion_window = "24h",
        metadata ={
            "description":"nightly eval job"
        }
    )

main()