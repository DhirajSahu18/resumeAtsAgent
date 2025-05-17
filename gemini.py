# gemini.py
import google.generativeai as genai
genai.configure(api_key="AIzaSyAfqrnU1acHl18MdyJ7vaJRLDC8sh5fLp0")

model = genai.GenerativeModel("gemini-2.0-flash")
