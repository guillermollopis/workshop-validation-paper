#!/bin/bash
# Semantic Scholar API search for gap validation
# Handles rate limiting with exponential backoff

BASE_URL="https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS="title,year,tldr,citationCount,url"
OUTPUT_FILE="C:/Users/Guillem/Desktop/ainpc/workshop_validation_paper/gap_search_results.txt"

# All 9 queries organized by gap
declare -a QUERIES=(
  "GAP1|lipsync voice cloning pipeline benchmark"
  "GAP1|talking head generation end-to-end comparison"
  "GAP1|audio-driven face synthesis systematic evaluation"
  "GAP3|emotional speech lipsync quality degradation"
  "GAP3|voice cloning emotion preservation evaluation"
  "GAP3|talking head neutral vs emotional benchmark"
  "GAP5|emotion congruence voice face generated video"
  "GAP5|audiovisual emotion mismatch deepfake perception"
  "GAP5|emotional coherence synthetic speech face"
)

echo "=== Semantic Scholar Gap Validation Search ===" > "$OUTPUT_FILE"
echo "Date: $(date)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

for entry in "${QUERIES[@]}"; do
  IFS='|' read -r gap query <<< "$entry"

  # URL-encode spaces as +
  encoded_query=$(echo "$query" | sed 's/ /+/g')

  echo "Searching: [$gap] $query ..."
  echo "-------------------------------------------" >> "$OUTPUT_FILE"
  echo "[$gap] Query: $query" >> "$OUTPUT_FILE"
  echo "-------------------------------------------" >> "$OUTPUT_FILE"

  # Retry with exponential backoff
  max_retries=6
  wait_time=30
  success=false

  for ((attempt=1; attempt<=max_retries; attempt++)); do
    echo "  Attempt $attempt (waiting ${wait_time}s first)..."
    sleep $wait_time

    response=$(curl -s -w "\n__HTTP__%{http_code}" \
      "${BASE_URL}?query=${encoded_query}&limit=5&fields=${FIELDS}" 2>/dev/null)

    http_code=$(echo "$response" | grep "__HTTP__" | sed 's/__HTTP__//')
    body=$(echo "$response" | grep -v "__HTTP__")

    if [ "$http_code" = "200" ]; then
      success=true
      # Parse and format results
      echo "$body" | python3 -c "
import sys, json
data = json.load(sys.stdin)
total = data.get('total', 0)
print(f'Total results: {total}')
print()
for i, paper in enumerate(data.get('data', []), 1):
    title = paper.get('title', 'N/A')
    year = paper.get('year', 'N/A')
    citations = paper.get('citationCount', 0)
    url = paper.get('url', '')
    tldr = paper.get('tldr', {})
    tldr_text = tldr.get('text', 'No TLDR available') if tldr else 'No TLDR available'
    print(f'{i}. [{year}] {title}')
    print(f'   Citations: {citations}')
    print(f'   URL: {url}')
    print(f'   TLDR: {tldr_text}')
    print()
" >> "$OUTPUT_FILE" 2>/dev/null
      echo "  Success!"
      break
    else
      echo "  Got HTTP $http_code, retrying..."
      wait_time=$((wait_time * 2))
      if [ $wait_time -gt 300 ]; then
        wait_time=300
      fi
    fi
  done

  if [ "$success" = false ]; then
    echo "FAILED after $max_retries attempts" >> "$OUTPUT_FILE"
    echo ""  >> "$OUTPUT_FILE"
  fi
done

echo "=== SEARCH COMPLETE ===" >> "$OUTPUT_FILE"
echo "Done! Results saved to $OUTPUT_FILE"
