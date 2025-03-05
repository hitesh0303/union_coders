# AI-Powered Legal Document Simplifier

This application helps users understand complex legal documents by simplifying them into easy-to-understand language while preserving their legal essence. It also includes a chatbot feature that can answer questions about the document content.

## Features

- Upload and process legal documents
- AI-powered document simplification using Google's Gemini
- Interactive chatbot for document-related queries
- Modern, responsive user interface
- Side-by-side comparison of original and simplified text

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- Google API key (for Gemini)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd legal-doc-simplifier
```

2. Set up the backend:
```bash
# Create and activate a virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file in the root directory and add your Google API key
echo "GOOGLE_API_KEY=your_api_key_here" > .env
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

## Running the Application

1. Start the backend server:
```bash
# From the root directory
uvicorn main:app --reload
```

2. Start the frontend development server:
```bash
# From the frontend directory
npm start
```

3. Open your browser and navigate to `http://localhost:3000`

## Usage

1. Click the "Upload Legal Document" button to select a legal document file
2. Wait for the document to be processed
3. View the original and simplified versions side by side
4. Use the chat interface to ask questions about the document content

## API Endpoints

- `POST /simplify`: Upload and simplify a legal document
- `POST /chat`: Send questions about the document content

## Technologies Used

- Backend:
  - FastAPI
  - Google Gemini API
  - Python

- Frontend:
  - React
  - Material-UI
  - Axios

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 