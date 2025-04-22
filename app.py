from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
import re

app = Flask(__name__)
CORS(app)

# OpenRouter API credentials
OPENROUTER_API_KEY = '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'
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'

# System prompt for crop recommendation
system_prompt = (
    "You are an agricultural expert. Based on the provided soil type, "
    "season, location, previous crop, and budget, recommend 3-4 suitable "
    "crops and a list of fertilizers to use, with crops listed first and fertilizers listed afterward."
)

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        # Parse JSON data from user
        data = request.json
        soil_type = data.get('soil_type')
        season = data.get('season')
        location = data.get('location')
        previous_crop = data.get('previous_crop')
        budget = data.get('budget')

        # Ensure all fields are provided
        if not all([soil_type, season, location, previous_crop, budget]):
            return jsonify({'error': 'All fields are required.'}), 400

        # Compose user prompt for OpenRouter API
        user_prompt = (
            f"Recommend 3-4 suitable crops and fertilizers for the following details: "
            f"Soil Type: {soil_type}, Season: {season}, Location: {location}, "
            f"Previous Crop: {previous_crop}, Budget: {budget}."
        )

        # Set up API headers and payload
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            "model": "gpt-3.5-turbo",  
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        # Make request to OpenRouter API
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        response_data = response.json()

        # Parse response and extract crops and fertilizers
        full_response = response_data['choices'][0]['message']['content']

        # Use regular expressions to split based on "Fertilizers:"
        crops = ""
        fertilizers = ""
        
        match = re.search(r"(.*?)(Fertilizers:.*)", full_response, re.DOTALL)
        if match:
            crops = match.group(1).strip()  # Part before "Fertilizers:"
            fertilizers = match.group(2).strip()  # Part starting from "Fertilizers:"
        else:
            crops = full_response.strip()  # If "Fertilizers:" is not found

        # Return recommendations as JSON
        return jsonify({'crops': crops, 'fertilizers': fertilizers})

    except Exception as e:
        # Log error and return generic message
        app.logger.error(f'Error: {str(e)}')
        return jsonify({'error': 'An error occurred, please try again later.'}), 500

if __name__ == '__main__':
    # Set up logging for error tracking
    logging.basicConfig(level=logging.ERROR)
    app.run(debug=True)
