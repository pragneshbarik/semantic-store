from SemanticStore import Store

s = Store()

def LLM(prompt) :
    # your LLM logic here
    return "response"

s.connect('semantic1')
# s.insert('gita.txt')
# s.insert('https://images.unsplash.com/photo-1532005614677-fa2783e8707a?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1887&q=80')
# s.insert('videoplayback.mp3')
res = s.search(query="some life", k=3, modals=['text', 'audio', 'image'])

print(res)

question = input("Ask a question")
while True :
    context = ' '.join(s.search(query={question}, k=5).texts.chunks()) # handles retrival of most relevant chunks from inserted text files

    prompt = f"""
    GIVEN THIS CONTEXT : {context}

    ANSWER THE FOLLOWING QUERY : {question}

    """
    response = LLM(prompt)

    print(response)

    question = input()
