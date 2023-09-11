import re
import numpy as np
from PyPDF2 import PdfReader

try:
    import nltk
    from nltk.corpus import stopwords
except:
    nltk.download('punkt')  # Ensure that the punkt tokenizer is downloaded
    nltk.download('stopwords')  # Ensure that stop words are downloaded

def order_by(records, order):
    """
    Order a list of records based on a specified order list.

    Args:
        records (list): A list of records to be ordered.
        order (list): A list of integers representing the desired order of records.

    Returns:
        list: A new list of records ordered according to the order list.
    """
    print(records,order)
    record_dict = {record[0]: record for record in records}
    ordered_records = [record_dict[i] for i in order]
    return ordered_records

def extract_text(path: str) -> str:
    """
    Extract and clean text from a given file path (PDF or TXT).

    Args:
        path (str): The file path from which text should be extracted.

    Returns:
        str: A cleaned text string.
        
    Raises:
        ValueError: If the file format is unsupported.
    """
    file_extension = path.split('.')[-1].lower()
    if file_extension == 'pdf':
        text = extract_text_from_pdf(path)
    elif file_extension == 'txt':
        text = extract_text_from_txt(path)
    else:
        raise ValueError("Unsupported file format")
    
    cleaned_text = re.sub(r'[^\w\s]', ' ', text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
    cleaned_text = cleaned_text.lower()
    return cleaned_text

def extract_text_from_pdf(path: str) -> str:
    """
    Extract text from a PDF file.

    Args:
        path (str): The file path of the PDF.

    Returns:
        str: The extracted text from the PDF.
    """
    text = ""
    pdf_reader = PdfReader(path)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_txt(path: str) -> str:
    """
    Extract text from a TXT file.

    Args:
        path (str): The file path of the TXT file.

    Returns:
        str: The extracted text from the TXT file.
    """
    with open(path, "r", encoding="utf-8") as txt_file:
        text = txt_file.read()
    return text

def split_text(text, chunk_size=256):
    """
    Split text into chunks of a specific word count.

    Args:
        text (str): The input text to split.
        chunk_size (int): The desired word count for each chunk (default is 256).

    Returns:
        List[str]: A list of text chunks.
    """
    pattern = r'[^a-zA-Z0-9\s]'
    text_cleaned = re.sub(pattern, '', text)
    tokens = nltk.word_tokenize(text_cleaned)
    filtered_tokens = [word for word in tokens if word.lower() not in stopwords.words('english')]
    chunks = []
    current_chunk = []
    max_tokens_per_chunk = chunk_size
    for token in filtered_tokens:
        if len(current_chunk) + len(nltk.word_tokenize(token)) <= max_tokens_per_chunk:
            current_chunk.append(token)
        else:
            chunks.append(current_chunk)
            current_chunk = [token]
    if current_chunk:
        chunks.append(current_chunk)
    chunked_text = [' '.join(chunk) for chunk in chunks]
    return chunked_text

def remove_neg_indexes(D: np.ndarray, I: np.ndarray):
    """
    Remove negative indexes from the results.

    Args:
        D (np.ndarray): The distances.
        I (np.ndarray): The indices.

    Returns:
        (np.ndarray, np.ndarray): The distances and indices with negative indexes removed.
    """
    D = D[I >= 0]
    I = I[I >= 0]
    return list(D), list(I)
