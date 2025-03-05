from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

import google.generativeai as genai
import os
from dotenv import load_dotenv
import io
import tempfile
import magic  # for file type detection
from PyPDF2 import PdfReader
import time
import random
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Load environment variables
load_dotenv()

# Create FastAPI app instance
app = FastAPI(
    title="Legal Document Simplifier API",
    description="API for simplifying legal documents using Google's Gemini AI",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
try:
    # List available models
    available_models = genai.list_models()
    print("Available models:", [model.name for model in available_models])
    
    # Use the specific Gemini model
    model_name = 'models/gemini-1.5-pro-latest'
    print(f"Using model: {model_name}")
    model = genai.GenerativeModel(model_name)
    print("Model initialized successfully")
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    model = None

# Define data models
class ChatMessage(BaseModel):
    message: str
    document_content: Optional[str] = None

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Legal Document Simplifier API"}

def chunk_text(text: str, chunk_size: int = 15000) -> List[str]:
    """Split text into chunks of approximately equal size"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        word_size = len(word) + 1  # +1 for space
        if current_size + word_size > chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = word_size
        else:
            current_chunk.append(word)
            current_size += word_size
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

async def read_pdf_file(file_content: bytes) -> str:
    """Read content from a PDF file"""
    # Create a temporary file to store the uploaded content
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name
    
    try:
        # Read the PDF using PyPDF2
        reader = PdfReader(temp_file_path)
        
        # Extract text from all pages
        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text.strip():
                text_parts.append(text)
        
        # Join all text parts with proper spacing
        return '\n\n'.join(text_parts)
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        raise HTTPException(
            status_code=400,
            detail="Could not read the PDF document. Please ensure it's a valid PDF file."
        )
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except:
            pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type((Exception)),
    before_sleep=lambda retry_state: print(f"Retrying after error: {retry_state.outcome.exception()}")
)
async def simplify_text_chunk(chunk: str) -> str:
    """Simplify a single chunk of text with retry logic"""
    try:
        prompt = f"""You are a legal document simplifier. Simplify the following legal document section into easy-to-understand language while preserving its legal essence. Use simple terms and clear explanations.

Document section:
{chunk}"""

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Error in simplify_text_chunk: {e}")
        # Add a random delay between 2-5 seconds before retrying
        time.sleep(random.uniform(2, 5))
        raise

async def process_chunks_with_rate_limit(chunks: List[str]) -> List[str]:
    """Process chunks with rate limiting"""
    simplified_chunks = []
    for i, chunk in enumerate(chunks, 1):
        print(f"Processing chunk {i}/{len(chunks)}")
        try:
            # Add a small random delay between chunks (1-3 seconds)
            if i > 1:
                delay = random.uniform(1, 3)
                print(f"Waiting {delay:.1f} seconds before processing next chunk...")
                time.sleep(delay)
            
            simplified_chunk = await simplify_text_chunk(chunk)
            simplified_chunks.append(simplified_chunk)
        except Exception as e:
            print(f"Error processing chunk {i}: {e}")
            # If a chunk fails, try with a smaller chunk size
            sub_chunks = chunk_text(chunk, chunk_size=8000)
            for sub_chunk in sub_chunks:
                try:
                    # Add a small delay between sub-chunks
                    time.sleep(random.uniform(1, 2))
                    simplified_sub_chunk = await simplify_text_chunk(sub_chunk)
                    simplified_chunks.append(simplified_sub_chunk)
                except Exception as sub_e:
                    print(f"Error processing sub-chunk: {sub_e}")
                    # If all retries fail, add an error message
                    simplified_chunks.append(f"[Error processing this section: {str(sub_e)}]")
    
    return simplified_chunks

# Document simplification endpoint
@app.post("/simplify")
async def simplify_document(file: UploadFile = File(...)):
    try:
        if model is None:
            raise HTTPException(
                status_code=500,
                detail="Gemini model not initialized properly. Please check your API key and model configuration."
            )
            
        # Read the uploaded file
        content = await file.read()
        
        # Detect file type using python-magic
        file_type = magic.from_buffer(content, mime=True)
        print(f"Detected file type: {file_type}")
        
        # Process the file based on its type
        if file_type == 'application/pdf':
            document_text = await read_pdf_file(content)
        elif file_type == 'text/plain':
            try:
                document_text = content.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    document_text = content.decode("latin-1")
                except:
                    raise HTTPException(
                        status_code=400,
                        detail="Could not decode text file content. Please ensure it's a valid text file."
                    )
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Please upload a .txt or .pdf file."
            )
        
        # Check if the document is empty
        if not document_text.strip():
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is empty"
            )
        
        print(f"Extracted text length: {len(document_text)} characters")
        
        # Split the document into chunks
        chunks = chunk_text(document_text)
        print(f"Split document into {len(chunks)} chunks")
        
        # Process chunks with rate limiting
        simplified_chunks = await process_chunks_with_rate_limit(chunks)
        
        # Combine all simplified chunks
        simplified_text = '\n\n'.join(simplified_chunks)
        
        return {
            "original": document_text,
            "simplified": simplified_text
        }
    except Exception as e:
        print(f"Error processing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chat endpoint
@app.post("/chat")
async def chat_with_document(chat_message: ChatMessage):
    try:
        # Prepare the context for the chat
        prompt = f"""You are a helpful legal assistant. Answer the following question about the legal document in a clear and concise manner.

Question: {chat_message.message}

Document content:
{chat_message.document_content}"""
        
        # Use Gemini to generate a response with retry logic
        response = await simplify_text_chunk(prompt)
        
        return {
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 