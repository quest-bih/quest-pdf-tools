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
        
    Notes:
    -----
    - The function first removes duplicate paragraphs from the input text
    - Section matching is case-insensitive
    - Section headers must be preceded by an empty line (except for inline sections)
    - Section ends when another known section header is encountered
    """
    
    text = remove_duplicate_pargraphs(text)
    # Create a list of all possible section terms from the sections module
    all_section_terms = (METHODS_TERMS + RESULTS_TERMS + DISCUSSION_TERMS + 
                        REFERENCES_TERMS + FUNDING + INTRODUCTION + CAS + 
                        ACNOWLEDGEMENTS + AUTH_CONT + ABBREVIATIONS + 
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
    
    # Find the target section using any of the patterns
    section_start = None
    for pattern in section_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            section_start = match.start()
            break
    
    if section_start is None:
        # Try the inline pattern when standard patterns don't match
        inline_pattern = r'\n\s*(' + '|'.join(map(re.escape, section_terms)) + r')[\s:]([^\n]+)'
        match = re.search(inline_pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
        return ""
    
    # Create patterns for different formatting styles of the next section
    next_section_patterns = []
    for term in [term for term in all_section_terms if term not in section_terms]:
        # Regular format
        next_section_patterns.append(re.escape(term))
        # Spaced letters
        next_section_patterns.append(' '.join([c for c in term]))
    
    # Create pattern for any next section except the current one
    next_section_pattern = r'\n\s*\n\s*(?:\d+\.|\[?\d+\]?\.?|[IVXivx]+\.|\d+\s*\|\s*)?\s*(' + '|'.join(next_section_patterns) + r')\s*[\n:]'
    
    # Find the next section after our target section
    next_section_match = re.search(next_section_pattern, text[section_start + 1:], re.IGNORECASE)
    
    if next_section_match:
        # If another section is found, extract everything up to that section
        section_end = section_start + 1 + next_section_match.start()
        return text[section_start:section_end].strip()
    else:
        # If no next section is found, extract everything until the end
        return text[section_start:].strip()
    
def remove_references_section(text):
    """
    Removes the references section from the text if found.
    
    This function uses extract_section() to identify and remove the references
    section from the provided text. The references section is identified using
    predefined REFERENCES_TERMS. If no references section is found, the original
    text is returned unchanged.
    
    Parameters:
    ----------
    text : str
        The input text from which to remove the references section.
        Should be raw text content that may contain a references section.
        
    Returns:
    -------
    str
        The text with the references section removed if found, otherwise
        returns the original text unchanged. The returned text is stripped
        of trailing whitespace.
        
    Notes:
    -----
    - Uses extract_section() to locate the references section
    - Case-insensitive matching is used for identifying references section
    - Returns original text if no references section is found
    """
    # Use extract_section to get the references section
    references_section = extract_section(text, REFERENCES_TERMS)
    
    if not references_section:
        return text  # No references section found
    
    # Find where the references section starts in the original text
    ref_start = text.find(references_section)
    
    if ref_start == -1:
        return text  # Shouldn't happen if extract_section found something
        
    # Remove the references section
    return text[:ref_start].strip()

    
