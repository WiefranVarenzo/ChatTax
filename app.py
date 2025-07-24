import streamlit as st
import requests

# =============================================
# Konfigurasi Halaman
# =============================================
st.set_page_config(page_title="💬 Chatbot Pajak", page_icon="💬", layout="centered")

st.markdown("""
# 💬 Chatbot Pajak
Tanyakan apa pun tentang perpajakan Indonesia berdasarkan dokumen yang telah diolah.
""")

st.divider()

# =============================================
# Input URL API Colab
# =============================================
with st.sidebar:
    st.subheader("🔗 Konfigurasi API")
    API_URL = st.text_input(
        "Masukkan API URL dari Colab (Ngrok):",
        value="https://976eda16e6b1.ngrok-free.app/ask", 
        help="Salin URL dari output Colab yang berformat https://xxxx.ngrok-free.app/ask"
    )
    st.caption("⚠️ Ganti setiap runtime Colab")

# =============================================
# Simpan history percakapan di session_state
# =============================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================================
# Tampilkan history chat seperti UI GPT
# =============================================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# =============================================
# Input pertanyaan user
# =============================================
prompt = st.chat_input("Tulis pertanyaan pajakmu di sini...")

if prompt:
    if not prompt.strip():
        st.warning("⚠️ Pertanyaan tidak boleh kosong!")
    elif "ngrok-free.app" not in API_URL:
        st.warning("⚠️ Harap masukkan URL ngrok yang valid!")
    else:
        # Tampilkan pertanyaan user di chat
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("🔍 Sedang mencari jawaban..."):
            try:
                res = requests.post(API_URL, json={"question": prompt})
                if res.status_code == 200:
                    answer = res.json().get("answer", "Maaf, saya tidak menemukan jawaban.")
                    # Tampilkan jawaban bot di chat
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    with st.chat_message("assistant"):
                        st.markdown(answer)
                else:
                    st.error(f"❌ Gagal memanggil API. Status code: {res.status_code}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
