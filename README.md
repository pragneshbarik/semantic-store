# SemanticStore
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Twitter header - 1 (2)](https://github.com/pragneshbarik/semantic-store/assets/65221256/3c47be22-28e0-4ece-80de-e8a7bfa111bf)



A simple easy to use vector store for small hobby projects.

A  versatile vector store designed for multimodal search. This store seamlessly integrates with Faiss to provide efficient similarity search capabilities. Whether you're working with image, text, or audio data, Semantic has you covered.

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

3. **Get started in python**

   ```python
     import Store from SemanticStore
   
     s = Store()
     s.connect('some2.db')
     s.insert('gita.txt')
     s.commit()
     res = s.search("what is meaning of life according to gita ?", 5, modals=['text', 'image'])
     
     print(res)

## Models
SemanticStore uses various state-of-the-art models to process text, images and audio.

| **Pipelines** |        **Model 1**        |        **Model 2**        |         **Model 3**         |         **Model 4**         |
|:-------------:|:-------------------------:|:-------------------------:|:---------------------------:|:---------------------------:|
| Text          | multi-qa-MiniLM-L6-cos-v1 |           _CLIP_          |              -              |              -              |
| Audio         |          Whisper          | multi-qa-MiniLM-L6-cos-v1 |            _CLIP_           |              -              |
| Image         |            CLIP           |           _BLIP_          | _multi-qa-MiniLM-L6-cos-v1_ |              -              |
| _Video_       |         _Whisper_         |           _CLIP_          |            _BLIP_           | _multi-qa-MiniLM-L6-cos-v1_ |

**Note** : Models and pipeines in _Italics_ are still to be implemented.

## Contributing
Contributions are welcome! If you'd like to enhance the SemanticStore or fix issues, please follow these steps:

1. Fork the repository.
2. Create a branch: git checkout -b feature/your-feature or fix/your-fix.
3. Commit your changes: git commit -m 'Add some feature' or git commit -m 'Fix some issue'.
4. Push to the branch: git push origin feature/your-feature or git push origin fix/your-fix.
5. Open a pull request


> **Note**: This vector store is intended for small hobby projects and personal use. It may not be suitable for large-scale or production environments.


