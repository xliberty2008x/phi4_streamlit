# Phi-4 Multimodal Chat Application

This application leverages the latest Phi-4 multimodal model, which supports text, image, and audio processing. Under the hood, it uses Microsoft’s Phi-4 model deployed via Azure Foundry. By registering with Azure Foundry, you can deploy the model and obtain an API key required to run this application.

## Features
- Chat interface supporting text, image, and audio messages.
- File upload and URL support for media integration.
- Integration with Azure-hosted Phi-4 multimodal model.

## Getting Started

### Prerequisites
- Python 3.8+
- An Azure API key from Azure Foundry after deploying the Phi-4 model

### Installation

1. **Clone the Repository**
    ```
    git clone https://github.com/yourusername/phi4_streamlit.git
    cd phi4_streamlit
    ```

2. **Create and Activate a Virtual Environment**
    ```
    python -m venv venv
    source venv/bin/activate   # On Windows use `venv\Scripts\activate`
    ```

3. **Install Dependencies**
    ```
    pip install -r requirements.txt
    ```

4. **Set Up Environment Variables**
    Create a `.env` file in the project root and add your Azure API key:
    ```
    AZURE_INFERENCE_CREDENTIAL=your_api_key_here
    ```

### Running Locally

Launch the Streamlit app by executing:
```
streamlit run app.py
```

### Deploying on Streamlit Cloud

1. Push your repository to GitHub.
2. Log in to [Streamlit Cloud](https://streamlit.io/cloud) and click **New App**.
3. Connect your GitHub repository and select the branch to deploy.
4. Set up necessary environment variables (e.g., `AZURE_INFERENCE_CREDENTIAL`) in the app’s settings dashboard.
5. Deploy the application and share your live app.

## Registration on Azure Foundry

To use the Phi-4 multimodal model:
1. Visit the Azure Foundry portal.
2. Register for an account and follow the instructions to deploy the Phi-4 model.
3. Retrieve your Azure API key once the deployment is complete.
4. Insert the key into your environment variables as shown above.

## License

This project is licensed under the MIT License.

## Acknowledgements

- Built using [Streamlit](https://streamlit.io/)
- Powered by Microsoft Phi-4 Multimodal Model
