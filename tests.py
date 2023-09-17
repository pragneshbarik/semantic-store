from pipelines.TextPipeline import TextPipeline
from pipelines.ImagePipeline import ImagePipeline
from pipelines.AudioPipeline import AudioPipeline
from faster_whisper import WhisperModel
import torch

model_size = "tiny.en"


model = WhisperModel(model_size, device="cpu", compute_type="int8")

def transcribe() :
    segments, info = model.transcribe("videoplayback.mp3", beam_size=5)
    text_segments = []

    for segment in segments:
        segment.start
        segment.end
        text_segments.append(segment.text)
    
    extracted_text = " ".join(text_segments)
    return extracted_text





audio_pipe = AudioPipeline('audio.faiss', 'db.db')
def test_audio_pipeline_insert() :
    uuid = audio_pipe.insert_file('videoplayback.mp3')
    print(uuid)

def test_audio_pipeline_search() :
    res = audio_pipe.similarity_search(query="spiderman", k = 5)
    print(res)

    


test_audio_pipeline_insert()
test_audio_pipeline_search()

    