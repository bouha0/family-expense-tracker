from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
import google.generativeai as genai
import PIL.Image
import json
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set your API key (use environment variables for production)
api_key = os.getenv('GEMINI_API_KEY', 'YOUR_API_KEY')
genai.configure(api_key=api_key)

# Allowed file extensions and maximum file size (5MB)
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_image():
    # Check if the request contains a file
    if 'image' not in request.files:
        logger.error("No image part in the request")
        return jsonify({'error': 'No image part'}), 400

    file = request.files['image']

    # Check if a file was selected
    if file.filename == '':
        logger.error("No file selected")
        return jsonify({'error': 'No selected file'}), 400

    # Validate file type and size
    if not allowed_file(file.filename):
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({'error': 'Invalid file type. Allowed types: jpg, jpeg, png'}), 400

    if len(file.read()) > MAX_FILE_SIZE:
        logger.error("File size exceeds the limit")
        return jsonify({'error': 'File size exceeds the limit (5MB)'}), 400
    file.seek(0)  # Reset file pointer after reading

    # Save the uploaded file securely
    filename = secure_filename(file.filename)
    image_path = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)  # Create uploads directory if it doesn't exist
    file.save(image_path)
    logger.info(f"File saved: {image_path}")

    try:
        # Process the image using Gemini API
        model = genai.GenerativeModel(model_name="gemini-1.5-pro")
        image = PIL.Image.open(image_path)
        prompt = "Extract all fields and return the response in JSON format."
        response = model.generate_content([prompt, image])

        # Strip Markdown formatting (if any)
        raw_response = response.text.strip('```json\n').strip('```')

        # Parse the response as JSON
        data = json.loads(raw_response)
        logger.info("Image processed successfully")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response: {e}")
        return jsonify({'error': 'Failed to process the image. Please try again.'}), 500

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

    finally:
        # Clean up the uploaded image
        if os.path.exists(image_path):
            os.remove(image_path)
            logger.info(f"File removed: {image_path}")

    # Return the extracted data
    return jsonify(data)

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)
