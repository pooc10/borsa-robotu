import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# --- TEKNİK HESAPLAMALAR ---
def teknik_hesapla(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    # Ortalamalar ve Destek/Direnç
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['Destek'] = df['Low'].rolling(window=20).min()
    df['Direnc'] = df['High'].rolling(window=20).max()
    return df

st.set_page_config(page_title="Pro BIST Robotu", layout="wide")
st.title("🦾 Profesyonel BIST Analiz Robotu")

ticker = st.text_input("Hisse Sembolü (Örn: THYAO, EREGL)", "THYAO").upper()
if not ticker.endswith(".IS"): ticker += ".IS"

if st.button("ANALİZİ BAŞLAT"):
    with st.spinner('Veriler taranıyor...'):
        hisse = yf.Ticker(ticker)
        df = hisse.history(period="6mo")
        
        if df.empty:
            st.error("Veri alınamadı!")
        else:
            df = teknik_hesapla(df)
            son_fiyat = df['Close'].iloc[-1]
            son_rsi = df['RSI'].iloc[-1]
            destek = df['Destek'].iloc[-1]
            direnc = df['Direnc'].iloc[-1]

            # --- METRİKLER ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Fiyat", f"{son_fiyat:.2f} TL")
            c2.metric("RSI (14)", f"{son_rsi:.2f}")
            c3.metric("Destek", f"{destek:.2f} TL")
            c4.metric("Direnç", f"{direnc:.2f} TL")

            # --- GRAFİK ---
            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Fiyat'))
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name='Trend', line=dict(color='orange')))
            st.plotly_chart(fig, use_container_width=True)

            # --- HABERLER (GÜNCELLENMİŞ GÜVENLİ YÖNTEM) ---
            st.subheader("📰 Son Haberler")
            try:
                haberler = hisse.news
                if haberler:
                    for n in haberler[:5]:
                        # Başlığı farklı yerlerde ara (yfinance güncellemeleri için)
                        title = n.get('title') or n.get('content', {}).get('title')
                        link = n.get('link') or n.get('content', {}).get('canonicalUrl', {}).get('url')
                        
                        if title:
                            if link:
                                st.markdown(f"- [{title}]({link})")
                            else:
                                st.markdown(f"- {title}")
                else:
                    st.info("Bu hisse için şu an güncel haber bulunamadı.")
            except Exception as e:
                st.write("Haberler şu an yüklenemiyor, lütfen daha sonra tekrar deneyin.")

            # --- ÖNERİ ---
            st.subheader("🤖 Robot Önerisi")
            if son_rsi < 35: st.success("🚀 ALIM BÖLGESİ: RSI çok düşük, tepki gelebilir.")
            elif son_rsi > 65: st.error("⚠️ SATIŞ BÖLGESİ: RSI çok yüksek, düzeltme gelebilir.")
            else: st.info("⚖️ NÖTR: Belirgin bir al-sat sinyali yok.")