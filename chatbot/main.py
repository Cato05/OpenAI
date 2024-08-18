from openai import OpenAI
from dotenv import load_dotenv
import os
#Loading .env file
def configure():
    load_dotenv()


def main():
    configure()
    #Making a client
    client = OpenAI(api_key=os.getenv("apiKey"))

    #Creating the user input
    message = input("User: ")
    system = "You are a helpful assistent"
    #Generating answer
    while message != "":
        response = client.chat.completions.create(
            #Specifing model
            model="gpt-4o-mini",
            messages=[
            {"role" : "system", "content" : system},
            {"role": "user", "content" : message}
            ]
        )

        #Extracting the generated text from response
        generatedText = response.choices[0].message.content
        #Printing response
        print(generatedText)
        message = input("User: ")
    print("=====================================================\n End")