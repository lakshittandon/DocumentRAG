#!/bin/zsh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE_FILE="$ROOT_DIR/docs/project-plan.txt"
OUTPUT_FILE="$ROOT_DIR/docs/Reliable_RAG_Project_Plan.docx"

textutil -convert docx -output "$OUTPUT_FILE" "$SOURCE_FILE" -font Helvetica -fontsize 12
echo "Exported project plan to $OUTPUT_FILE"
