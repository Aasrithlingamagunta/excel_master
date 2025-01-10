from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import os
import json
from transformers import pipeline
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load Hugging Face API token from environment variable
HUGGING_FACE_API_TOKEN = os.getenv("HUGGING_FACE_API_TOKEN")
if not HUGGING_FACE_API_TOKEN:
    logger.error("Hugging Face API token is not set. Please configure it in the environment.")

# Initialize Hugging Face Q&A pipeline
try:
    qa_pipeline = pipeline(
        "question-answering",
        model="distilbert-base-uncased-distilled-squad",
        use_auth_token=HUGGING_FACE_API_TOKEN
    )
    logger.info("Hugging Face pipeline initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Hugging Face pipeline: {e}")
    qa_pipeline = None


def render_main_page(request):
    """Render the main page for file upload and Q&A."""
    return render(request, 'api/upload.html')


@csrf_exempt
def upload_file_view(request):
    """Handle file upload and extract content from the document."""
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    try:
        # Ensure output directory exists
        os.makedirs("output", exist_ok=True)

        # Load the Excel file into a DataFrame
        df = pd.read_excel(uploaded_file)
        content_chunks = extract_content_from_excel(df)

        # Save the processed file (optional)
        output_path = "output/processed_file.xlsx"
        df.to_excel(output_path, index=False)

        return JsonResponse({"message": "File uploaded and processed successfully", "content": content_chunks})
    except ValueError as ve:
        logger.error("Invalid file format: %s", ve)
        return JsonResponse({"error": f"Invalid file format: {ve}"}, status=400)
    except Exception as e:
        logger.error("Error processing file: %s", e)
        return JsonResponse({"error": f"Error processing file: {e}"}, status=500)


def chunk_text(content, chunk_size=500):
    """
    Split large text into smaller chunks of a specified size.

    Args:
        content (str): The text content to split.
        chunk_size (int): The maximum number of words in each chunk.

    Returns:
        generator: A generator yielding text chunks.
    """
    words = content.split()
    for i in range(0, len(words), chunk_size):
        yield " ".join(words[i:i + chunk_size])


def extract_content_from_excel(df):
    """
    Extract meaningful text content from a DataFrame and split it into chunks.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        list: A list of cleaned, context-aware text chunks.
    """
    try:
        rows = []
        for _, row in df.iterrows():
            # Combine key-value pairs or meaningful data into a single string
            cleaned_row = " ".join(
                f"{str(col).strip()}: {str(value).strip()}"
                for col, value in row.items()
                if pd.notna(value) and str(value).strip()  # Convert value to string and check if non-empty
            )
            if cleaned_row:  # Only include non-empty rows
                rows.append(cleaned_row)

        # Combine all rows into a single text
        text_content = " ".join(rows)

        # Chunk the text into manageable pieces
        return list(chunk_text(text_content, chunk_size=500))
    except Exception as e:
        logger.error("Error extracting content: %s", e)
        return [f"Error extracting content: {e}"]


@csrf_exempt
def qa_view(request):
    """Process the user's question and return the best answer."""
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)

    if qa_pipeline is None:
        return JsonResponse({"error": "Hugging Face pipeline is not initialized."}, status=500)

    try:
        data = json.loads(request.body)
        question = data.get('question')
        document_content = data.get('content')

        if not question or not document_content:
            return JsonResponse({"error": "Missing question or document content"}, status=400)

        best_answer = None
        best_score = 0

        for chunk in document_content:
            try:
                logger.info("Processing chunk: %s", chunk[:100])  # Log the first 100 characters of the chunk
                response = qa_pipeline(question=question, context=chunk)
                answer = response.get('answer', 'No answer found.')
                score = response.get('score', 0)

                logger.info("Chunk Score: %f, Answer: %s", score, answer)

                if score > best_score:
                    best_score = score
                    best_answer = answer
            except Exception as e:
                logger.error("Error processing chunk: %s", e)

        return JsonResponse({"answer": best_answer or "No relevant answer found."}, status=200)
    except json.JSONDecodeError:
        logger.error("Invalid JSON data provided")
        return JsonResponse({"error": "Invalid JSON data provided"}, status=400)
    except Exception as e:
        logger.error("Failed to process the question: %s", e)
        return JsonResponse({"error": f"Failed to process the question: {e}"}, status=500)
