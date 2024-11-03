import speech_recognition as sr

# Функция для преобразования аудио в текст
def audio_to_text(dest_name: str):
    r = sr.Recognizer()
    with sr.AudioFile(dest_name) as source:
        audio = r.record(source)
    result = r.recognize_google(audio, language="ru-RU")
    return result