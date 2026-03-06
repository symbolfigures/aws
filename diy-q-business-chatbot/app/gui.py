from inference import infer
import streamlit as st
import json
from PIL import Image
import sys
from utils import font_css, log_interaction
import uuid

st.set_page_config(
    page_title="Chatbot",
    page_icon=Image.open('static/owl1_16xx.png')
)

st.markdown(font_css(), unsafe_allow_html=True)

with open('static/style.css') as f:
	st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# beta
col1A, col1B, col1C = st.columns([1, 2, 1])
col1C.markdown('''<p style="font-family: monospace; text-align:right"></p>''', unsafe_allow_html=True)
# title
st.write('''
# RAG Chatbot
Check sources for accuracy.
''')

# init chat history
if 'chat_history' not in st.session_state:
	st.session_state.chat_history = []
# display chat history
for message in st.session_state.chat_history:
	if message['role'] == 'owl1':
		avatar = 'static/owl1_64xx.png'
	if message['role'] == 'owl2':
		avatar = 'static/owl2_64xx.png'
	with st.chat_message(message['role'], avatar=avatar):
		st.markdown(message['text'], unsafe_allow_html=True)


def main():
	question = None
	question = st.chat_input('Ask a question')
	if question:
		msg_id = str(uuid.uuid4())
		with st.chat_message('owl2', avatar='static/owl2_64xx.png'):
			st.markdown(question)
		st.session_state.chat_history.append({'role': 'owl2', 'text': question})
		with st.spinner('Researching...') as status:
			answer = infer(question)
		if answer:
			st.session_state.chat_history.append({'role': 'owl1', 'text': answer})
			log_interaction(msg_id, question, answer, 'none')

			with st.chat_message('owl1', avatar='static/owl1_64xx.png'):
				st.markdown(answer, unsafe_allow_html=True)

			col0, col1, col2 = st.columns([18, 1, 1])
			col1.button(
				':material/thumb_up:',
				on_click=log_feedback, 
				args=(msg_id, question, answer, 'positive'),
				type='tertiary'
			)
			col2.button(
				':material/thumb_down:',
				on_click=log_feedback, 
				args=(msg_id, question, answer, 'negative'), 
				type='tertiary'
			)


def log_feedback(msg_id, question, answer, feedback):
	log_interaction(msg_id, question, answer, feedback)
	st.toast('Feedback recorded.')


if __name__ == '__main__':
	main()

















