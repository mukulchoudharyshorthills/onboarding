import fitz # PyMuPDF
import os
import tempfile
#from azure.ai.openai import OpenAIClient
from azure.ai.inference import ChatCompletionsClient
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import ContainerClient
import base64
import json
import requests

AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')

AZURE_SAS_URL = os.getenv("AZURE_SAS_URL")
CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")

client = ChatCompletionsClient(endpoint=AZURE_OPENAI_ENDPOINT, credential=AzureKeyCredential(AZURE_OPENAI_KEY))


SYSTEM_PROMPT = {
    'personal':"""You are a data entry professional and you must analyze a document, extract relevant information and report it. 

    I'll give you a pdf document or a image from which you must extract personal identifiable information (PII).

    * Input *
    A pdf or image file containing text and images. It can be possibly the result of a scanned file.

    * Output *
    You must extract the personal information and return them as a valid JSON object. Dont add word json to the result.
    """,
    'employment':"""You are an intelligent document processing assistant. Extract all available employment information from this document and provide it in structured JSON format. Include, if available:
                    Employee Name
                    Employer Name
                    Job Title / Designation
                    Start Date of Employment
                    End Date (or mark as 'current' if still employed)
                    Department (if available)
                    Employment Type (full-time, part-time, contract, etc.)
                    Salary or Compensation Details
                    Address of Employer
                    Additional relevant employment details
                    Only extract what is explicitly available in the document, with no fabrication. If a field is missing, leave it null or indicate 'not present.Dont add word json to the result'""",
    'education':"""Analyze the uploaded education document (such as a transcript, diploma, or certificate) and extract all relevant user education information in a structured JSON format. Please identify and output the following fields if present:
                    Full Name of student
                    Institution/School/University name
                    Degree or qualification awarded
                    Course or major subject
                    Date of issue or graduation date
                    Grades, marks, GPA, or classification
                    Duration or academic year(s)
                    Any honors or distinctions
                    Extract only information explicitly visible in the document. If a field is missing, output it as null or 'not present.' Do not invent any data. Dont add word json to the result""",
    'certificates':"""Analyze the uploaded certificate document (PDF or image) and extract all relevant user information available in the certificate. Please identify and output the following fields in a structured JSON format if present:
                    Full Name
                    Date of Birth
                    Certificate Number
                    Date of Issue
                    Expiry Date (if applicable)
                    Issuing Authority / Organization
                    Any grades, scores, or honors mentioned
                    Relevant descriptive fields such as course or certification name
                    Extract only the information explicitly visible in the document. If a field is missing, output null or 'not present'. Do not invent or guess any data.Dont add word json to the result"""
}

def extract_pii_from_image(image_path: str, tag: str):
    with open(image_path, 'rb') as img_file:
        img_bytes = img_file.read()
        img_data = base64.b64encode(img_bytes).decode('utf-8')

    """messages = [
        {
                "role": "user",
                "content": [
                    {"type": "text", "text": SYSTEM_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}
                ]
            }
    ]
    print(client)
    response = client.complete(
        model=AZURE_OPENAI_DEPLOYMENT,
        messages=messages
    )"""
    print(SYSTEM_PROMPT[tag])
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": SYSTEM_PROMPT[tag]},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}}
                ]
            }
        ],
        "max_tokens": 800
    }
    headers = {
    "api-key": AZURE_OPENAI_KEY,
    "Content-Type": "application/json",
}
    response = requests.post(AZURE_OPENAI_ENDPOINT, json=payload, headers=headers)
    result = response.json()
    print(result["choices"][0]["message"]["content"])
    return json.loads(result["choices"][0]["message"]["content"])

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
    if not all([AZURE_SAS_URL, CONTAINER_NAME]):
        raise ValueError("Azure Storage credentials or container name missing from .env file")

    # Create blobcontainerclient
    blob_container_client = ContainerClient.from_container_url(AZURE_SAS_URL)

    # Use file name as blob name if not specified
    if blob_name is None:
        blob_name = os.path.basename(file_path)

    print(f"Uploading {file_path} → {CONTAINER_NAME}/{blob_name}")
    blob_path = f"{AZURE_SAS_URL.split('?')[0]}/{blob_name}?{AZURE_SAS_URL.split('?')[1]}"

    # Upload file
    with open(file_path, "rb") as data:
        blob_container_client.upload_blob(name=blob_name, data=data, overwrite=True)

    print("✅ Upload complete!")
    return blob_path