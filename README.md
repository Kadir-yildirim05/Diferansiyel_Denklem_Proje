# Difsolv

Difsolv, diferansiyel denklemleri adım adım çözen, LaTeX biçiminde gösteren ve ses/PDF çıktıları üreten modern bir web arayüzüdür.

Özellikler
- 3 sütunlu modern arayüz
- Sol panelde denklem türleri menüsü
- Orta panelde tür bulma ve adım adım çözüm
- Sağ panelde geçmiş, ses ve PDF çıktıları
- Mevcut Python çözücü ve medya dosyaları korunarak wrapper üzerinden entegrasyon

Kurulum
1. Sanal ortam oluşturun:
   python -m venv .venv
   source .venv/bin/activate
2. Bağımlılıkları yükleyin:
   pip install -r requirements.txt
3. Uygulamayı çalıştırın:
   streamlit run app.py
4. Tarayıcıda açın:
   http://localhost:8501

Yapı
- app.py: ana Streamlit arayüzü
- difsolv_engine.py: legacy solver ve medya katmanı için wrapper
- requirements.txt: Python bağımlılıkları

Notlar
- Mevcut repo içinde yer alan `tür_ile_çözüm_birleştirme_bütünü_30.py`, `seslendirme.py` ve `pdf_oluşturma_kütüphanesi_tablo.py` dosyaları çalıştırılabilir şekilde korunur.
- Bu web uygulaması, legacy modüllere doğrudan müdahale etmeden güvenli arayüz katmanı sağlar; gerektiğinde `difsolv_engine.py` içindeki fonksiyonlar gerçek solver fonksiyonlarına bağlanacak şekilde güncellenebilir.
- Ses üretimi için gTTS kullanılır. PDF üretimi için reportlab kullanılır.

Geliştirme/ipucu
- Gelişmiş üretim için aşağıdaki adımları uygulayabilirsiniz:
  - Legacy modül adlarını kendi repo yapınıza göre adapte edin.
  - `difsolv_engine.py` içinde `detect_equation_type` ve `solve_equation` fonksiyonlarını gerçek matematik motoruyla değiştirin.
  - `st.session_state` içindeki geçmiş ve kullanıcı oturum mantığını SQLite veya veritabanı katmanına taşıyın.

