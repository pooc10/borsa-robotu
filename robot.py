import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk

# Sayfa Genişliği ve Tema
st.set_page_config(page_title="Pro Borsa Robotu", layout="wide")

# NLTK İndir (Haber Analizi için)
@st.cache_resource
def setup_nltk():
    nltk.download('vader_lexicon')

setup_nltk()

def analiz_motoru(ticker):
    hisse = yf.Ticker(ticker)
    df = hisse.history(period="6mo")
    if df.empty: return None, None, None
    
    # --- TEKNİK ANALİZ ---
    df['RSI'] = ta.rsi(df['Close'], length=14)
    df['EMA20'] = ta.ema(df['Close'], length=20)
    df['EMA50'] = ta.ema(df['Close'], length=50)
    
    # Destek ve Direnç Hesaplama (Son 30 günün en alt ve üst noktaları)
    destek = df['Low'].tail(30).min()
    direnc = df['High'].tail(30).max()
    
    # Trend Analizi
    son_fiyat = df['Close'].iloc[-1]
    ema20 = df['EMA20'].iloc[-1]
    trend = "YUKARI 🚀" if son_fiyat > ema20 else "AŞAĞI 📉"
    
    # --- HABER ANALİZİ ---
    haber_listesi = []
    sentiment_skor = 0
    try:
        raw_news = hisse.news
        sia = SentimentIntensityAnalyzer()
        for n in raw_news[:5]:
            # Haber yapısı yfinance versiyonuna göre değişebilir, güvenli çekim:
            title = n.get('content', {}).get('title', n.get('title', 'Başlık Yok'))
            summary = n.get('content', {}).get('summary', '')
            link = n.get('content', {}).get('canonicalUrl', {}).get('url', '#')
            
            skor = sia.polarity_scores(title)['compound']
            sentiment_skor += skor
            haber_listesi.append({"baslik": title, "skor": skor, "link": link})
        sentiment_skor /= 5 if len(raw_news) > 0 else 1
    except: pass
    
    return df, {"destek": destek, "direnc": direnc, "trend": trend, "haber_skor": sentiment_skor}, haber_listesi

# --- ARAYÜZ ---
st.title("🦾 Yapay Zeka Destekli BIST Robotu")

ticker_input = st.text_input("Hisse Kodu (Örn: THYAO, SASA, EREGL)", "THYAO").upper()
if not ticker_input.endswith(".IS"): ticker_input += ".IS"

if st.button("DERİN ANALİZİ BAŞLAT"):
    df, teknik, haberler = analiz_motoru(ticker_input)
    
    if df is not None:
        # Üst Metrikler
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Son Fiyat", f"{df['Close'].iloc[-1]:.2f} TL")
        c2.metric("Ana Trend", teknik['trend'])
        c3.metric("Destek (Alım)", f"{teknik['destek']:.2f} TL", delta_color="normal")
        c4.metric("Direnç (Satış)", f"{teknik['direnc']:.2f} TL", delta_color="inverse")

        # Grafik
        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Fiyat'))
        fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='Hızlı Trend (EMA20)', line=dict(color='yellow')))
        # Destek/Direnç Çizgileri
        fig.add_hline(y=teknik['destek'], line_dash="dash", line_color="green", annotation_text="Destek (Alım Bölgesi)")
        fig.add_hline(y=teknik['direnc'], line_dash="dash", line_color="red", annotation_text="Direnç (Kar Al)")
        st.plotly_chart(fig, use_container_width=True)

        # Strateji Kartları
        col_st1, col_st2 = st.columns(2)
        
        with col_st1:
            st.subheader("📊 Al-Sat Stratejisi")
            fiyat = df['Close'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            
            if fiyat <= teknik['destek'] * 1.02:
                st.success(f"💎 ALIM BÖLGESİNDE: Fiyat desteğe çok yakın ({fiyat:.2f}). Buradan tepki gelebilir.")
            elif fiyat >= teknik['direnc'] * 0.98:
                st.error(f"⚠️ SATIŞ BÖLGESİNDE: Fiyat dirence dayandı ({fiyat:.2f}). Kar realizasyonu düşünülebilir.")
            
            if rsi < 30: st.warning("🔥 RSI Aşırı Satım: Teknik olarak tepki yükselişi kapıda!")
            elif rsi > 70: st.warning("🧊 RSI Aşırı Alım: Hisse çok şişmiş, düzeltme gelebilir.")
            else: st.info("🧘 Nötr Bölge: Trend yönünde kalınmalı.")

        with col_st2:
            st.subheader("📰 Son Haberler & Duyarlılık")
            h_renk = "🟢 Pozitif" if teknik['haber_skor'] > 0.05 else "🔴 Negatif" if teknik['haber_skor'] < -0.05 else "🟡 Nötr"
            st.write(f"Piyasa Algısı: **{h_renk}**")
            
            for h in haberler:
                st.markdown(f"- [{h['baslik']}]({h['link']})")

    else:
        st.error("Veri alınamadı!")

st.markdown("---")
st.caption("🤖 Robot Notu: Bu analizler matematiksel verilere dayanır. Borsada risk her zaman vardır.")