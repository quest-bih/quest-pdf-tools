import re
from sections import *

all_section_terms = (METHODS_TERMS + RESULTS_TERMS + DISCUSSION_TERMS + 
                        REFERENCES_TERMS + FUNDING + INTRODUCTION + CAS + 
                        ACNOWLEDGEMENTS + AUTH_CONT + ABBREVIATIONS + CONCLUSION + ABSTRACT +
                        LIMITATIONS + COI + SUPP_DATA + DATA_AVAILABILITY + ETHICS)

def remove_duplicate_pargraphs(text):
    """
    Removes duplicate paragraphs from text while preserving empty lines.
    
    Parameters:
    ----------
    text : str
        The input text to process.
        
    Returns:
    -------
    str
        The text with duplicate paragraphs removed, empty lines preserved.
    """
    # Split text into paragraphs and filter out duplicates while keeping empty lines
    paragraphs = [p for i, p in enumerate(text.split('\n')) 
                 if p.strip() == ''or p.strip() in all_section_terms or text.split('\n').index(p) == i]

    # Join paragraphs back into text
    return '\n'.join(paragraphs)
    
def extract_section(text, section_terms):
    """
    Extracts a specific section from the text based on provided section terms.
    A section starts with its terms (preceded by an empty line) and ends when another section begins.
    
    The function handles various section header formats:
    - Regular format (e.g., "Methods")
    - Spaced letters (e.g., "M E T H O D S")
    - Numbered sections (e.g., "1. Methods", "I. Methods")
    - Sections with pipes (e.g., "1 | INTRODUCTION")
    - Inline sections (e.g., "Methods: text continues...")
    
    Parameters:
    ----------
    text : str
        The input text from which to extract the section. Should be raw text content
        that may contain multiple sections.
    section_terms : list
        List of terms that indicate the start of the section. Case-insensitive matching
        is used for these terms.
        
    Returns:
    -------
    str
        The extracted section text, including the section header keyword. Returns an empty string
        if the section is not found. If a detected keyword is immediately followed by another
        section keyword, that match is omitted. If multiple sections are found, returns the longest one.
        
    Notes:
    -----
    - The function first removes duplicate paragraphs from the input text
    - Section matching is case-insensitive
    - Section headers must be preceded by an empty line (except for inline sections)
    - Section ends when another known section header is encountered
    - The detected keyword is included in the extracted text
    - If a detected keyword is directly followed by another section keyword, that match is skipped
    - When multiple sections match, the longest one is returned
    """
    
    # Create regex patterns for different formatting styles of the target section
    # Handle regular format, spaced letters, numbered sections, and sections with colons
    # All patterns require the keyword to be followed by newline or colon
    section_patterns = [
        # Regular format: "Methods" followed by newline or colon
        r'\n\s*(' + '|'.join(map(re.escape, section_terms)) + r')\s*[\n:]',
        
        # Spaced letters: "M E T H O D S" followed by newline or colon
        r'\n\s*(' + '|'.join(' '.join(term) for term in [[c for c in term] for term in section_terms]) + r')\s*[\n:]',
        
        # Numbered sections: "1. Methods", "I. Methods", etc. followed by newline or colon
        r'\n\s*(?:\d+\.|\[?\d+\]?\.?|[IVXivx]+\.)\s*(' + '|'.join(map(re.escape, section_terms)) + r')\s*[\n:]',
        
        # Numbered sections with pipe: "1 | INTRODUCTION" followed by newline or colon
        r'\n\s*(?:\d+\s*\|\s*)(' + '|'.join(map(re.escape, section_terms)) + r')\s*[\n:]',
        
        # Inline matching: keyword followed by colon (with optional content after)
        r'\n\s*(' + '|'.join(map(re.escape, section_terms)) + r')\s*:([^\n]*)'    
    ]
    
    # Find all occurrences of the target section using any of the patterns
    section_matches = []
    
    for pattern in section_patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        # print(matches)
        for match in matches:
            section_matches.append((match.start(), match.end(), pattern, match))
    
    # Sort matches by position in text
    section_matches.sort(key=lambda x: x[0])
    
    # Create patterns for different formatting styles of the next section
    next_section_patterns = []
    for term in [term for term in all_section_terms if term not in section_terms]:
        # Regular format - escape the term and add word boundaries
        escaped_term = re.escape(term)
        # Add word boundary at start and end, but handle spaces in multi-word terms
        if ' ' in term:
            # Multi-word term: ensure word boundary at start and end, but allow spaces in between
            next_section_patterns.append(r'\b' + escaped_term + r'\b')
        else:
            # Single-word term: word boundaries on both sides
            next_section_patterns.append(r'\b' + escaped_term + r'\b')
        # Spaced letters
        spaced_term = ' '.join([c for c in term])
        next_section_patterns.append(r'\b' + re.escape(spaced_term) + r'\b')
    
    # Create patterns for next section - only stop if keyword is on a new line or followed by colon
    # Pattern 1: Keyword on a new line (preceded by \n) - must be followed by newline or colon
    next_section_pattern = r'\n\s*(?:\d+\.|\[?\d+\]?\.?|[IVXivx]+\.|\d+\s*\|\s*)?\s*(' + '|'.join(next_section_patterns) + r')\s*[\n:]'
    # Pattern 2: Keyword followed by colon - must be at start of line (preceded by \n) to avoid matching keywords in reference entries
    next_inline_pattern = r'\n\s*(?:\d+\.|\[?\d+\]?\.?|[IVXivx]+\.|\d+\s*\|\s*)?\s*(' + '|'.join(next_section_patterns) + r')\s*:'
    
    # Extract all sections and find the longest one
    extracted_sections = []
    
    for section_start, section_end_match, pattern, match_obj in section_matches:
        # Check if immediately after this section keyword there's another section keyword starting a new section
        # Get text immediately after the match (first 150 chars to check for immediate next section)
        text_after_match = text[section_end_match:section_end_match + 150]
        
        # Only skip if another section keyword appears as a proper section header immediately after
        # The patterns already ensure proper formatting (newline + keyword + newline/colon)
        # So keywords in regular text content won't match these patterns
        immediate_next_match = re.search(next_section_pattern, text_after_match, re.IGNORECASE)
        immediate_next_inline = re.search(next_inline_pattern, text_after_match, re.IGNORECASE)
        
        # If there's a next section keyword immediately after (within first 50 chars or on same line), skip this match
        if immediate_next_match and immediate_next_match.start() < 50:
            continue
        if immediate_next_inline and immediate_next_inline.start() < 50:
            continue
        
        # Find the next section after our target section (both regular and inline)
        remaining_text = text[section_end_match:]
        next_section_match = re.search(next_section_pattern, remaining_text, re.IGNORECASE)
        next_inline_match = re.search(next_inline_pattern, remaining_text, re.IGNORECASE)
        
        # Reset matches if they start at position 0
        if next_section_match and next_section_match.start() == 0:
            next_section_match = None
        if next_inline_match and next_inline_match.start() == 0:
            next_inline_match = None
        
        # Calculate section end based on the earliest match
        section_end = None
        if next_section_match and next_inline_match:
            section_end = section_end_match + min(next_section_match.start(), next_inline_match.start())
        elif next_section_match:
            section_end = section_end_match + next_section_match.start()
        elif next_inline_match:
            section_end = section_end_match + next_inline_match.start()
        
        # Extract section text, including the detected keyword
        # Start from section_start to include the keyword
        section_text = text[section_start:section_end].strip() if section_end else text[section_start:].strip()
        
        extracted_sections.append(section_text)
    
    # Return the longest extracted section
    if extracted_sections:
        return max(extracted_sections, key=len)
    else:
        return ""
    
def remove_references_section(text):
    """
    Removes the references section from a text document.
    
    This function identifies and removes the references section from the input text
    using the extract_section() function and predefined REFERENCES_TERMS. The function
    preserves all text before and after the references section.
    
    Args:
        text (str): Raw text content potentially containing a references section.
            The text can be in any format and may or may not contain a references section.
            
    Returns:
        str: The input text with the references section removed. If no references
            section is found, returns the original text unchanged.
            
    Example:
        >>> text = "Introduction\\n...\\nReferences\\n1. Smith et al...\\nConclusion"
        >>> result = remove_references_section(text)
        >>> print(result)
        "Introduction\\n...\\nConclusion"
    """
    # Use extract_section to get the references section
    references_section = extract_section(text, REFERENCES_TERMS)
    
    if not references_section:
        return text  # No references section found
    
    # Find where the references section starts in the original text
    ref_start = text.find(references_section)
    
    if ref_start == -1:
        return text  # Shouldn't happen if extract_section found something
      
    # remove only the reference section, keep the text before and after it 
    # print(text[:ref_start]+text[ref_start + len(references_section):])
    return text[:ref_start] + text[ref_start + len(references_section):]


# with open("pdfs/10.3390nu14010148/10.3390nu14010148.txt", "r") as f:
#     text = f.read()
#     text2 = remove_duplicate_pargraphs(text)
#     #save text2 to a file
#     with open("output_para.txt", "w") as f:
#         f.write(text2)

#     # print(extract_section(text,METHODS_TERMS))
    # print(extract_section(text,RESULTS_TERMS))
#     # print(extract_section(text,DISCUSSION_TERMS))
#     # print((extract_section(text,DATA_AVAILABILITY)))
#     # print(extract_section(text,REFERENCES_TERMS))
#     # print(remove_references_section(text))