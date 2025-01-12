from fastapi import FastAPI, HTTPException
import openai
import pandas as pd
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()

app = FastAPI()

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.post("/process-docs")
async def process_docs(payload: list[dict]):
    try:
        # Step 1: Clean data
        documents = clean_data(payload)

        # Step 2: Combine all document content into a single string
        combined_content = " ".join([page["words"] for doc in documents for page in doc["content"]])
        
        # Step 3: Query the LLM for a single summary of the overall content
        overall_llm_response = query_llm(combined_content)
        
        # Step 4: Parse the LLM response
        overall_summary = overall_llm_response["summary"]
        overall_metadata = overall_llm_response["metadata"]

        # Final response
        return {
            "summary": overall_summary,
            "metadata": overall_metadata,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def clean_data(payload):
    def extract_page_content(page):
        words = " ".join([word["content"] for word in page.get("words", [])])
        return {"page_number": page["page_number"], "words": words}

    combined_documents = []
    for doc in payload:
        doc_id = doc["doc_id"]
        pages = [extract_page_content(page) for page in doc["content"]]
        combined_documents.append({
            "doc_id": doc_id,
            "total_pages": len(pages),
            "content": pages
        })

    return combined_documents


def query_llm(document_text):
    prompt = f"""
    Summarize the following document in plain text that is coherent, logically structured, 
    contextually accurate and easy to understand by a legal professional with no prior knowledge of the matter. 
    Adhere to this format:

    Title:
    [Provide a concise title for the document]

    Overview:
    [Give a brief overview of the content]

    Key Points:
    - [Key point 1]: [Explanation of key point 1]
    - [Key point 2]: [Explanation of key point 2]
    - [Additional key points as needed]

    Conclusion:
    [Provide a final remark summarizing the overall matter]

    Document:
    {document_text}
    """

    response = openai.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {
                "role": "system", 
                "content": "You are a legal assistant, with an expert knowledge in Australian law."},
            {
                "role": "user", 
                "content": prompt},
        ]
    )
    return {
        "summary": response.choices[0].message.content,
        "metadata": extract_metadata(response.choices[0].message.content)
    }


def extract_metadata(document_text):
    response = openai.chat.completions.create(
        model="gpt-4o-mini-2024-07-18",
        messages=[
            {
                "role": "system",
                "content": (f"""
                    You are a metadata extraction assistant. Your job is to extract metadata
                    from legal and technical documents in the following format:
                    
                    Key Issues:
                        - Issue 1
                        - Issue 2
                    Important Dates:
                        - Date 1: Reason for importance
                        - Date 2: Reason for importance
                    Relevant Parties:
                        - Party 1
                        - Party 2
                """
                )
            },
            {
                "role": "user",
                "content": f"Extract metadata from this document:\n\n{document_text}"
            }
        ]
    )

    llm_output = response.choices[0].message.content

    key_issues = extract_list_from_section(llm_output, "Key Issues")
    important_dates = extract_list_from_section(llm_output, "Important Dates")
    relevant_parties = extract_list_from_section(llm_output, "Relevant Parties")

    metadata_text = (
        "Key Issues:\n"
        + "\n".join([f"{issue}" for issue in key_issues])
        + "\n\nImportant Dates:\n"
        + "\n".join([f"{date}" for date in important_dates])
        + "\n\nRelevant Parties:\n"
        + "\n".join([f"{party}" for party in relevant_parties])
    )

    return metadata_text

def extract_list_from_section(text, section_name):
    section = extract_section_from_text(text, section_name)
    return [item.strip() for item in section.split("\n") if item.strip()]

def extract_section_from_text(text, section_name):
    start_marker = f"{section_name}:"
    end_marker = "\n\n"
    start_index = text.find(start_marker) + len(start_marker)
    end_index = text.find(end_marker, start_index)
    if start_index < len(start_marker):
        return ""
    return text[start_index:end_index].strip()
