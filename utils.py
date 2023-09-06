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