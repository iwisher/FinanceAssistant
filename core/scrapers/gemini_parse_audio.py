"""
Install the Google AI Python SDK

$ pip install google-generativeai
"""

import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import pydub
from pydub import AudioSegment

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

# ref https://ai.google.dev/gemini-api/docs/safety-settings
def gemini_chat(file_path, history=[], chunk_length_ms=900000): # Added chunk_length_ms
  # Create the model
  generation_config = {
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
  }
  safetty_settings = {
     HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
     HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
     HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
     #HarmCategory.HARM_CATEGORY_UNSPECIFIED: HarmBlockThreshold.BLOCK_NONE,
     HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
  }
  

  model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-002",
    generation_config=generation_config,
    safety_settings=safetty_settings,
    system_instruction="You help generate transcript from input files. Please generate transcript verbitemly and accurately.",
    #system_instruction= "Purpose and Goals:\n\nListen to financial news audio and extract relevant information.\nSummarize key stock market and economics changes, and influencing factors.\nProvide details on company-specific news, such as earnings reports and major announcements.\nEnsure the summary is clear, concise, objective, and easy to understand.\nThe summary should include key metric values and key data, such as specific index values (e.g., Dow Jones closing at 34,000), percentage changes in stock prices or indexes, interest rates, economic growth figures, and unemployment numbers.\nBehaviors and Rules:\n\nAudio Analysis:\na) Carefully listen to the provided financial news audio.\nb) Pay close attention to quantitative data and any mentions of the Nasdaq Composite, S&P 500, and key economic indicators.\n\nInformation Extraction:\na) Identify and summarize the key stock market and ecomoncis changes, including percentage changes and specific index values.\nb) Summarize key economic indicator changes and their potential impact on the market.\nc) Identify any influencing factors, such as government policies or global events, that are mentioned in the audio.\nd) Gather relevant information on company-specific news, including earnings reports, major announcements (mergers, acquisitions, new products), and significant price movements.\ne) Note the reasons for any company-specific changes or price movements.\n\nSummary Generation:\na) Present the extracted information in a clear and concise manner.\nb) Use a neutral tone in your own summary. If analysts or experts in the audio express opinions or predictions, clearly attribute those statements.\nc) Structure the summary logically, starting with an overview of the market, followed by economic indicators, influencing factors, and finally, company-specific news.\nd) Use bullet points or other formatting tools to enhance readability.\ne) Ensure the summary is easy to understand, even for someone with limited financial knowledge.\nf) In addition to summarizing the news, highlight any key insights or analysis offered in the audio, such as expert interpretations of market trends or potential investment implications.\n\nOverall Tone:\n\nBe informative, objective, and accurate in your summary.\nUse professional and clear language.\nFocus on providing a concise and comprehensive overview of the financial news audio.",
  )

  audio = AudioSegment.from_mp3(file_path)
  chunks = []
  for i in range(0, len(audio), chunk_length_ms):
    chunk = audio[i:i + chunk_length_ms]
    chunk_path = f"./download/audiosegment/temp_audio_chunk_{i}.mp3"
    chunk.export(chunk_path, format="mp3")
    chunks.append(chunk_path)

  full_transcript = ""
  for chunk_path in chunks:
    try:
      files = [upload_to_gemini(chunk_path, mime_type="audio/mpeg")]
      chat_session = model.start_chat(history=history)
      response = chat_session.send_message(["Provide a transcript of this audio. If there are multiple speakers, please generate audio diarization for this audio. If you can infer the speaker, please do. If not, use speaker A, speaker B, etc", files[0]])
      full_transcript += response.text.strip() + " "
      os.remove(chunk_path) # Clean up temporary files
    except Exception as e:
      print(f"Error processing chunk {chunk_path}: {e}")
      os.remove(chunk_path) # Clean up temporary files even if error occurred.

  return full_transcript


if __name__ == '__main__':
   transcript = gemini_chat("./download/NaNaShuoMeiGu-20241103-2055.mp3")
   print(transcript)
   with open("./download/NaNaShuoMeiGu-20241103-2055.txt", "w") as f:
      f.write(transcript)
      f.close()