import os
from dotenv import load_dotenv, find_dotenv


class Config:
    DEBUG = False  # Set to True to enable debugging mode
    PORT = 5000  # Set the port you want your app to run on
    HOST = "0.0.0.0"  # Set the host IP address

class DevelopmentConfig(Config):
    load_dotenv(find_dotenv())
    
class ProductionConfig(Config):
    PORT = 8080
    DEBUG = False
    
    
# Function to get the selected configuration based on env_node
def get_config(env_node="development"):
    config_by_env_node = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
    }
    return config_by_env_node.get(env_node.lower(), DevelopmentConfig)
