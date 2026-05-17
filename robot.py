import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- MATEMATİKSEL ANALİZ MOTORU (Hata Vermez) ---
def teknik_hesapla(df):
    # RSI Hesapla
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Hareketli Ortalamalar
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # Destek ve Direnç (Son 20 günün zirve ve dip noktaları)
    df['Destek'] = df['Low'].rolling(window=20).min()
    df['Direnc'] = df['High'].rolling(window=20).max()
    return df

# --- ARAYÜZ ---
st.set_page_config(page_title="Pro BIST Analiz", layout="wide")
st.title("🦾 Profesyonel BIST Analiz Robotu")

ticker = st.text_input("Hisse Sembolü (Örn: THYAO, EREGL)", "THYAO").upper()
if not ticker.endswith(".IS"): ticker += ".IS"

if st.button("DERİN ANALİZİ BAŞLAT"):
    with st.spinner('Piyasa verileri ve haberler taranıyor...'):
        hisse = yf.Ticker(ticker)
        df = hisse.history(period="6mo")
        
        if df.empty:
            st.error("Hisse verisi alınamadı!")
        else:
            df = teknik_hesapla(df)
            son_fiyat = df['Close'].iloc[-1]
            son_rsi = df['RSI'].iloc[-1]
            destek = df['Destek'].iloc[-1]
            direnc = df['Direnc'].iloc[-1]
            ema20 = df['EMA20'].iloc[-1]
            
            # --- ÜST METRİKLER ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Güncel Fiyat", f"{son_fiyat:.2f} TL")
            c2.metric("RSI (14)", f"{son_rsi:.2f}")
            c3.metric("Destek (Alım)", f"{destek:.2f} TL")
            c4.metric("Direnç (Satış)", f"{direnc:.2f} TL")

            # --- GRAFİK ---
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Fiyat'))
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='Trend (EMA20)', line=dict(color='orange', width=1.5)))
            fig.add_hline(y=destek, line_dash="dash", line_color="green", annotation_text="DESTEK")
            fig.add_hline(y=direnc, line_dash="dash", line_color="red", annotation_text="DİRENÇ")
            st.plotly_chart(fig, use_container_width=True)

            # --- AL-SAT VE STRATEJİ ---
            st.subheader("🤖 Robotun İşlem Önerisi")
            col_s1, col_s2 = st.columns(2)
            
            with col_s1:
                st.info("🎯 **Giriş/Çıkış Seviyeleri**")
                if son_fiyat <= destek * 1.01:
                    st.success(f"GİRİŞ SİNYALİ: Fiyat desteğe ({destek:.2f}) çok yakın. Alım için uygun olabilir.")
                elif son_fiyat >= direnc * 0.99:
                    st.error(f"ÇIKIŞ SİNYALİ: Fiyat dirence ({direnc:.2f}) dayandı. Kar satışı gelebilir.")
                else:
                    st.write(f"İşlem Aralığında: Beklemede kalın. Hedef Direnç: {direnc:.2f}")

            with col_s2:
                st.info("📈 **Trend ve RSI Durumu**")
                if son_rsi < 30: st.warning("Aşırı Satım (Tepki Yükselişi Beklenir)")
                elif son_rsi > 70: st.warning("Aşırı Alım (Düzeltme Beklenir)")
                
                if son_fiyat > ema20: st.write("Trend Yönü: ✅ YUKARI (Pozitif)")
                else: st.write("Trend Yönü: ❌ AŞAĞI (Negatif)")

            # --- HABERLER ---
            st.subheader("📰 Son Dakika Haberleri")
            try:
                haberler = hisse.news[:5]
                if haberler:
                    for n in haberler:
                        st.markdown(f"- **{n['title']}**")
                else:
                    st.write("Bu hisse için yakın zamanda haber bulunamadı.")
            except:
                st.write("Haber servisine şu an ulaşılamıyor.")

st.markdown("---")
st.caption("Yatırım tavsiyesi değildir. Matematiksel modellemedir.")