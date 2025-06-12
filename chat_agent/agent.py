# Copyright 2024 Google, LLC. This software is provided as-is,
# without warranty or representation for any use or purpose. Your
# use of it is subject to your agreement with Google.
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#    http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Example Agent Workflow using Google's ADK
# 
# This notebook provides an example of building an agentic workflow with Google's new ADK. 
# For more information please visit  https://google.github.io/adk-docs/



# Vertex AI Modules
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part # Removed unused: GenerationConfig, Tool, ChatSession, FunctionDeclaration, grounding, GenerationResponse

# Vertex Agent Modules
from google.adk.agents import Agent # Base class for creating agents
# Removed unused: from google.adk.runners import Runner
# Removed unused: from google.adk.sessions import InMemorySessionService
# Removed unused: from google.adk.artifacts import InMemoryArtifactService, GcsArtifactService
from google.adk.tools.agent_tool import AgentTool # Wrapper to use one agent as a tool for another
# Removed unused: from google.adk.tools import ToolContext
from google.adk.tools import google_search # Removed unused: load_artifacts

# Vertex GenAI Modules (Alternative/Legacy way to interact with Gemini, used here for types)
# Removed unused: import google.genai
# Removed unused: from google.genai import types as types

# Google Cloud AI Platform Modules
# Removed unused: from google.cloud import aiplatform_v1beta1 as aiplatform


# Other Python Modules
#import base64 # Not used in the final script
#from IPython.display import Markdown # Not used in the final script
# Removed unused: import asyncio
# Removed unused: import requests
import os # For interacting with the operating system (paths, environment variables)
# Removed unused: from typing import List, Dict, TypedDict, Any
# Removed unused: import json
# Removed unused: from urllib.parse import urlparse
import warnings # For suppressing warnings
import logging # For controlling logging output
# Removed unused: import mimetypes
# Removed unused: import io
from dotenv import load_dotenv


# --- Configuration ---
load_dotenv()


# Ignore all warnings
warnings.filterwarnings("ignore")
# Set logging level to ERROR to suppress informational messages
logging.basicConfig(level=logging.ERROR)


# --- Agent Tool Definitions ---
# @title Define Tools for creating a ticket, adding notes to a ticket, add a file to the session, and getting the GCS URI




# --- Agents ---

# -- Search Agent ---
# This agent's role is to perform a Google search for grounding
search_agent = None
search_agent = Agent(
    model="gemini-2.0-flash-exp", # A robuts and responsive model for performing simple actions
    name="search_agent",
    instruction=
    """
        You are a research expert for your company. You will be provided with a request to perform a Google search for something and you will return your findings.
        
        You will use the `google_search` tool to perform a Google search and respond with the results.
        
        An example workflow proceed with your research.
        
        An example workflow would be:
        1: You will be provided with a topic or question to research
        2: Use the `google_search` tool to perform a Google search for the provided question or topic.
        3: Return the response to the calling agent
        
    """,
    description="Performs searches related to a provided question or topic.",
    tools=[
        google_search,
    ],
)


# --- Reasoning Agent ---
# This agent's role is to generate a detailed response to a users question
reasoning_agent = None
reasoning_agent = Agent(
    model="gemini-2.5-pro-preview-05-06", # Advanced model for complex tasks and reasoning
    name="reasoning_agent",
    instruction=
    """
        You are a research expert for your company. You will be provided with a request to research something and you will return your findings.
        
        You have access to the following tools:
        1: Tool `search_agent`: Use this AgentTool to request a Google search for grounding.
        
               
        An example workflow would be:
        1: You will be provided with a topic or question to research.
        2: Use the `search_agent` AgentTool to request a Google search for the provided question or topic.
        3: Return the response to the calling agent
        
    """,
    description="Performs reasearch related to a provided question or topic.",
    tools=[
        AgentTool(agent=search_agent), # Make the search_agent available as a tool
        # get_session_id, # Commented out: No longer needed by status_message tool
    ],
)



# --- Root Agent Definition ---
# @title Define the Root Agent with Sub-Agents

# Initialize root agent variables
root_agent = None
runner_root = None # Initialize runner variable (although runner is created later)

    # Define the root agent (coordinator)
search_agent_team = Agent(
    name="search_support_agent",    # Name for the root agent
    #model="gemini-2.0-flash-001", # Model for the root agent (orchestration)
    model="gemini-2.0-flash-exp", # Model that supports Audio input and output 
    description="The main coordinator agent. Handles user requests and delegates tasks to specialist sub-agents and tools.", # Description (useful if this agent were itself a sub-agent)
    instruction=                  # The core instructions defining the workflow
    """
        You are the lead support coordinator agent. Your goal is to understand the customer's question or topic, and then delegate to the appropriate agent or tool.

        You have access to specialized tools and sub-agents:
        1. AgentTool `reasoning_agent`: Provide the user's question or topic. This agent will research the topic or question and provide a detailed response. The `reasoning_agent`'s response will be streamed directly to the user.
        
      

        Your workflow:
        1. Start by greeting the user.
        2. Ask no more than 1-2 clarifying questions to understand their research request.
        3. Once the request is clear, inform the user you will begin the research (e.g., "Okay, I'll start researching that for you. Please wait a moment.").
        4. Call the `reasoning_agent` and provide the user's research request. 
        5. Provide the full audit report from the `research_agent` to the user. Do not summarize this information, just return the full report exactly as you receive it. 
        6. Ask the user if there is anything else you can help with.
       
    """,
    tools=[
        AgentTool(agent=reasoning_agent), # Make the reasoning_agent available as a tool
    ],
    sub_agents=[
    ],

)

# Assign the created agent to the root_agent variable for clarity in the next step
root_agent = search_agent_team
