from langchain_openai import AzureChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from typing import List, Dict, Any, AsyncGenerator
import os
from langchain.callbacks.base import BaseCallbackHandler
import asyncio

class StreamingCallbackHandler(BaseCallbackHandler):
    def __init__(self):
        self.content = ""

    def on_llm_new_token(self, token: str, **kwargs):
        """
        Callback handler to process each new token generated during streaming.
        This will be called for each token received from the streaming response.
        """
        self.content += token
        print(token, end="", flush=True)  # Optionally print to console, remove if not needed


class LLM:
    def __init__(self, system_prompt: str, deployment: str = "gpt-35-turbo"):
        # Initialize the AzureChatOpenAI model with streaming enabled
        self.llm = AzureChatOpenAI(
            stream=True,  # Enable streaming responses
            deployment_name=deployment,
            openai_api_version=os.getenv("LLM_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("LLM_OPENAI_API_BASE"),
            openai_api_key=os.getenv("LLM_OPENAI_API_KEY"),
            max_tokens=2048
        )
        self.system_prompt = system_prompt
        self.conversation_history = []

    async def generate_response(self, question: str, context: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """
        Generates an AI response using the LLM model with the provided question and context.
        :param question: The user's question
        :param context: List of dictionaries containing the most similar content
        :return: An async generator that yields chunks of the AI-generated response
        """
        # Initialize the callback handler for streaming
        callback_handler = StreamingCallbackHandler()

        # Prepare the conversation with the system prompt, history, and provided context
        # Inject the context into the user's question with a clear heading
        injected_question = question + "\n" + "\n\n".join([f"Context: {ctx['content']}" for ctx in context])
        conversation = [SystemMessage(content=self.system_prompt)] + [HumanMessage(content=injected_question)]
        
            
        for message in conversation:
            print('---')
            print(message)

        # Stream the response using the astream method
        async for chunk in self.llm.astream(conversation):
            # Optionally append the chunk to the conversation history for future context
            self.conversation_history.append(AIMessage(content=chunk.content))
            yield chunk.content  # Yield each chunk to the async generator


    def clear_conversation_history(self):
        """Clear the conversation history."""
        self.conversation_history = []

    def set_deployment(self, deployment: str):
        """Update the LLM model deployment."""
        self.llm = AzureChatOpenAI(
            deployment_name=deployment,
            openai_api_version=os.getenv("LLM_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("LLM_OPENAI_API_BASE"),
            openai_api_key=os.getenv("LLM_OPENAI_API_KEY"),
            max_tokens=2048
        )

    def set_system_prompt(self, prompt: str):
        """Update the system prompt."""
        self.system_prompt = prompt
