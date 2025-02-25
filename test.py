from langchain_mistralai import ChatMistralAI

# Your API Key
api_key = "use your own api key"

# Initialize the model
llm = ChatMistralAI(model_name="mistral-tiny", api_key=api_key)

# # Test prompt
# test_prompt = "Hello! tell me about this model?"

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