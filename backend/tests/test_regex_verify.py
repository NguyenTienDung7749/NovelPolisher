"""
Regex Regression Test for Chapter Pattern
==========================================
This test verifies the updated regex pattern works correctly
and doesn't produce false positives on normal text.
"""

import re
import sys

# Regex mới (đã cập nhật) - same as in chapter_split.py
REGEX_PATTERN = re.compile(
    r'^\s*chương\s+(\d{1,5})\s*(?:[:：.\-–—]\s*(.+?))?\s*$',
    re.IGNORECASE | re.MULTILINE
)

test_cases = [
    # Positive Cases (Phải bắt được - these are chapter headings)
    ("Chương 1: Mở đầu", True),
    ("CHƯƠNG 2 - Tiếp theo", True),
    ("Chương 3. Kết thúc", True),
    ("Chương 4", True),  # Không có tiêu đề
    ("  Chương 5 : Tiêu đề có space  ", True),
    ("Chương 100—Dấu gạch dài", True),
    ("Chương 999", True),  # Large number, no title

    # Negative Cases (KHÔNG được bắt - Tránh False Positive)
    ("Chương trình này rất hay", False),  # "chương trình" is a word
    ("Trong chương 5 hắn nói", False),  # Not at line start
    ("Một chương mới bắt đầu", False),  # "chương" followed by word not number
    ("Chương", False),  # Thiếu số
    ("Xem chương 1 để biết thêm chi tiết", False),  # Mid-sentence
    ("Đây là nội dung chương 2 của truyện", False),  # Mid-sentence
]

print("--- RUNNING REGEX REGRESSION TEST ---")
print(f"Pattern: {REGEX_PATTERN.pattern}")
print()

failed = False
for text, expected in test_cases:
    # Use search() like actual code - but for chapter headers, they should be on their own line
    # So we test if the ENTIRE text matches as a chapter heading line
    match = REGEX_PATTERN.search(text)
    is_match = bool(match)
    if is_match != expected:
        print(f"❌ FAIL | Input: '{text}' | Expected: {expected} | Got: {is_match}")
        failed = True
    else:
        print(f"✅ PASS | '{text}'")

print()
if failed:
    print("❌ SOME TESTS FAILED!")
    sys.exit(1)
else:
    print("🎉 ALL TESTS PASSED!")
    sys.exit(0)
