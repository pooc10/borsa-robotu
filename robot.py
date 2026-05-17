import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- GELİŞMİŞ ANALİZ FONKSİYONLARI ---
def analiz_motoru(df):
    # RSI Hesaplama
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    
    # Sıfıra bölme hatasını engellemek için küçük bir değer ekle
    rs = gain / loss.replace(0, 0.00001)
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Hareketli Ortalamalar
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # Destek/Direnç (Son 30 Gün)
    df['Destek'] = df['Low'].rolling(window=30).min()
    df['Direnc'] = df['High'].rolling(window=30).max()
    
    # Volatilite (Oynaklık)
    df['Volatilite'] = df['Close'].pct_change().rolling(window=20).std() * 100
    return df

def haber_algisi_hesapla(haberler):
    pozitif_kelimeler = ['rekor', 'artış', 'büyüme', 'kazanç', 'pozitif', 'alım', 'yukarı', 'kâr', 'anlaşma', 'ihale', 'temettü', 'hedef', 'proje', 'beklenti', 'güçlü']
    negatif_kelimeler = ['düşüş', 'kayıp', 'negatif', 'satış', 'aşağı', 'zarar', 'risk', 'kriz', 'dava', 'iptal', 'borç', 'enflasyon', 'zayıf', 'gerileme']
    
    skor = 0
    detaylar = []
    if not haberler:
        return "Nötr 🟡", []
        
    for n in haberler:
        title = n.get('title') or n.get('content', {}).get('title', '')
        if not title: continue
        
        baslik_lower = title.lower()
        durum = "Nötr 😐"
        
        for p in pozitif_kelimeler:
            if p in baslik_lower:
                skor += 1
                durum = "Pozitif 🟢"
                break
        
        for neg in negatif_kelimeler:
            if neg in baslik_lower:
                skor -= 1
                durum = "Negatif 🔴"
                break
                
        detaylar.append({"baslik": title, "algı": durum})
    
    algı_sonucu = "Pozitif 🟢" if skor > 0 else "Negatif 🔴" if skor < 0 else "Nötr 🟡"
    return algı_sonucu, detaylar

# --- ARAYÜZ ---
st.set_page_config(page_title="Master BIST Analist", layout="wide")
st.title("🤖 Master BIST Analiz Sistemi")

ticker = st.text_input("Hisse Sembolü (Örn: THYAO, EREGL)", "THYAO").upper()
if not ticker.endswith(".IS"): ticker += ".IS"

if st.button("TAM KAPSAMLI ANALİZİ BAŞLAT"):
    with st.spinner('Piyasa derinliği taranıyor...'):
        hisse = yf.Ticker(ticker)
        df = hisse.history(period="6mo")
        
        if df.empty:
            st.error("Veri alınamadı! Lütfen sembolü kontrol edin.")
        else:
            df = analiz_motoru(df)
            fiyat = df['Close'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            destek = df['Destek'].iloc[-1]
            direnc = df['Direnc'].iloc[-1]
            ema20 = df['EMA20'].iloc[-1]
            oynaklik = df['Volatilite'].iloc[-1]
            
            # Değişim yüzdesi
            onceki_kapanis = df['Close'].iloc[-2]
            degisim = ((fiyat - onceki_kapanis) / onceki_kapanis) * 100

            # --- 1. RADAR PANELİ ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Anlık Fiyat", f"{fiyat:.2f} TL", f"{degisim:.2f}%")
            c2.metric("Oynaklık (Risk)", f"%{oynaklik:.2f}")
            c3.metric("RSI (Güç)", f"{rsi:.2f}")
            
            algı, haber_detay = haber_algisi_hesapla(hisse.news)
            c4.metric("Haber Algısı", algı)

            # --- 2. GRAFİK ---
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Fiyat'))
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='Trend (EMA20)', line=dict(color='orange')))
            fig.add_hline(y=destek, line_dash="dash", line_color="green", annotation_text="DİP DESTEK")
            fig.add_hline(y=direnc, line_dash="dash", line_color="red", annotation_text="ZİRVE DİRENÇ")
            st.plotly_chart(fig, use_container_width=True)

            # --- 3. UZMAN YORUMU VE STRATEJİ ---
            st.subheader("🕵️ Teknik Analist Yorumu")
            
            col_a, col_b = st.columns(2)
            with col_a:
                yorum_paragrafi = "Hisse için profesyonel görüş: "
                if fiyat > ema20:
                    yorum_paragrafi += "Fiyat kısa vadeli trendin üzerinde seyrediyor, yükseliş isteği güçlü. "
                else:
                    yorum_paragrafi += "Hissede satış baskısı hakim, toparlanma için EMA20 üzerine çıkmalı. "
                
                if rsi < 35:
                    yorum_paragrafi += "Göstergeler aşırı satıma işaret ediyor, teknik bir tepki alımı beklenebilir. "
                elif rsi > 65:
                    yorum_paragrafi += "Hisse teknik olarak yorulmuş, kar satışı düzeltmesi yaşanabilir. "
                
                st.info(yorum_paragrafi)

                st.write("### 🎯 Strateji Rehberi")
                st.write(f"✅ **İdeal Alım Bölgesi:** {destek:.2f} - {destek * 1.02:.2f} TL arası")
                st.write(f"🎯 **Hedef (Kâr Al):** {direnc:.2f} TL")
                st.write(f"🛑 **Zarar Kes (Stop):** {destek * 0.97:.2f} TL")

            with col_b:
                st.write("### 🗞️ Haber Duyarlılığı")
                if not haber_detay:
                    st.write("Yakın zamanda önemli bir haber akışı tespit edilemedi.")
                else:
                    for h in haber_detay[:5]:
                        st.write(f"{h['algı']} {h['baslik'][:85]}...")
                
                # Robot Puanı
                puan = 0
                if fiyat > destek * 1.05: puan += 1
                if 30 < rsi < 60: puan += 1
                if algı == "Pozitif 🟢": puan += 1
                if fiyat > ema20: puan += 1
                
                st.write(f"### ⭐ Robot Puanı: {puan}/4")
                if puan >= 3: st.success("STRATEJİ: GÜÇLÜ DURUŞ / POZİTİF")
                elif puan == 2: st.warning("STRATEJİ: BEKLE VE GÖR / NÖTR")
                else: st.error("STRATEJİ: ZAYIF GÖRÜNÜM / NEGATİF")

st.markdown("---")
st.caption("Yatırım tavsiyesi değildir. Veriler matematiksel algoritmalarla hesaplanmıştır.")