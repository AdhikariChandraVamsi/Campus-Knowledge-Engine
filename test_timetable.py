import sys
import uuid
import os
import argparse

# Add current path to sys path to ensure 'app' imports correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.pipeline.extractor import extract_timetable_data
from app.pipeline.chunker import chunk_timetable
from app.services.llm_service import generate_answer

def run_timetable_test(pdf_path: str, question: str):
    print(f"\n📄 Loading timetable from: {pdf_path}")
    
    # 1. Extract the raw grid table out of the PDF using our new logic
    print("   Extracting grid data...")
    structured_data = extract_timetable_data(pdf_path)
    
    # 2. Process to chunks using a random UUID and generic demographics
    print("   Formatting specific timetable chunks...")
    fake_metadata = {
        "department": "CSE",
        "semester": "5",
        "section": "A",
        "university_id": str(uuid.uuid4()),
        "document_type": "timetable"
    }
    chunks = chunk_timetable(structured_data, fake_metadata)
    
    print(f"   Generated {len(chunks)} chunks.")
    
    # 3. Query LLM directly. 
    # Since timetables are usually just ~6 chunks, we can bypass ChromaDB completely 
    # for testing and feed all context directly to Gemini for perfect results!
    print(f"\n❓ Question: {question}")
    print("   Asking Gemini...\n")
    
    answer = generate_answer(question, chunks)
    
    print("✅ Answer:")
    print(f"  {answer}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Standalone Timetable Tester")
    parser.add_argument("--pdf", required=True, help="Path to the Timetable PDF file")
    parser.add_argument("--q", required=True, help="The question you want to ask")
    
    args = parser.parse_args()
    run_timetable_test(args.pdf, args.q)
