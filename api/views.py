from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import openai
import os
import json

# Use environment variable for OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")
print(f"Loaded OpenAI API Key: {openai.api_key}")


# Render main HTML page
def render_main_page(request):
    return render(request, 'api/upload.html')


# File upload and processing view
@csrf_exempt
def upload_file_view(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        try:
            # Ensure the output directory exists
            os.makedirs("output", exist_ok=True)

            # Process file using pandas (assuming .xlsx format)
            df = pd.read_excel(uploaded_file)

            # Combine content into a single string
            content = extract_content_from_excel(df)

            # Save processed output (optional)
            output_path = "output/processed_file.xlsx"
            df.to_excel(output_path, index=False)

            return JsonResponse({"message": "File uploaded and processed successfully", "content": content})
        except ValueError as ve:
            return JsonResponse({"error": f"Invalid file format: {ve}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error processing file: {e}"}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

# Extract content from DataFrame


def extract_content_from_excel(df):
    """
    Extracts all text content from an Excel DataFrame.
    Combines all columns and rows into a single string.
    """
    try:
        text_content = df.astype(str).agg(' '.join, axis=1).str.cat(sep=' ')
        return text_content
    except Exception as e:
        return f"Error extracting content: {e}"

# Question and Answer view using OpenAI API


@csrf_exempt
def qa_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            question = data.get('question')
            document_content = data.get('content')

            if not question or not document_content:
                return JsonResponse({"error": "Missing question or document content"}, status=400)

            # Generate response using OpenAI's ChatCompletion
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # Use a supported model like gpt-3.5-turbo or gpt-4
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Answer the question based on this content:\n\n{document_content}\n\nQuestion: {question}"}
                ],
                max_tokens=200
            )

            # Extract answer
            answer = response["choices"][0]["message"]["content"].strip()
            return JsonResponse({"answer": answer}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data provided"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Failed to process the question: {str(e)}"}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)

