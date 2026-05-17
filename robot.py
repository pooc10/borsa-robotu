import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- GELİŞMİŞ ANALİZ FONKSİYONLARI ---
def analiz_motoru(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + rs)) if not (loss == 0).all() else 50 # Basit RSI
    
    # Ortalamalar
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # Destek/Direnç (Son 30 Gün)
    df['Destek'] = df['Low'].rolling(window=30).min()
    df['Direnc'] = df['High'].rolling(window=30).max()
    
    # Volatilite (Oynaklık)
    df['Volatilite'] = df['Close'].pct_change().rolling(window=20).std() * 100
    return df

def haber_algisi_hesapla(haberler):
    pozitif_kelimeler = ['rekor', 'artış', 'büyüme', 'kazanç', 'pozitif', 'alım', 'yukarı', 'kâr', 'anlaşma', 'ihale', 'temettü', 'hedef']
    negatif_kelimeler = ['düşüş', 'kayıp', 'negatif', 'satış', 'aşağı', 'zarar', 'risk', 'kriz', 'dava', 'iptal', 'borç', 'enflasyon']
    
    skor = 0
    detaylar = []
    for n in haberler:
        baslik = (n.get('title') or n.get('content', {}).get('title', '')).lower()
        durum = "Nötr 😐"
        for p in pozitif_kelimeler:
            if p in baslik:
                skor += 1
                durum = "Pozitif 🟢"
        for neg in negatif_kelimeler:
            if neg in baslik:
                skor -= 1
                durum = "Negatif 🔴"
        detaylar.append({"baslik": baslik, "algı": durum})
    
    algı_sonucu = "Pozitif 🟢" if skor > 0 else "Negatif 🔴" if skor < 0 else "Nötr 🟡"
    return algı_sonucu, detaylar

# --- ARAYÜZ ---
st.set_page_config(page_title="Master BIST Analist", layout="wide")
st.title("🤖 Master BIST Analiz Sistemi")

ticker = st.text_input("Hisse Sembolü", "THYAO").upper()
if not ticker.endswith(".IS"): ticker += ".IS"

if st.button("TAM KAPSAMLI ANALİZİ BAŞLAT"):
    with st.spinner('Piyasa derinliği ve algoritma çalıştırılıyor...'):
        hisse = yf.Ticker(ticker)
        df = hisse.history(period="6mo")
        
        if df.empty:
            st.error("Veri alınamadı!")
        else:
            df = analiz_motoru(df)
            fiyat = df['Close'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            destek = df['Destek'].iloc[-1]
            direnc = df['Direnc'].iloc[-1]
            ema20 = df['EMA20'].iloc[-1]
            oynaklik = df['Volatilite'].iloc[-1]
            degisim = ((fiyat - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100

            # --- 1. RADAR PANELİ ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Anlık Fiyat", f"{fiyat:.2f} TL", f"{degisim:.2f}%")
            c2.metric("Piyasa Volatilitesi", f"%{oynaklik:.2f}")
            c3.metric("RSI Gücü", f"{rsi:.2f}")
            
            algı, haber_detay = haber_algisi_hesapla(hisse.news)
            c4.metric("Haber Algısı", algı)

            # --- 2. GRAFİK ---
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Mum'))
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='Kısa Trend', line=dict(color='orange')))
            fig.add_hline(y=destek, line_dash="dash", line_color="green", annotation_text="Kritik Destek")
            fig.add_hline(y=direnc, line_dash="dash", line_color="red", annotation_text="Kritik Direnç")
            st.plotly_chart(fig, use_container_width=True)

            # --- 3. UZMAN YORUMU VE STRATEJİ ---
            st.subheader("🕵️ Teknik Analist Yorumu")
            
            col_a, col_b = st.columns(2)
            with col_a:
                # Dinamik Yorum Oluşturma
                yorum = ""
                if fiyat > ema20:
                    yorum += "Hisse kısa vadeli yükselen trendini koruyor. "
                else:
                    yorum += "Fiyat hareketli ortalamanın altında, baskı devam ediyor. "
                
                if rsi < 40:
                    yorum += "RSI göstergesi aşırı satım bölgesine yakın, tepki alımları her an gelebilir. "
                elif rsi > 60:
                    yorum += "Hisse teknik olarak yorulmuş görünüyor, kar satışlarına dikkat edilmeli. "
                
                if oynaklik > 2:
                    yorum += "Hissede yüksek oynaklık var, stop-loss seviyelerine sadık kalınmalı."
                
                st.info(yorum)

                st.write("### 🎯 İşlem Seviyeleri")
                st.write(f"📍 **İdeal Alım Bölgesi:** {destek:.2f} - {destek * 1.02:.2f} TL")
                st.write(f"📍 **Kritik Direnç (Hedef):** {direnc:.2f} TL")
                st.write(f"🛑 **Stop-Loss (Zarar Kes):** {destek * 0.97:.2f} TL")

            with col_b:
                st.write("### 🗞️ Haber Algı Analizi")
                for h in haber_detay[:5]:
                    st.write(f"{h['algı']} {h['baslik'][:80]}...")
                
                # Puanlama Sistemi
                puan = 0
                if fiyat > destek: puan += 1
                if rsi < 50: puan += 1
                if algı == "Pozitif 🟢": puan += 1
                if fiyat > ema20: puan += 1
                
                st.write(f"### ⭐️ Robot Puanı: {puan}/4")
                if puan >= 3: st.success("SONUÇ: GÜÇLÜ AL / TUT")
                elif puan == 2: st.warning("SONUÇ: İZLE / KADEMELİ AL")
                else: st.error("SONUÇ: SAT / UZAK DUR")

st.markdown("---")
st.caption("Yatırım tavsiyesi değildir. Veriler matematiksel indikatörler ve haber taraması ile üretilmiştir.")