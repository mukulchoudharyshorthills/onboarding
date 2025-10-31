import fitz # PyMuPDF
import os
import tempfile
#from azure.ai.openai import OpenAIClient
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient
import base64
import json

AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')

ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
ACCOUNT_KEY = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

client = ChatCompletionsClient(AZURE_OPENAI_ENDPOINT, AzureKeyCredential(AZURE_OPENAI_KEY))


#SYSTEM_PROMPT = (
#    "You are an AI assistant extracting personal identifiable information (PII) from an image. "
#    "Return JSON with fields: name, email, phone, address, date_of_birth."
#)
SYSTEM_PROMPT = (
    """You are a data entry professional and you must analyze a document, extract relevant information and report it. 

    I'll give you a pdf document or a image from which you must extract:
    * **name**: a string representing the name of a person
    * **surname**: a string representing the surname of a person
    * **birth_date**: a date, in the format YYYY-MM-DD, representing the birth dateof a person
    * **sex**: a single character (either "F" or "M"), representing the sex of the person

    * Input *
    A pdf or image file containing text and images. It can be possibly the result of a scanned file.

    * Output *
    You must extract the field specified above and return them as a valid JSON object. Below an example:
    {
        "name": "Mark",
        "surname": "Twain",
        "sex": "M",
        "birth_date": "1835-11-30"
    }"""
)

def extract_pii_from_image(image_path):
    with open(image_path, 'rb') as img_file:
        img_bytes = img_file.read()
        img_data = base64.b64encode(img_bytes).decode('utf-8')

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract PII from this image."},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}}
            ]
        }
    ]

    response = client.get_chat_completions(
        deployment_id=AZURE_OPENAI_DEPLOYMENT,
        messages=messages
    )

    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except Exception:
        return {"raw": content}

def convert_pdf_to_images(pdf_path):
    doc = fitz.open(pdf_path)
    image_paths = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap()
        img_path = os.path.join(tempfile.gettempdir(), f"page_{i+1}.png")
        pix.save(img_path)
        image_paths.append(img_path)
    doc.close()
    return image_paths

def upload_file_to_blob(file_path: str, blob_name: str = None):
    """Uploads a local file to Azure Blob Storage"""
    if not all([ACCOUNT_NAME, ACCOUNT_KEY, CONTAINER_NAME]):
        raise ValueError("Azure Storage credentials or container name missing from .env file")

    # Construct the connection string manually
    conn_str = f"DefaultEndpointsProtocol=https;AccountName={ACCOUNT_NAME};AccountKey={ACCOUNT_KEY};EndpointSuffix=core.windows.net"

    # Create BlobServiceClient
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)

    # Get container client
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)

    # Ensure the container exists
    container_client.create_container(exist_ok=True)

    # Use file name as blob name if not specified
    if blob_name is None:
        blob_name = os.path.basename(file_path)

    print(f"Uploading {file_path} → {CONTAINER_NAME}/{blob_name}")
    blob_path = f"{CONTAINER_NAME}/{blob_name}"
    # Get blob client
    blob_client = container_client.get_blob_client(blob_name)

    # Upload file
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)

    print("✅ Upload complete!")
    return blob_path