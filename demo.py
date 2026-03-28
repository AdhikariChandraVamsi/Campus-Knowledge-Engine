"""
Panel Review Demo Script
Runs the complete flow:
  1. Login as admin
  2. Upload timetable PDF
  3. Wait for pipeline to complete
  4. Login as student
  5. Ask a question
  6. Print the answer

Usage:
  python demo.py --pdf /path/to/timetable.pdf --university_id YOUR_UNI_ID
"""
import argparse
import time
import requests
import sys

BASE_URL = "http://localhost:8000"

def print_step(n, msg):
    print(f"\n{'='*55}")
    print(f"  STEP {n}: {msg}")
    print(f"{'='*55}")

def check_server():
    try:
        r = requests.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        print("✅ Server is running")
    except Exception:
        print("❌ Server not running. Start with: uvicorn app.main:app --reload")
        sys.exit(1)

def login(email, password):
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        print(f"❌ Login failed: {r.text}")
        sys.exit(1)
    data = r.json()
    print(f"✅ Logged in as {email} | Role: {data['role']}")
    return data["access_token"]

def upload_pdf(token, pdf_path, university_id):
    headers = {"Authorization": f"Bearer {token}"}
    with open(pdf_path, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/documents/upload",
            headers=headers,
            files={"file": (pdf_path.split("/")[-1], f, "application/pdf")},
            data={
                "document_type": "timetable",
                "department": "CSE",
                "semester": "5",
                "section": "F",
                "regulation": "2023",
                "academic_year": "2024-25",
            },
        )
    if r.status_code not in (200, 201, 202):
        print(f"❌ Upload failed: {r.text}")
        sys.exit(1)
    doc = r.json()
    print(f"✅ Uploaded: {doc['original_filename']}")
    print(f"   Document ID: {doc['id']}")
    print(f"   Status: {doc['status']}")
    return doc["id"]

def wait_for_indexing(token, doc_id, timeout=60):
    headers = {"Authorization": f"Bearer {token}"}
    print(f"⏳ Waiting for pipeline to index document", end="", flush=True)
    for _ in range(timeout):
        r = requests.get(f"{BASE_URL}/documents/", headers=headers)
        docs = r.json()
        doc = next((d for d in docs if d["id"] == doc_id), None)
        if doc:
            status = doc["status"]
            if status == "indexed":
                print(f"\n✅ Indexed! Chunks created: {doc['chunk_count']}")
                return True
            elif status == "failed":
                print(f"\n❌ Pipeline failed for document {doc_id}")
                return False
        print(".", end="", flush=True)
        time.sleep(1)
    print(f"\n⚠️  Timeout — check server logs")
    return False

def ask_question(token, question):
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.post(
        f"{BASE_URL}/query/",
        headers=headers,
        json={"question": question},
    )
    if r.status_code != 200:
        print(f"❌ Query failed: {r.text}")
        return
    result = r.json()

    print(f"\n  Question: {question}")
    print(f"  {'─'*50}")

    if result.get("clarification_needed"):
        print(f"  🔁 Clarification needed: {result['clarification_needed']}")
        return

    if result["was_answered"]:
        print(f"  ✅ Answer:\n\n  {result['answer']}")
        print(f"\n  Chunks used: {len(result['chunks_used'])}")
        for c in result["chunks_used"]:
            print(f"    - {c['chunk_id']} | score: {c['similarity_score']} | type: {c['document_type']}")
    else:
        print(f"  ⚠️  Not answered (below similarity threshold)")
        print(f"  Response: {result['answer']}")

def main():
    parser = argparse.ArgumentParser(description="CKE Panel Review Demo")
    parser.add_argument("--pdf", required=True, help="Path to timetable PDF")
    parser.add_argument("--university_id", required=True, help="University ID from seed.py")
    args = parser.parse_args()

    print("\n🚀 Campus Knowledge Engine — Panel Review Demo\n")

    # Step 1: Server health
    print_step(1, "Verify server is running")
    check_server()

    # Step 2: Admin login
    print_step(2, "Admin login")
    admin_token = login("admin@amrita.edu", "Admin@1234")

    # Step 3: Upload PDF
    print_step(3, f"Upload timetable PDF: {args.pdf}")
    doc_id = upload_pdf(admin_token, args.pdf, args.university_id)

    # Step 4: Wait for indexing
    print_step(4, "Pipeline: Extract → Clean → Chunk → Embed → Store")
    indexed = wait_for_indexing(admin_token, doc_id)

    if not indexed:
        print("⚠️  Skipping query step — document not indexed")
        sys.exit(1)

    # Step 5: Student login
    print_step(5, "Student login")
    student_token = login("student@amrita.edu", "Student@1234")

    # Step 6: Ask questions
    print_step(6, "Student queries")
    questions = [
        "What is my timetable on Monday?",
        "When do I have my first class on Friday?",
        "What subject do I have at 9 AM on Wednesday?",
    ]
    for q in questions:
        ask_question(student_token, q)
        time.sleep(1)

    print(f"\n\n{'='*55}")
    print("  ✅ DEMO COMPLETE — All systems operational")
    print(f"{'='*55}\n")
    print("  Swagger UI: http://localhost:8000/docs")
    print("  Health:     http://localhost:8000/health\n")

if __name__ == "__main__":
    main()
