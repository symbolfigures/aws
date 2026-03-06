#!/bin/bash
set -e

echo "downloading vectorstore..."
python load_vectorstore.py

echo "starting streamlit..."
exec streamlit run gui.py
