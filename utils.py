import fitz # PyMuPDF
import os
import tempfile
from azure.ai.openai import OpenAIClient
from azure.core.credentials import AzureKeyCredential
import base64
import json

AZURE_OPENAI_ENDPOINT = os.getenv('AZURE_OPENAI_ENDPOINT')
AZURE_OPENAI_KEY = os.getenv('AZURE_OPENAI_KEY')
AZURE_OPENAI_DEPLOYMENT = os.getenv('AZURE_OPENAI_DEPLOYMENT')


client = OpenAIClient(AZURE_OPENAI_ENDPOINT, AzureKeyCredential(AZURE_OPENAI_KEY))


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
        img_data = base64.b64encode(img_file.read()).decode('utf-8')

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