from flask import Flask, request, redirect, url_for, render_template, jsonify
from models import users, loginlogs, documents, user_helper, document_helper, log_helper
import os
import time
from datetime import datetime
from bson import ObjectId
from utils import convert_pdf_to_images, extract_pii_from_image
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

@app.route('/ping')
def ping():
   return 'pong!'

@app.route('/login', methods=['GET'])
def login():
    username = request.args.get('username')
    password = request.args.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    user = users.find_one({"username": username})
    if not user:
        users.insert_one({"username": username, "password": password, "status": "unverified"})

    user = users.find_one({"username": username})

    loginlogs.insert_one({
        "user_id": user["_id"],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": int(time.time()),
        "action": "login"
    })

    return jsonify({'message': 'Login successful'}), 200

@app.route('/user', methods=['GET'])
def getUsers():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    user = user_helper(users.find_one({"_id": ObjectId(user_id)}))
    if not user:
        return jsonify({'error': 'user not found'}), 400
    return jsonify({'message': 'user fetched', 'user': user}), 200

@app.route('/logout', methods=['GET'])
def logout():
    user_id = request.args.get('id')
    if not user_id:
        return jsonify({'error': 'Missing user id'}), 400

    loginlogs.insert_one({
        "user_id": user_id,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timestamp": int(time.time()),
        "action": "logout"
    })

    return jsonify({'message': 'Logout successful'}), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    allowed_ext = ('.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.tif')
    files = request.files.getlist('files')
    uploadedFiles = []
    responses = []
    for file in files:
        if file.filename == '':
            responses.append({'error': 'No selected file', 'filename': file.filename})
            continue
        if not file.filename.lower().endswith(allowed_ext):
            return jsonify({'error': 'Please upload a PDF or image file'}), 400
        #prompt_file = f"./prompts/prompt_file.txt"
        file_path = f"./input/{file.filename}"
        
        if os.path.exists(file_path):
            timestamp = int(time.time())
            name, ext = os.path.splitext(file.filename)
            file.filename = f"{name}_{timestamp}{ext}"
            file_path = f"./input/{file.filename}"
        file.save(file_path)

        results = []
        if file.filename.lower().endswith('.pdf'):
            images = convert_pdf_to_images(file_path)
            for img_path in images:
                pii = extract_pii_from_image(img_path)
                results.append(pii)
        else:
            pii = extract_pii_from_image(file_path)
            results.append(pii)
        
        print(results)
        result = documents.insert_one({
            "user_id": ObjectId(request.form.get('user_id')),
            "path": file_path,
            "title": request.form.get('title', ''),
            "tag": request.form.get('tag', ''),
            "data": results,
            "status": "unverified"
        })
        uploadedFiles.append(document_helper(documents.find_one({"_id": result.inserted_id})))

    
    return jsonify({'message': 'File uploaded successfully', 'uploaded_files': uploadedFiles }), 200

@app.route('/logs', methods=['GET'])
def getUserLogs():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400

    result = loginlogs.find({"user_id": ObjectId(user_id)})
    logs = []
    for log in result:
        logs.append(log_helper(log))
    if not logs:
        return jsonify({'message': 'no user logs found'}), 400
    return jsonify({'message': 'user logs fetched', 'logs': logs}), 200

@app.route('/verifyDocumentData', methods=['GET'])
def verifyDocData():
    id = request.args.get('id')
    if not id:
        return jsonify({'error': 'Missing document id'}), 400

    result = documents.update_one(
        {"_id": ObjectId(id), "status": "unverified"},
        {"$set": {"status": "verified"}}
    )
    return jsonify({'message': 'Document data verified successfully'}), 200

@app.route('/editedDocumentData', methods=['POST'])
def editedDocData():
    id = request.args.get('id')
    if not id:
        return jsonify({'error': 'Missing document id'}), 400
    updatedData = request.get_json()
    if not updatedData:
        return jsonify({'error': 'Missing updated data'}), 400

    result = documents.update_one(
        {"_id": id, "status": "unverified"},
        {"$set": {"edited_data": updatedData, "status": "verified"}}
    )
    return jsonify({'message': 'Data edited and marked verified successfully'}), 200

if __name__ == '__main__':
   app.debug = True
   app.run(port=8000)