#!/usr/bin/env python3
"""Extract chapters from the chat history HTML file"""

# Read the HTML file
with open('architecture_advice.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove HTML tags
import re
text = re.sub(r'<[^>]*>', '', content)

# Split by newlines
lines = text.split('\n')

# Chapter markers with their line numbers
chapters = [
    (0, 13014, 13512),
    (1, 13514, 14058),
    (2, 14061, 14666),
    (3, 14669, 15275),
    (4, 15277, 15834),
    (5, 15837, 16458),
    (6, 16460, 17176),
    (7, 17178, 17795),
    (8, 17797, 18341),
    (9, 18342, 18998),
    (10, 19000, 19472),
    (11, 19474, 20102),
    (12, 20104, 20701),
    (13, 20703, 21374),
    (14, 21376, 22084),
    (15, 22086, 22759),
    (16, 22761, 23323),
    (17, 23325, 24046),
    (18, 24048, 24574),
    (19, 24576, 25237),
    (20, 25239, 25865),
    (21, 25867, 26497),
    (22, 26499, 27213),
    (23, 27215, 27802),
    (24, 27804, 28506),
    (25, 28508, 28986),
    (26, 28988, 29696),
    (27, 29698, 30351),
    (28, 30353, 31000),  # approximate end
]

# Extract each chapter
for chapter_num, start, end in chapters:
    # Adjust for 0-based indexing
    chapter_content = '\n'.join(lines[start:end])
    
    # Save to file
    filename = f'chapter_{chapter_num:02d}.txt'
    with open(f'book_extracted/{filename}', 'w', encoding='utf-8') as f:
        f.write(chapter_content)
    print(f'Extracted Chapter {chapter_num}: {len(chapter_content)} chars')

print('Done!')
