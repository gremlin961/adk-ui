# ADK UI

This project is a simple User Interface (UI) demonstrating how to interact with the Google Agent Development Kit (ADK).

## Overview

The primary goal of this UI is to provide a straightforward example of ADK integration and usage. It showcases basic interactions and functionalities that can be built using the ADK.

## Features

*   Demonstrates ADK initialization and communication.
*   Provides a simple interface for sending requests to and receiving responses from an ADK-powered agent.

## Getting Started

To run this project, you'll need to set up your environment and install the necessary dependencies.

### Prerequisites

*   Python 3.x
*   pip (Python package installer)

### Installation & Setup

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd adk-ui
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file:**
    This project uses a `.env` file to manage environment variables, such as API keys or other configuration settings. This file is not committed to the repository for security reasons.

    Create a file named `.env` in the `chat_agent/` directory (`chat_agent/.env`).

    Add the necessary environment variables to this file. You can configure it to use either a Google API Key or Vertex AI.

    **Option 1: Using a Google API Key**
    If you prefer to use a Google API Key directly, your `.env` file might look like this:
    ```env
    # Replace with your actual Google API Key
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY"

    # Other necessary variables for the ADK agent, if any
    # ADK_AGENT_ID="YOUR_AGENT_ID"
    ```

    **Option 2: Using Vertex AI (as per current project setup)**
    If you want to use Vertex AI, configure your `.env` file as follows. This is the current recommended setup for this project.
    ```env
    GOOGLE_GENAI_USE_VERTEXAI=TRUE
    GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"  # Replace with your Google Cloud Project ID
    GOOGLE_CLOUD_LOCATION="global"          # Or your specific location
    GOOGLE_CLOUD_REGION="us-central1"       # Or your specific region
    ```
    Ensure you replace `"YOUR_PROJECT_ID"` with your actual Google Cloud Project ID. The `LOCATION` and `REGION` might also need adjustment based on your Vertex AI setup.

    Choose the option that best suits your needs and ensure all required variables are correctly set as per the ADK documentation or your specific agent requirements.

5.  **Run the application:**
    ```bash
    python main.py
    ```
    The application should now be running, and you can access the UI in your browser (typically at `http://127.0.0.1:5000` or as specified by the `main.py` script).

## Project Structure

The project is organized as follows:

```
.
├── .gitignore
├── LICENSE
├── main.py                 # Main Python application file
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── chat_agent/             # Contains the ADK agent logic
│   ├── __init__.py
│   └── agent.py
└── static/                 # Contains the frontend UI files
    ├── index.html          # Main HTML file for the UI
    ├── script.js           # JavaScript for UI interactions
    └── styles.css          # CSS for styling the UI
```

## Contributing

(Information about how to contribute to the project can be added here later if needed)

## License

This project is licensed under the [LICENSE_NAME] License - see the [LICENSE](LICENSE) file for details.
