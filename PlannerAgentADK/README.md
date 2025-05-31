# PlannerAgentADK

This application demonstrates a planner agent built using the Google Agent Development Kit (ADK). The agent is capable of understanding user requests and utilizing a set of tools to perform actions like solving math problems, performing file operations, sending SMS/MMS messages, and making phone calls via Twilio.

## How it Works

The core of the application is the `PlannerAgentADK` (`adk_planner_agent.py`), which is an `LlmAgent` configured with a set of tools and instructions.

1.  **Initialization**:
    *   Environment variables are loaded from a `.env` file (e.g., for Twilio credentials, Google Cloud Project details).
    *   Logging is configured.
    *   Tools are initialized:
        *   `MathTool`: Solves basic mathematical expressions.
        *   `FileIOTool`: Performs file operations (write, append, read, delete) within a designated base directory (`app_io_files` relative to the agent script, or `adk_tool_files` in the current working directory if not specified).
        *   `SmsTool`: Sends SMS and MMS messages using Twilio.
        *   `CallsTool`: Makes phone calls using Twilio.
    *   These tools are wrapped as `FunctionTool` instances and provided to the `LlmAgent`.

2.  **LLM Configuration**:
    *   The agent uses a Google generative model (defaulting to `gemini-2.5-flash-preview-05-20`).
    *   It can be configured to use Google AI Studio (via `GOOGLE_API_KEY`) or Vertex AI (via `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`). The `GOOGLE_GENAI_USE_VERTEXAI` environment variable controls this (defaults to `FALSE` for AI Studio).

3.  **Agent Instruction**:
    *   A specific instruction is provided to the LLM, guiding it to first consider using available tools to fulfill user requests before responding directly.

4.  **Tool Usage**:
    *   When the agent determines a tool is needed, it outputs a function call.
    *   The ADK framework executes the tool, and the results are fed back to the agent.
    *   The agent then uses these results to formulate the final response to the user.

5.  **Main Agent (`root_agent`)**:
    *   A global `root_agent` is defined and initialized. This is the agent that the ADK CLI tools (`adk run`, `adk web`) will interact with.

## Prerequisites

1.  **Python**: Ensure you have Python installed (version 3.8+ recommended).
2.  **Google ADK**: Install the Google Agent Development Kit.
    ```bash
    pip install google-adk
    ```
3.  **Dependencies**: Install the Python packages listed in `requirements.txt`:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Environment Variables**:
    *   Create a `.env` file in the `PlannerAgentADK` directory.
    *   **For Google LLM Access**:
        *   **Google AI Studio (Default)**:
            *   Set `GOOGLE_GENAI_USE_VERTEXAI=FALSE` (or omit, as it defaults to `FALSE`).
            *   Obtain a `GOOGLE_API_KEY` from Google AI Studio and add it to your `.env` file:
                ```
                GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"
                ```
        *   **Vertex AI**:
            *   Set `GOOGLE_GENAI_USE_VERTEXAI=TRUE`.
            *   Set your Google Cloud Project ID and Location:
                ```
                GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
                GOOGLE_CLOUD_LOCATION="your-gcp-location" # e.g., us-central1
                ```
            *   Ensure you are authenticated: `gcloud auth application-default login`
    *   **For Twilio Tools (SMS/Calls)**:
        *   Create a Twilio account and get your Account SID, Auth Token, and a Twilio phone number.
        *   Add these to your `.env` file:
            ```
            TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
            TWILIO_AUTH_TOKEN="your_auth_token"
            TWILIO_FROM_PHONE="+1xxxxxxxxxx"
            ```
        *   (Optional) For testing the tools directly via their `if __name__ == "__main__":` blocks:
            ```
            TEST_RECIPIENT_PHONE="+1xxxxxxxxxx" # A phone number you can send test messages/calls to
            ```
    *   **Example `.env` file content (for Google AI Studio & Twilio)**:
        ```env
        # Google AI Studio
        GOOGLE_API_KEY="YOUR_AI_STUDIO_API_KEY"
        GOOGLE_GENAI_USE_VERTEXAI=FALSE

        # Twilio
        TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        TWILIO_AUTH_TOKEN="your_auth_token"
        TWILIO_FROM_PHONE="+1xxxxxxxxxx"
        TEST_RECIPIENT_PHONE="+1yyyyyyyyyy"
        ```

## How to Run

Navigate to the parent directory of `PlannerAgentADK` (i.e., `PlannerApp`).

1.  **Using ADK CLI (Recommended)**:
    *   **Interactive Run**:
        ```bash
        adk run ADK
        ```
        This will load the `root_agent` from `PlannerAgentADK/adk_planner_agent.py` and allow you to interact with it in your terminal. (Note: The `ADK` argument refers to the `PlannerAgentADK` directory where the `adk_planner_agent.py` and `root_agent` are defined).
    *   **Web UI**:
        ```bash
        adk web
        ```
        This will start a local web server (typically on `http://127.0.0.1:8000`) providing a chat interface to interact with the agent.

2.  **Direct Script Execution (for testing individual tool files)**:
    *   You can run the individual tool Python files (`adk_math_tool.py`, `adk_file_io_tool.py`, etc.) directly if they have an `if __name__ == "__main__":` block for testing purposes. This is mainly for isolated tool testing.
    ```bash
    cd PlannerAgentADK
    python adk_math_tool.py
    python adk_file_io_tool.py 
    # etc.
    ```
    *   Running `adk_planner_agent.py` directly will initialize the agent and log its status but won't provide an interactive prompt by default. The ADK CLI tools are preferred for interaction.

## Future Exploration

My intention is to attempt to build similar planner agents using Langchain and LangGraph in the future. This will allow for a comparison of different frameworks and approaches to building multi-tool AI agents.

## File Structure

```
PlannerAgentADK/
├── .env                   # (You need to create this for credentials)
├── .gitignore
├── __init__.py
├── adk_calls_tool.py      # Tool for making phone calls
├── adk_file_io_tool.py    # Tool for file input/output
├── adk_math_tool.py       # Tool for solving math expressions
├── adk_planner_agent.py   # Main agent definition
├── adk_sms_tool.py        # Tool for sending SMS/MMS
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

The `app_io_files/` directory will be created by `adk_file_io_tool.py` (if the agent is configured to point there as in the current `adk_planner_agent.py` setup) to store any files written by the agent. If `FileIOTool` is initialized without a specific `base_directory`, it will create `adk_tool_files/` in the current working directory. 