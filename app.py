import streamlit as st
import requests
import uuid
from streamlit.components.v1 import html

# =============================================
# Konfigurasi Halaman & Inisialisasi State
# =============================================
st.set_page_config(page_title="Chatbot Pajak Pro", page_icon="🤖", layout="wide")

maze_snippet = """
<script>
(function (m, a, z, e) {
  var s, t;
  try { t = m.sessionStorage.getItem('maze-us'); } catch (err) {}
  if (!t) { t = new Date().getTime(); try { m.sessionStorage.setItem('maze-us', t); } catch (err) {} }
  s = a.createElement('script');
  s.src = z + '?apiKey=' + e;
  s.async = true;
  a.getElementsByTagName('head')[0].appendChild(s);
  m.mazeUniversalSnippetApiKey = e;
})(window, document, 'https://snippet.maze.co/maze-universal-loader.js', 'd58d794c-587e-4b4e-b2c6-9a7b77399290');
</script>
"""

# Masukkan snippet ke halaman
html(maze_snippet, height=0, width=0)

# Inisialisasi semua state yang dibutuhkan untuk sesi pengguna
def init_session_state():
    """Inisialisasi session state jika belum ada."""
    if "token" not in st.session_state:
        st.session_state.token = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversations" not in st.session_state:
        st.session_state.conversations = []
    if "current_conversation_id" not in st.session_state:
        st.session_state.current_conversation_id = None
    if "active_api_url" not in st.session_state:
        st.session_state.active_api_url = None

init_session_state()

# =============================================
# Fungsi untuk Berinteraksi dengan API Backend
# =============================================
def api_request(method, endpoint, json_data=None):
    """Fungsi terpusat untuk semua permintaan ke API backend."""
    if not st.session_state.active_api_url:
        st.toast("URL Backend belum diatur!", icon="❌")
        return None
        
    headers = {}
    if st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
        
    try:
        url = f"{st.session_state.active_api_url.rstrip('/')}/{endpoint}"
        res = requests.request(method, url, headers=headers, json=json_data, timeout=90) # Timeout lebih lama untuk model AI
        res.raise_for_status()
        return res.json()
    except requests.exceptions.HTTPError as e:
        # Menampilkan pesan error yang lebih informatif dari backend
        detail = "Terjadi kesalahan pada server."
        try:
            detail = e.response.json().get('detail', detail)
        except requests.exceptions.JSONDecodeError:
            pass
        st.error(f"Error API: {detail}")
    except requests.exceptions.RequestException as e:
        st.error(f"Koneksi ke backend gagal: {e}")
    return None

def refresh_conversations():
    """Memuat ulang daftar percakapan dari backend untuk pengguna yang login."""
    if st.session_state.token:
        st.session_state.conversations = api_request("get", "conversations") or []

# =============================================
# Tampilan Sidebar (Menu Utama)
# =============================================
with st.sidebar:
    st.title("Menu Chatbot")
    
    # Form untuk memasukkan URL backend
    with st.form(key="api_form"):
        api_url_input = st.text_input("URL Backend Ngrok", value=st.session_state.get("active_api_url", ""))
        if st.form_submit_button("Set URL"):
            st.session_state.active_api_url = api_url_input.strip()
            st.rerun()

    if st.session_state.active_api_url:
        st.success(f"API Terhubung")
    else:
        st.warning("Silakan masukkan URL backend untuk memulai.")
    st.divider()

    # --- TAMPILAN SETELAH LOGIN ---
    if st.session_state.token:
        st.subheader("Riwayat Percakapan")
        
        if st.button("➕ Percakapan Baru", use_container_width=True):
            st.session_state.current_conversation_id = None
            st.session_state.messages = []
            st.rerun()

        # Muat dan tampilkan daftar percakapan
        if not st.session_state.conversations:
            refresh_conversations()

        for convo in st.session_state.conversations:
            convo_id = convo['id']
            # Gunakan kolom agar tombol hapus sejajar
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                # Tombol untuk memilih percakapan
                if st.button(convo['title'], key=f"convo_{convo_id}", use_container_width=True):
                    st.session_state.current_conversation_id = convo_id
                    st.session_state.messages = api_request("get", f"conversations/{convo_id}") or []
                    st.rerun()
            with col2:
                # Tombol untuk menghapus percakapan
                if st.button("🗑️", key=f"del_{convo_id}", help="Hapus percakapan", use_container_width=True):
                    api_request("delete", f"conversations/{convo_id}")
                    st.session_state.current_conversation_id = None
                    st.session_state.messages = []
                    refresh_conversations() # Refresh list setelah hapus
                    st.rerun()

        st.divider()
        if st.button("Logout", use_container_width=True, type="primary"):
            # Hapus semua state kecuali URL API
            for key in list(st.session_state.keys()):
                if key != 'active_api_url':
                    del st.session_state[key]
            st.rerun()
            
    # --- TAMPILAN SEBELUM LOGIN ---
    else:
        st.info("Login untuk menyimpan riwayat percakapan Anda.")
        tab_login, tab_register = st.tabs(["Login", "Register"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                if st.form_submit_button("Login", use_container_width=True, disabled=not st.session_state.active_api_url):
                    res = api_request("post", "login", {"email": email, "password": password})
                    if res and "access_token" in res:
                        st.session_state.token = res.get("access_token")
                        st.rerun()

        with tab_register:
            with st.form("register_form"):
                email_reg = st.text_input("Email Registrasi")
                password_reg = st.text_input("Password Registrasi", type="password")
                if st.form_submit_button("Register", use_container_width=True, disabled=not st.session_state.active_api_url):
                    res = api_request("post", "register", {"email": email_reg, "password": password_reg})
                    if res:
                        st.success("Registrasi berhasil! Silakan login.")

# =============================================
# Tampilan Utama (Area Chat)
# =============================================
st.title("🤖 Chatbot Pajak Profesional")
st.caption("Didukung oleh Mistral 7B dan RAG")

# Tampilkan pesan yang ada di state
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Tampilkan tombol feedback hanya untuk pesan dari asisten dan jika pengguna login
        if msg["role"] == "assistant" and st.session_state.token:
            col1, col2, _ = st.columns([1, 1, 10])
            if col1.button("👍", key=f"up_{msg['id']}", help="Suka jawaban ini"):
                api_request("post", "feedback", {"message_id": msg['id'], "rating": 1})
                st.toast("Terima kasih atas feedback Anda!", icon="✅")
            if col2.button("👎", key=f"down_{msg['id']}", help="Tidak suka jawaban ini"):
                api_request("post", "feedback", {"message_id": msg['id'], "rating": -1})
                st.toast("Terima kasih atas feedback Anda!", icon="✅")

# Input chat dari pengguna
if prompt := st.chat_input("Tulis pertanyaan Anda...", disabled=not st.session_state.active_api_url):
    
    # Tambahkan pesan pengguna ke UI secara lokal terlebih dahulu
    # Beri ID sementara agar tombol feedback tidak error
    temp_user_id = f"user_{uuid.uuid4()}"
    st.session_state.messages.append({"role": "user", "content": prompt, "id": temp_user_id})
    st.rerun()

# Logika untuk memproses pesan terakhir dari pengguna
# Cek jika pesan terakhir adalah dari 'user' dan belum diproses
last_message = st.session_state.messages[-1] if st.session_state.messages else None
if last_message and last_message["role"] == "user" and last_message["id"].startswith("user_"):
    
    # Hapus ID sementara dari pesan pengguna
    last_message.pop("id", None)
    
    with st.chat_message("assistant"):
        with st.spinner("🤖 AI sedang berpikir..."):
            payload = {
                "question": last_message["content"],
                "conversation_id": st.session_state.current_conversation_id
            }
            
            response = api_request("post", "ask", payload) 
            
            if response:
                # Jika pengguna login, muat ulang seluruh percakapan dari DB
                if st.session_state.token:
                    st.session_state.current_conversation_id = response["conversation_id"]
                    st.session_state.messages = api_request("get", f"conversations/{response['conversation_id']}") or []
                    refresh_conversations() # Refresh daftar convo jika ini percakapan baru
                else: 
                    # Jika pengguna adalah tamu, tambahkan jawaban AI secara lokal
                    temp_assistant_id = f"assistant_{uuid.uuid4()}"
                    st.session_state.messages.append({"role": "assistant", "content": response["answer"], "id": temp_assistant_id})
                
                # Tampilkan ulang halaman untuk memperbarui chat
                st.rerun()
