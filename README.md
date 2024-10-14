# RAG-Service Backend

This project serves as a backend for a Retrieval-Augmented Generation (RAG) service. It provides APIs to handle document uploads, process the uploaded data, and answer questions about the content of these documents.

## Features

- Document upload and processing
- Question-answering based on uploaded documents
- RESTful API endpoints for interaction

## Getting Started

### Prerequisites

- Python 3.12+
- PDM (Python Development Master) for dependency management
- FastAPI
- Uvicorn
- Azure Cosmos DB for storage

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rag-service-backend.git
   cd rag-service-backend
   ```

2. Install dependencies using PDM:
   ```bash
   pdm install
   ```

3. Set up environment variables:
   - Copy `.env.template` to `.env`
   - Modify the variables in `.env` as needed to configure your Azure Cosmos DB and other settings.

### Running the Server

To start the server, run:

   ```bash
   pdm run src/main.py
   ```

The server will be accessible at `http://localhost:8080` by default.

### API Endpoints

- **GET /ping**: A simple health check endpoint that returns "pong".
- **POST /upload**: Upload documents for processing.
- **GET /get-documents**: Retrieve documents associated with a given passphrase.
- **DELETE /delete-document**: Delete a specific document by passphrase and filename.
- **POST /sanitize**: Sanitize documents older than a specified date.
- **GET /ask**: Ask a question based on the uploaded documents and receive a streaming response.

### Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.


### Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the web framework.
- [Azure Cosmos DB](https://azure.microsoft.com/en-us/services/cosmos-db/) for the database service.
- [LangChain](https://langchain.readthedocs.io/en/latest/) for the document processing and question-answering capabilities.
