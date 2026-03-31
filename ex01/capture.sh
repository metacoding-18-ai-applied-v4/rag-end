#!/bin/bash
cd "/Users/nomadlab/Desktop/김주혁/workspace/coding-study/집필에이전트 v2/projects/사내AI비서_v2/code/ex01"
mkdir -p ../../assets/CH01

SCRIPT="../../../../.claude/skills/screenshot/scripts/book_capture.py"

python3 "$SCRIPT" --cmd ".venv/bin/python step1_fail.py" --cwd "." --output "../../assets/CH01/01_step1-hallucination.png" --title "step1_fail.py"
python3 "$SCRIPT" --cmd ".venv/bin/python step2_context.py" --cwd "." --output "../../assets/CH01/01_step2-context.png" --title "step2_context.py"
python3 "$SCRIPT" --cmd ".venv/bin/python step3_rag.py" --cwd "." --output "../../assets/CH01/01_step3-rag.png" --title "step3_rag.py"
python3 "$SCRIPT" --cmd ".venv/bin/python step3_rag_no_chunking.py" --cwd "." --output "../../assets/CH01/01_no-chunking-compare.png" --title "step3_rag_no_chunking.py"
python3 "$SCRIPT" --cmd ".venv/bin/python step4_rag.py" --cwd "." --output "../../assets/CH01/01_step4-rag.png" --title "step4_rag.py"
