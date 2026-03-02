#!/bin/bash

# =============================================================================
# dump_project.sh
# Dumps the entire project into a single structured file for AI review.
# Place this script in the root of your project and run: bash dump_project.sh
# =============================================================================

OUTPUT_FILE="ethereum-dev-kit.txt"
SCRIPT_NAME="project_dump.sh"

# Folders and patterns to ignore
IGNORE_DIRS=("node_modules" "__pycache__" ".git" "envName" ".mypy_cache" ".pytest_cache" "dist" "build" ".next" ".venv"  ".env" "package-lock.json" "bitcoin-30.2")

# File extensions to skip (binaries, images, etc.)
SKIP_EXTENSIONS=("png" "jpg" "jpeg" "gif" "svg" "ico" "pdf" "zip" "tar" "gz" "exe" "bin" "woff" "woff2" "ttf" "eot" "pyc" "pyo" "db" "sqlite" "lock")

# Max file size to include (in bytes) — skip files larger than 100KB
MAX_SIZE=102400

# ─── Build the find exclusion flags ──────────────────────────────────────────
EXCLUDE_FLAGS=()
for dir in "${IGNORE_DIRS[@]}"; do
    EXCLUDE_FLAGS+=(-not -path "*/$dir/*" -not -name "$dir")
done

# ─── Helper: check if extension should be skipped ────────────────────────────
should_skip_extension() {
    local file="$1"
    local ext="${file##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]')
    for skip in "${SKIP_EXTENSIONS[@]}"; do
        if [[ "$ext" == "$skip" ]]; then
            return 0
        fi
    done
    return 1
}

# ─── Start writing the output file ───────────────────────────────────────────
echo "Generating project dump -> $OUTPUT_FILE ..."

cat > "$OUTPUT_FILE" <<EOF
================================================================================
  PROJECT DUMP — AI REVIEW FILE
  Generated: $(date)
  Root: $(pwd)
================================================================================

This file contains the full source code of the project, structured for AI review.
Each file is clearly delimited with its relative path and content.

IGNORED: node_modules, __pycache__, .git, envName (venv), binaries, and images.

================================================================================
  PROJECT STRUCTURE (directory tree)
================================================================================

EOF

# ─── Append directory tree ───────────────────────────────────────────────────
if command -v tree &> /dev/null; then
    TREE_IGNORE=$(IFS='|'; echo "${IGNORE_DIRS[*]}")
    tree -a -I "$TREE_IGNORE" --dirsfirst >> "$OUTPUT_FILE" 2>/dev/null
else
    # Fallback if tree is not installed
    find . "${EXCLUDE_FLAGS[@]}" | sort >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# ─── Append each file's content ──────────────────────────────────────────────
cat >> "$OUTPUT_FILE" <<EOF
================================================================================
  FILE CONTENTS
================================================================================

EOF

FILE_COUNT=0
SKIPPED_COUNT=0

while IFS= read -r -d '' filepath; do
    # Skip the output file and this script itself
    filename=$(basename "$filepath")
    if [[ "$filename" == "$OUTPUT_FILE" || "$filename" == "$SCRIPT_NAME" ]]; then
        continue
    fi

    # Skip by extension
    if should_skip_extension "$filepath"; then
        ((SKIPPED_COUNT++))
        continue
    fi

    # Skip files that are too large
    filesize=$(wc -c < "$filepath" 2>/dev/null || echo 0)
    if [[ "$filesize" -gt "$MAX_SIZE" ]]; then
        echo "────────────────────────────────────────────────────────────────────────────" >> "$OUTPUT_FILE"
        echo "FILE: ${filepath#./}" >> "$OUTPUT_FILE"
        echo "SKIPPED: File too large (${filesize} bytes > ${MAX_SIZE} bytes limit)" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE"
        ((SKIPPED_COUNT++))
        continue
    fi

    # Skip non-text files (binary check)
    if ! file "$filepath" | grep -qE 'text|json|script|empty'; then
        ((SKIPPED_COUNT++))
        continue
    fi

    # Write file header and content
    {
        echo "────────────────────────────────────────────────────────────────────────────"
        echo "FILE: ${filepath#./}"
        echo "────────────────────────────────────────────────────────────────────────────"
        cat "$filepath"
        echo ""
        echo ""
    } >> "$OUTPUT_FILE"

    ((FILE_COUNT++))

done < <(find . "${EXCLUDE_FLAGS[@]}" -type f -print0 | sort -z)

# ─── Footer ──────────────────────────────────────────────────────────────────
cat >> "$OUTPUT_FILE" <<EOF
================================================================================
  END OF PROJECT DUMP
  Files included : $FILE_COUNT
  Files skipped  : $SKIPPED_COUNT
================================================================================
EOF

echo ""
echo "✅ Done!"
echo "   Files included : $FILE_COUNT"
echo "   Files skipped  : $SKIPPED_COUNT"
echo "   Output saved to: $(pwd)/$OUTPUT_FILE"








