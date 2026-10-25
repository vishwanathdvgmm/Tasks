import argparse
import json
from .models import AnswerRequest
from .pipeline import RAGPipeline

def main() -> None:
    parser = argparse.ArgumentParser(description="Task 07 Enterprise RAG demo")
    parser.add_argument("command", choices=["demo", "ask"])
    parser.add_argument("question", nargs="?", default="What are the requirements for remote access?")
    args = parser.parse_args()
    result = RAGPipeline().answer(AnswerRequest(question=args.question))
    print(json.dumps(result.model_dump(), indent=2))

if __name__ == "__main__":
    main()
