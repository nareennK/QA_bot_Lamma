import requests
import gradio as gr
import json  # Importing the JSON module
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")  # Connecting to MongoDB on port 27017
db = client["qa_database"]  # Use/ create a database called 'qa_database'
collection = db["qa_collection"]  # Use/ create a collection called 'qa_collection'

# API endpoint
API_URL = "https://llm.kryptomind.net/api/generate"

# Function to generate answer by sending a POST request to the API
def generate_answer(question):
    payload = {
        "model": "llama3",
        "prompt": question,  # The question we want to ask
        "max_tokens": 100     # Limit the response length
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        # Send the POST request to the API with streaming enabled
        response = requests.post(API_URL, json=payload, headers=headers, stream=True)
        response.raise_for_status()  # Raise an exception if the request was not successful

        # Variable to store the concatenated answer
        answer = ""

        # Iterate over the response in chunks
        for chunk in response.iter_lines():
            if chunk:
                # Decode the chunk and parse it as JSON using json.loads
                decoded_chunk = chunk.decode("utf-8")
                result = json.loads(decoded_chunk)  # Parse the chunk as JSON
                text = result.get("response", "")
                answer += text  # Append the text part to the final answer

                # Check if the response is marked as complete (done=True)
                done = result.get("done", False)
                if done:
                    break  # Stop processing if the response is complete

        # Save the question-answer pair in MongoDB
        save_to_mongo(question, answer)

        return answer
    except Exception as e:
        return f"Error: {str(e)}"

# Function to save the question and answer pair in MongoDB
def save_to_mongo(question, answer):
    collection.insert_one({"question": question, "answer": answer})  # Store QA in the database
    print(f"Saved QA: {question} -> {answer}")

# Gradio interface function
def qa_bot_ui(question):
    answer = generate_answer(question)
    return answer

# Define Gradio interface for the QA bot
ui = gr.Interface(
    fn=qa_bot_ui,
    inputs=gr.Textbox(lines=2, placeholder="What is your question"),
    outputs="text",
    title="Question Answer Bot",
    description="Ask me any question, and I'll get an answer for you!"
)

# Run the Gradio app
if __name__ == "__main__":
    ui.launch(share=True)
