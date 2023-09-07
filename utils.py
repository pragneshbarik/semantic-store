import re
from PyPDF2 import PdfReader
import nltk
import numpy as np

nltk.download('punkt')  # Ensure that the punkt tokenizer is downloaded
nltk.download('stopwords')  # Ensure that stop words are downloaded

def order_by(records, order):
        print(len(records), len(order))
        # if not all(0 <= i < len(records) for i in order) or len(set(order)) != len(order):
        #     raise ValueError("Invalid order list")

        record_dict = {record[0]: record for record in records}

        ordered_records = [record_dict[i] for i in order]

        return ordered_records

def extract_text(path: str) -> str :
        text=""
        pdf_reader = PdfReader(path)

        for page in pdf_reader.pages :
            text+= page.extract_text()

        cleaned_text = re.sub(r'[^\w\s]', ' ', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)

        cleaned_text = cleaned_text.lower()
        return cleaned_text


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

    D = D[0][I >= 0]
    I = I[0][I >= 0]

    return list(D), list(I) 


