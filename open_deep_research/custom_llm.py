# import requests
# from langchain.llms import LLM
# from typing import Optional, List

# # Available models from the GitHub Models Marketplace.
# AVAILABLE_MODELS = [
#     "gpt-4o-mini", "gpt-4o", 
#     "DeepSeek-V3", "DeepSeek-R1",
#     "Cohere-command-r-plus-08-2024", 
#     "Llama-3.2-11B-Vision-Instruct", "Llama-3.3-70B-Instruct", "Llama-3.2-90B-Vision-Instruct", 
#     "Codestral-2501", "Mistral-Large-2411", "Ministral-3B",
#     "Phi-4-mini-instruct", "Phi-4-multimodal-instruct"
#     # Note: Some models are commented out because they either throw errors or are not available.
# ]

# class CustomLLM(LLM):
#     base_url: str
#     api_key: str
#     model_name: str

#     def __init__(self, base_url: str, api_key: str, model_name: str):
#         """
#         Initializes the CustomLLM.

#         :param base_url: Azure inference endpoint URL.
#         :param api_key: GitHub PAT token used as the API key.
#         :param model_name: Name of the model to use (must be one from AVAILABLE_MODELS).
#         """
#         if model_name not in AVAILABLE_MODELS:
#             raise ValueError(f"Model '{model_name}' is not in the list of available models.")
#         self.base_url = base_url
#         self.api_key = api_key
#         self.model_name = model_name

#     @property
#     def _llm_type(self) -> str:
#         return "custom_llm"

#     def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
#         """
#         Sends the prompt to the model via the Azure endpoint.

#         :param prompt: The input prompt for the model.
#         :param stop: Optional list of stop tokens.
#         :return: The generated text response.
#         """
#         headers = {
#             "Authorization": f"Bearer {self.api_key}",
#             "Content-Type": "application/json"
#         }
#         # The payload structure might need adjustments based on your endpoint's API specification.
#         payload = {
#             "model": self.model_name,
#             "prompt": prompt,
#             # You can add additional parameters here if required by the API.
#         }
#         response = requests.post(self.base_url, headers=headers, json=payload)
#         if response.status_code != 200:
#             raise Exception(f"Request failed: {response.status_code} - {response.text}")
#         result = response.json()
#         # Adjust the key 'text' if your API returns the response differently.
#         return result.get("text", "")

# # Example usage:
# if __name__ == "__main__":
#     # Azure inference endpoint (provided by the GitHub Models Marketplace)
#     azure_endpoint = "https://your-azure-endpoint/inference"
#     # GitHub PAT token to authenticate requests.
#     github_pat = "YOUR_GITHUB_PAT_TOKEN"
#     # Select a model from the available list.
#     selected_model = "gpt-4o"  # Change this to any model from AVAILABLE_MODELS

#     custom_llm = CustomLLM(base_url=azure_endpoint, api_key=github_pat, model_name=selected_model)
    
#     # Send a prompt and print the response.
#     prompt = "Tell me a joke about AI."
#     response = custom_llm(prompt)
#     print(response)


import requests
from typing import List, Optional, Any
from langchain.llms.base import LLM
from langchain.chat_models import azureml_endpoint

class AzureInferenceLLM(LLM):
    """Custom LLM that wraps the Azure Inference API endpoint at models.inference.ai.azure.com."""
    
    def __init__(self, api_key: str, endpoint: str = "https://models.inference.ai.azure.com/your-model-endpoint"):
        self.api_key = api_key
        self.endpoint = endpoint

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        # Build the request payload based on the API's requirements.
        payload = {
            "prompt": prompt,
            # Include other parameters as needed (e.g., max_tokens, temperature, etc.)
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(self.endpoint, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        # Adjust this based on the response structure of the API.
        generated_text = result.get("generated_text", "")
        return generated_text

    @property
    def _llm_type(self) -> str:
        return "azure_inference_llm"
