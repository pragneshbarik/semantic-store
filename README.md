# SemanticStore
![Twitter header - 1 (1)](https://github.com/pragneshbarik/semantic-store/assets/65221256/7b09abd2-aed7-409d-b52c-ced6dc74ca58)


A simple easy to use vector store for small hobby projects.

A  versatile vector store designed for multimodal search. This store seamlessly integrates with Faiss to provide efficient similarity search capabilities. Whether you're working with image, text, or audio data, this vector store has you covered.

## Features

- **Multimodal Support**: Handle a wide range of data types, including image, text, and audio vectors.
- **Faiss Integration**: Utilize the speed and efficiency of Faiss for similarity search.
- **Custom Pipelines**: Create customizable pipelines for processing and indexing your data.
- **Ease of Use**: Designed for simplicity, making it accessible to developers of all levels.

## Getting Started

Follow these steps to get started with the Multimodal Vector Store:

1. **Clone the Repository**

   ```shell
   git clone https://github.com/pragneshbarik/semantic-store.git

2. **Install requirements.txt**
   ```shell
   pip install -r requirements.txt

2. **Get started in python**

   ```python
     import Store from SemanticStore
   
     s = Store()
     s.connect('some2.db')
     s.insert('gita.txt')
     s.commit()
     res = s.search("what is meaning of life according to gita ?", 5, modals=['text', 'image'])
     
     print(res)


