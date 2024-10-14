import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_config
from api.routes import router
from dotenv import load_dotenv, find_dotenv

# Setting up logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

# Load envs 
load_dotenv(find_dotenv(),override=True)

# Read the value of the ENV_NODE environment variable
env_node = os.getenv("ENV_NODE", "development")  # Default to development
docs = os.getenv("DOCS", "true")  # Default to true

# Get the selected configuration based on the environment node
selected_config = get_config(env_node)

# Initialize FastAPI app
app = FastAPI(docs_url=None if docs!="true" else "/docs")

# Configure CORS
# Define CORS origins based on the environment
if os.getenv("ENV") == "production":
    origins = [
        "https://corag-backend.wittybeach-c0d983ae.northeurope.azurecontainerapps.io",  # Replace with your Azure app URL
    ]
else:
    origins = ["*"]  # Allow all origins in development

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
# Applying configuration settings to FastAPI
app.state.config = selected_config

# Setup routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=app.state.config.HOST, port=app.state.config.PORT)
