from foundry_local_sdk import FoundryLocalManager, Configuration
model_alias = "phi-3.5-mini"

# 1. Start Foundry Local Manager
config = Configuration(app_name="local-rag-assistant")
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance

# 2. Start Foundry Local Web Service
manager.start_web_service()

# 3. Find the model we want
model = manager.catalog.get_model(model_alias)

# 4. If the model is not downloaded, download it
print("Model downloading (it might take a while on the first run)...")
model.download()

# 5. Upload the model into memory
print("Model loading...")
model.load()

# 6. Get the chat client
client = model.get_chat_client()

# 7. Ask a question
messages = [
    {"role": "user", "content": "Hello, who are you?"}
]

response = client.complete_chat(messages)
print(response.choices[0].message.content)