from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import os
import json
from transformers import pipeline
import logging

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Hugging Face Q&A pipeline
try:
    qa_pipeline = pipeline(
        "question-answering",
        model="distilbert-base-uncased-distilled-squad",
        use_auth_token=os.getenv("HUGGING_FACE_API_TOKEN", "")
    )
    logger.info("Hugging Face pipeline initialized successfully.")
except Exception as e:
    logger.error(f"Failed to initialize Hugging Face pipeline: {e}")
    qa_pipeline = None

def render_main_page(request):
    return render(request, 'api/upload.html')

@csrf_exempt
def upload_file_view(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Invalid request method"}, status=405)

    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({"error": "No file uploaded"}, status=400)

    try:
        os.makedirs("output", exist_ok=True)
        df = pd.read_excel(uploaded_file)
        content_chunks = extract_content_from_excel(df)

        output_path = "output/processed_file.xlsx"
        df.to_excel(output_path, index=False)

        return JsonResponse({"message": "File uploaded and processed successfully", "content": content_chunks})
    except Exception as e:
        logger.error("Error processing file: %s", e)
        return JsonResponse({"error": f"Error processing file: {e}"}, status=500)

def split_large_content(content, chunk_size=500):
    words = content.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)]

def extract_content_from_excel(df):
    try:
        chunks = []
        for _, row in df.iterrows():
            row_content = " ".join(
                f"{str(col).strip()}: {str(value).strip()}"
                for col, value in row.items()
                if pd.notna(value) and str(value).strip()
            )
            if row_content:
                chunks.extend(split_large_content(row_content, chunk_size=500))
        return chunks
    except Exception as e:
        logger.error("Error extracting content from rows: %s", e)
        return [f"Error extracting content: {e}"]

@csrf_exempt
def qa_view(request):
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

        best_answer, best_score = None, 0

        for chunk in document_content:
            try:
                response = qa_pipeline(question=question, context=chunk)
                answer, score = response.get('answer', ''), response.get('score', 0)

                if score > best_score:
                    best_score, best_answer = score, answer
            except Exception as e:
                logger.error("Error processing chunk: %s", e)

        return JsonResponse({"answer": best_answer or "No relevant answer found."}, status=200)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data provided"}, status=400)
    except Exception as e:
        logger.error("Failed to process the question: %s", e)
        return JsonResponse({"error": f"Failed to process the question: {e}"}, status=500)
