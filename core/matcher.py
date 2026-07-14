import re

def normalize_word(word):
    """Cleans a single word for bulletproof Arabic matching."""
    word = re.sub(r'[\u064B-\u065F]', '', word) # Remove Tashkeel
    word = re.sub(r'[^\w\s]', '', word)         # Remove Punctuation
    word = re.sub(r'[أإآ]', 'ا', word)          # Normalize Alef
    word = re.sub(r'ة', 'ه', word)              # Normalize Taa
    word = re.sub(r'ى', 'ي', word)              # Normalize Yaa
    return word.lower()

def find_all_sequences(target_words, srt_words):
    """Finds ALL occurrences of target_words in srt_words."""
    n = len(target_words)
    if n == 0:
        return []

    matches = []
    for i in range(len(srt_words) - n + 1):
        match = True
        for j in range(n):
            if srt_words[i+j]['word'] != target_words[j]:
                match = False
                break
        if match:
            matches.append(i)
    return matches

def find_precise_clip_boundaries(segment_text, parsed_subtitles):
    if not parsed_subtitles or not segment_text.strip():
        return 0.0, 5.0

    # 1. Build a flattened list of EVERY WORD in the SRT
    srt_words = []
    for block in parsed_subtitles:
        words = block['text'].split()
        for w in words:
            clean_w = normalize_word(w)
            if clean_w:
                srt_words.append({
                    'word': clean_w,
                    'start': block['start'],
                    'end': block['end']
                })

    if not srt_words:
        return 0.0, 5.0

    # 2. Clean the user's pasted segment into a list of words
    segment_words = [normalize_word(w) for w in segment_text.split()]
    segment_words = [w for w in segment_words if w]

    if not segment_words:
        return 0.0, 5.0

    start_time = 0.0
    end_time = 0.0
    
    start_idx = -1
    end_idx = -1



    # --- 3. FIND START TIME (N-Gram Expansion) ---
    best_start_matches = []
    for size in range(1, len(segment_words) + 1):
        target = segment_words[:size]
        matches = find_all_sequences(target, srt_words)
        
        if len(matches) > 0:
            best_start_matches = matches
            
        if len(matches) == 1:
            break # Unique match found!

    if best_start_matches:
        start_idx = best_start_matches[0]
        start_time = srt_words[start_idx]['start']

    # --- 4. FIND END TIME (Reverse N-Gram Expansion) ---
    best_end_matches = []
    best_size = 1
    for size in range(1, len(segment_words) + 1):
        target = segment_words[-size:]
        matches = find_all_sequences(target, srt_words)
        
        # Filter matches so they must be at or after start_idx
        if start_idx != -1:
            valid_matches = [m for m in matches if m >= start_idx]
        else:
            valid_matches = matches

        if len(valid_matches) > 0:
            best_end_matches = valid_matches
            best_size = size
            
        if len(valid_matches) == 1:
            break # Unique match found!

    if best_end_matches:
        # Pick the closest valid match after start_idx
        end_idx = best_end_matches[0] + best_size - 1
        end_time = srt_words[end_idx]['end']

    # --- 5. FALLBACKS ---
    if start_idx == -1 and end_idx != -1:
        start_time = max(0.0, end_time - 5.0)
    elif end_idx == -1 and start_idx != -1:
        end_time = start_time + 5.0
    elif start_idx == -1 and end_idx == -1:
        start_time = 0.0
        end_time = 5.0

    if end_time <= start_time:
        end_time = start_time + 5.0

    return start_time, end_time