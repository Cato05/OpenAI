from openai import OpenAI
from dotenv import load_dotenv
import os

def configure():
    load_dotenv()


def main():
    configure()
    client = OpenAI(api_key=os.getenv("apiKey"))

    message = input("User: ")
    system = "You are a helpful assistent"
    while message != "":
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
            {"role" : "system", "content" : system},
            {"role": "user", "content" : message}
            ]
        )

        #Extracting the generated text from response
        generatedText = response.choices[0].message.content

        print(generatedText)
        message = input("User: ")
    print("=====================================================\n End")