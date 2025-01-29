from langchain_mistralai import ChatMistralAI

# Your API Key
api_key = "rTZD2HoYGOZ14S80IQO1RIibXJgz6wYL"

# Initialize the model
llm = ChatMistralAI(model_name="mistral-tiny", api_key=api_key)

# # Test prompt
# test_prompt = "Hello! Can you confirm if you are responding correctly?"

# # Generate response
# try:
#     response = llm.invoke(test_prompt)
#     print("✅ ChatMistralAI Response:", response.content)
# except Exception as e:
#     print("❌ Error:", e)


while True:
    user_input = input("Enter your msg: ")
    response = llm.invoke(user_input)
    print("model response: ", response.content)