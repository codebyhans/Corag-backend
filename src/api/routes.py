import asyncio
import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import io
import os
import aiofiles  # For async file handling
from prepare.load import Load
from prepare.split import Split
from prepare.embed import Embed
from prepare.store import Store
from prepare.retrieve import Retrieve
from prepare.llm import LLM
from langchain.schema import HumanMessage, AIMessage  # Import AIMessage
from typing import AsyncGenerator
import datetime as dt 
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, JSONResponse
from typing import AsyncGenerator, List, Dict, Any
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the router
router = APIRouter()

# Simulating a database or storage for document embeddings
document_embeddings = {}

class QuestionRequest(BaseModel):
    question: str

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    question: str
    history: Optional[List[Message]] = []

class DeleteDocumentRequest(BaseModel):
    passphrase: str
    filename: str


router = APIRouter()
logger = logging.getLogger(__name__)

# Debug endpoint
@router.get('/ping')
async def ping():
    return "pong"

# Initialize the processing classes
loader = Load()
splitter = Split()
embedder = Embed()
storage = Store()
retriever = Retrieve()
llm_answer = LLM(system_prompt=f"""
            You are an AI assistant designed to answer questions based on the provided context and nothing else. 
            Your task is to understand the user's question and generate a relevant, accurate, and helpful response using the following context and nothing else. 
            If the provided context doesn't contain enough information to answer the question fully, make sure to inform the user. 
            Maintain a friendly and helpful tone. 
            """
        )

llm_sorry = LLM(system_prompt=f"""
            You are an AI assistant that informs the user that no relevant information was found, and suggest them rephrase the question. 
            Maintain a friendly and helpful tone. Do not use introductions like "sure!" or "Definitely"" or any other type of polite introduction to your answer.
            """
            )

@router.get('/get-documents')
async def get_documents(
    passphrase: str = Query(...)
):
    """
    Retrieve documents associated with a given passphrase.

    :param passphrase: The passphrase to query documents for.
    :return: JSONResponse containing the list of documents or an error message.
    """
    try:
        storage.delete_documents_older_than(current_time=dt.datetime.now(), passphrase=passphrase)
        documents = storage.get_documents(passphrase)
        if documents:
            return JSONResponse(status_code=200, content={"documents": documents})
        else:
            return JSONResponse(status_code=200, content={"documents": []})
    except Exception as e:
        logger.error(f"Error during document retrieval: {e}")
        return JSONResponse(status_code=500, content={"message": "Failed to retrieve documents."})

@router.post('/delete-document')
async def delete_document(
    request: DeleteDocumentRequest  # Use the new model for the request body
):
    """
    Delete a document associated with a given passphrase and filename.

    :param request: The request body containing passphrase and filename.
    :return: JSONResponse indicating the success or failure of the operation.
    """
    try:
        storage.delete_document(passphrase=request.passphrase, filename=request.filename)
        return JSONResponse(status_code=200, content={"message": "Document deleted successfully."})
    except Exception as e:
        logger.error(f"Error during document deletion: {e}")
        return JSONResponse(status_code=500, content={"message": "Failed to delete document."})


@router.post('/sanitize')
async def sanitize_documents():
    """
    Sanitize documents older than a specified date.

    :return: JSONResponse indicating the success or failure of the operation.
    """
    try:
        # Assuming the keep_until date is passed in the request body
        storage.delete_documents_older_than(current_time=dt.datetime.now(), passphrase=None)
        return JSONResponse(status_code=200, content={"message": "Documents sanitized successfully."})
    except Exception as e:
        logger.error(f"Error during sanitization: {e}")
        return JSONResponse(status_code=500, content={"message": "Failed to sanitize documents."})


@router.get('/ask')  # Keep this as GET
async def ask_question(
    question: str, 
    passphrase: str = Query(...)
):
    """
    Handle incoming questions and provide streaming responses.

    :param question: The user's question.
    :param history: A JSON string of previous messages in the conversation.
    :return: Streaming response with AI-generated answers.
    """
    try:
        # Parse the history from JSON string to list of dictionaries
        #chat_history = json.loads(history)

        # Embed the question asynchronously if possible
        question_embedding = embedder.embed_documents([{"page_content": question, "metadata": {}}])[0]['embedding']
        
        # Retrieve similar content from the database
        similar_content = retriever.vector_search(passphrase, question_embedding, top_k=5)

        if similar_content:
            # Convert history to LangChain message format
            #chat_history = [
            #    AIMessage(content=msg['content']) if msg['role'] == "assistant" else HumanMessage(content=msg['content'])
            #    for msg in chat_history
            #]
            
            # Update LLM's conversation history
            #llm.conversation_history = chat_history
            
            # Define an async generator to stream responses
            async def response_stream() -> AsyncGenerator[bytes, None]:
                try:
                    async for chunk in llm_answer.generate_response(
                        question=question, 
                        context=similar_content
                        ):
                        # Yield the data in the correct SSE format
                        yield f"data: {chunk}\n\n".encode('utf-8')
                except Exception as e:
                    logger.error(f"Error during streaming: {e}")
                    yield f"data: Error during streaming: {str(e)}\n\n".encode('utf-8')

            # Return the streaming response to the client
            return StreamingResponse(response_stream(), media_type="text/event-stream")

        else:
            # If no similar content is found, tell the LLM to inform the user
            #llm.conversation_history = [HumanMessage(content="I'm sorry. I did not find any relevant context in the supplied documents.")]
            async def response_stream() -> AsyncGenerator[bytes, None]:
                try:
                    async for chunk in llm_sorry.generate_response(question="Kindly ask me to rephrase my question", context=[]):
                        # Yield the data in the correct SSE format
                        yield f"data: {chunk}\n\n".encode('utf-8')
                except Exception as e:
                    logger.error(f"Error during streaming: {e}")
                    yield f"data: Error during streaming: {str(e)}\n\n".encode('utf-8')

            # Return the streaming response to the client
            return StreamingResponse(response_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")



# Document upload endpoint
@router.post('/upload')
async def upload_documents(
    files: List[UploadFile] = File(...),
    passphrase: str = Query(...),
    expiration: float = Query(...)
    ):
    expiration_time = dt.datetime.now()+dt.timedelta(hours=expiration)
    logger.info("Processing uploaded documents")
    processed_files = []
    all_embedded_chunks = []
    try:
        for file in files:
            try:
                contents = await file.read()
                file_path = f"/tmp/{file.filename}"

                # Save the file temporarily using aiofiles for async file I/O
                async with aiofiles.open(file_path, "wb") as temp_file:
                    await temp_file.write(contents)

                # Load the document
                documents = loader.load_document(file_path)

                for document in documents: 
                    document.page_content = document.page_content.replace('\n', ' ')

                print(documents)
                # Split the document
                chunks = splitter.split_documents(documents)

                # Embed the chunks
                embedded_chunks = embedder.embed_documents(chunks)

                all_embedded_chunks.extend(embedded_chunks)
                processed_files.append(file.filename)

                # Remove the temporary file safely
                if os.path.exists(file_path):
                    os.remove(file_path)

                logger.info(f"Processed document: {file.filename}")
            except Exception as file_error:
                logger.error(f"Error processing file {file.filename}: {file_error}")
                raise HTTPException(status_code=400, detail=f"Error processing file {file.filename}: {str(file_error)}")

        # Store all embedded chunks with a passphrase
        storage.store_embeddings(
            passphrase=passphrase, 
            documents=all_embedded_chunks, 
            keep_until=expiration_time
            )

        print(expiration)
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Documents processed and stored successfully",
                "data": {
                    "processed_files": processed_files,
                    "total_chunks": len(all_embedded_chunks)
                }
            }
        )
    except Exception as e:
        logger.error(f"Error in upload process: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# List documents endpoint
@router.get('/documents')
async def list_documents():
    return {"documents": list(document_embeddings.keys())}
