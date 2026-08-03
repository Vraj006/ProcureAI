import argparse
import sys
from pathlib import Path

# Add backend root to sys.path so app module can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.document_processor import DocumentProcessor


def main():
    parser = argparse.ArgumentParser(description="Process a PDF document and extract text.")
    parser.add_argument("file_path", type=str, help="Path to the PDF file")
    args = parser.parse_args()

    file_path = Path(args.file_path)

    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)

    print(f"Processing: {file_path}")
    
    processor = DocumentProcessor()
    result = processor.process_document(file_path)

    print("\n--- Processing Results ---")
    print(f"Success: {result.success}")
    print(f"Method : {result.processing.method.value}")
    print(f"Pages  : {result.processing.page_count}")
    print(f"Time   : {result.processing.processing_time_seconds:.2f} seconds")
    
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            print(f"- {error}")
            
    if result.metadata:
        print("\nMetadata:")
        for k, v in result.metadata.model_dump().items():
            if v:
                print(f"- {k}: {v}")

    print("\n--- Text Preview (first 500 chars) ---")
    preview = result.content.raw_text[:500]
    print(preview if preview else "<No text extracted>")
    if len(result.content.raw_text) > 500:
        print("...\n[Remaining text truncated]")

if __name__ == "__main__":
    main()
