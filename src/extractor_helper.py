import re
from sections import *

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
                 if p.strip() == '' or text.split('\n').index(p) == i]

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
        The extracted section text, including the section header. Returns an empty string
        if the section is not found. For inline sections, returns only the header line.
        If multiple sections are found, returns the longest one.
        
    Notes:
    -----
    - The function first removes duplicate paragraphs from the input text
    - Section matching is case-insensitive
    - Section headers must be preceded by an empty line (except for inline sections)
    - Section ends when another known section header is encountered
    - When multiple sections match, the longest one is returned
    """
    
    text = remove_duplicate_pargraphs(text)
    # Create a list of all possible section terms from the sections module
    all_section_terms = (METHODS_TERMS + RESULTS_TERMS + DISCUSSION_TERMS + 
                        REFERENCES_TERMS + FUNDING + INTRODUCTION + CAS + 
                        ACNOWLEDGEMENTS + AUTH_CONT + ABBREVIATIONS + CONCLUSION + ABSTRACT +
                        LIMITATIONS + COI + SUPP_DATA + DATA_AVAILABILITY + ETHICS)
    
    # Create regex patterns for different formatting styles of the target section
    # Handle regular format, spaced letters, numbered sections, and sections with colons
    section_patterns = [
        # Regular format: "Methods"
        r'\n\s*\n\s*(' + '|'.join(map(re.escape, section_terms)) + r')\s*[\n:]',
        
        # Spaced letters: "M E T H O D S"
        r'\n\s*\n\s*(' + '|'.join(' '.join(term) for term in [[c for c in term] for term in section_terms]) + r')\s*[\n:]',
        
        # Numbered sections: "1. Methods", "I. Methods", etc.
        r'\n\s*\n\s*(?:\d+\.|\[?\d+\]?\.?|[IVXivx]+\.)\s*(' + '|'.join(map(re.escape, section_terms)) + r')\s*[\n:]',
        
        # Numbered sections with pipe: "1 | INTRODUCTION"
        r'\n\s*\n\s*(?:\d+\s*\|\s*)(' + '|'.join(map(re.escape, section_terms)) + r')\s*[\n:]'
    ]
    
    # Find all occurrences of the target section using any of the patterns
    section_matches = []
    
    for pattern in section_patterns:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for match in matches:
            section_matches.append((match.start(), pattern))
    
    # If no matches found with standard patterns, try inline pattern
    if not section_matches:
        inline_pattern = r'\n\s*(' + '|'.join(map(re.escape, section_terms)) + r')[\s:]([^\n]+)'
        match = re.search(inline_pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
        return ""
    
    # Sort matches by position in text
    section_matches.sort(key=lambda x: x[0])
    
    # Create patterns for different formatting styles of the next section
    next_section_patterns = []
    for term in [term for term in all_section_terms if term not in section_terms]:
        # Regular format
        next_section_patterns.append(re.escape(term))
        # Spaced letters
        next_section_patterns.append(' '.join([c for c in term]))
    
    # Create pattern for any next section except the current one
    next_section_pattern = r'\n\s*\n\s*(?:\d+\.|\[?\d+\]?\.?|[IVXivx]+\.|\d+\s*\|\s*)?\s*(' + '|'.join(next_section_patterns) + r')\s*[\n:]'
    
    # Extract all sections and find the longest one
    extracted_sections = []
    
    for section_start, pattern in section_matches:
        # Find the next section after our target section
        next_section_match = re.search(next_section_pattern, text[section_start + 1:], re.IGNORECASE)
        
        if next_section_match:
            # If another section is found, extract everything up to that section
            section_end = section_start + 1 + next_section_match.start()
            extracted_sections.append(text[section_start:section_end].strip())
        else:
            # If no next section is found, extract everything until the end
            extracted_sections.append(text[section_start:].strip())
    
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
    return text[:ref_start] + text[ref_start + len(references_section):]
