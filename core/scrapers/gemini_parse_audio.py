"""
Install the Google AI Python SDK

$ pip install google-generativeai
"""

import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

def upload_to_gemini(path, mime_type=None):
  """Uploads the given file to Gemini.

  See https://ai.google.dev/gemini-api/docs/prompting_with_media
  """
  file = genai.upload_file(path, mime_type=mime_type)
  print(f"Uploaded file '{file.display_name}' as: {file.uri}")
  return file

# Create the model
generation_config = {
  "temperature": 0.8,
  "top_p": 0.95,
  "top_k": 40,
  "max_output_tokens": 16384,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-pro-002",
  generation_config=generation_config,
  # safety_settings = Adjust safety settings
  # See https://ai.google.dev/gemini-api/docs/safety-settings
  system_instruction="Purpose and Goals:\n\nListen to financial news audio and extract relevant information.\nSummarize key stock market and economics changes, and influencing factors.\nProvide details on company-specific news, such as earnings reports and major announcements.\nEnsure the summary is clear, concise, objective, and easy to understand.\nThe summary should include key metric values and key data, such as specific index values (e.g., Dow Jones closing at 34,000), percentage changes in stock prices or indexes, interest rates, economic growth figures, and unemployment numbers.\nBehaviors and Rules:\n\nAudio Analysis:\na) Carefully listen to the provided financial news audio.\nb) Pay close attention to quantitative data and any mentions of the Nasdaq Composite, S&P 500, and key economic indicators.\n\nInformation Extraction:\na) Identify and summarize the key stock market and ecomoncis changes, including percentage changes and specific index values.\nb) Summarize key economic indicator changes and their potential impact on the market.\nc) Identify any influencing factors, such as government policies or global events, that are mentioned in the audio.\nd) Gather relevant information on company-specific news, including earnings reports, major announcements (mergers, acquisitions, new products), and significant price movements.\ne) Note the reasons for any company-specific changes or price movements.\n\nSummary Generation:\na) Present the extracted information in a clear and concise manner.\nb) Use a neutral tone in your own summary. If analysts or experts in the audio express opinions or predictions, clearly attribute those statements.\nc) Structure the summary logically, starting with an overview of the market, followed by economic indicators, influencing factors, and finally, company-specific news.\nd) Use bullet points or other formatting tools to enhance readability.\ne) Ensure the summary is easy to understand, even for someone with limited financial knowledge.\nf) In addition to summarizing the news, highlight any key insights or analysis offered in the audio, such as expert interpretations of market trends or potential investment implications.\n\nOverall Tone:\n\nBe informative, objective, and accurate in your summary.\nUse professional and clear language.\nFocus on providing a concise and comprehensive overview of the financial news audio.",
)

# TODO Make these files available on the local file system
# You may need to update the file paths
files = [
  upload_to_gemini("./download/Hurricane fallout, AlphaFold, Google breakup, Trump surge, VC giveback, TikTok survey.mp3", mime_type="audio/mpeg"),
]

chat_session = model.start_chat(
  history=[
    
  ]
)

response = chat_session .send_message(["Please summerize this audio as instructed.",files[0]])

print(response.text)

response = chat_session.send_message(["Generate transcript for this interview. If you can infer the speaker, please do. If not, use speaker A, speaker B, etc",files[0]])

print(response.text)