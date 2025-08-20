import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ページ設定
st.set_page_config(
    page_title="日本人口動態ダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #A23B72;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #2E86AB;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """データの読み込みとクリーニング"""
    try:
        # 人口動態データの読み込み
        population_2024 = pd.read_csv("人口動態/population_included/2024_population.csv", 
                                    encoding='utf-8', skiprows=5)
        
        # 年齢別人口データの読み込み
        age_data = {}
        for year in [2022, 2023, 2024]:
            try:
                df = pd.read_csv(f"人口動態/prefecture_population_age/{year}_population_age.csv", 
                               encoding='utf-8', skiprows=2)
                age_data[year] = df
            except:
                st.warning(f"{year}年のデータを読み込めませんでした。")
        
        return population_2024, age_data
    except Exception as e:
        st.error(f"データの読み込みに失敗しました: {e}")
        return None, None

def clean_population_data(df):
    """人口動態データのクリーニング"""
    if df is None:
        return None
    
    # 列名の設定
    columns = ['団体コード', '都道府県名', '男性人口', '女性人口', '総人口', '世帯数',
              '転入国内', '転入国外', '転入計', '出生数', 'その他増', '増加計',
              '転出国内', '転出国外', '転出計', '死亡数', 'その他減', '減少計',
              '人口増減数', '人口増減率', '自然増減数', '自然増減率', '社会増減数', '社会増減率']
    
    # 列数を調整
    if len(df.columns) >= len(columns):
        df.columns = columns[:len(df.columns)]
    
    # 合計行を除外
    df = df[df['都道府県名'] != '合計'].copy()
    
    # 数値列の変換
    numeric_cols = ['男性人口', '女性人口', '総人口', '世帯数', '出生数', '死亡数',
                   '人口増減数', '人口増減率', '自然増減数', '自然増減率', 
                   '社会増減数', '社会増減率']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace(' ', ''), 
                                  errors='coerce')
    
    return df

def clean_age_data(age_data):
    """年齢別データのクリーニング"""
    cleaned_data = {}
    
    for year, df in age_data.items():
        if df is None:
            continue
            
        # 合計行のみを抽出
        total_row = df[df.iloc[:, 1] == '合計'].copy()
        if not total_row.empty:
            # 数値列を変換
            numeric_cols = total_row.columns[3:]  # 年齢階級のカラム
            for col in numeric_cols:
                total_row.loc[:, col] = pd.to_numeric(
                    total_row[col].astype(str).str.replace(',', '').str.replace(' ', ''), 
                    errors='coerce'
                )
            cleaned_data[year] = total_row
    
    return cleaned_data

def create_prefecture_ranking(df):
    """都道府県別ランキング作成"""
    ranking_data = df[['都道府県名', '人口増減数', '人口増減率']].copy()
    ranking_data = ranking_data.sort_values('人口増減率', ascending=False)
    return ranking_data

def create_population_pyramid(age_data, year=2024):
    """人口ピラミッドの作成"""
    if year not in age_data:
        return None
    
    df = age_data[year]
    
    # 年齢階級の列名を取得（4列目以降）
    age_columns = df.columns[4:25]  # 0歳～4歳から100歳以上まで
    
    # 男女別データを取得
    male_data = df[df.iloc[:, 2] == '男'].iloc[0, 4:25] if not df[df.iloc[:, 2] == '男'].empty else None
    female_data = df[df.iloc[:, 2] == '女'].iloc[0, 4:25] if not df[df.iloc[:, 2] == '女'].empty else None
    
    if male_data is None or female_data is None:
        return None
    
    # 年齢階級のラベル
    age_labels = ['0-4歳', '5-9歳', '10-14歳', '15-19歳', '20-24歳', '25-29歳', '30-34歳',
                  '35-39歳', '40-44歳', '45-49歳', '50-54歳', '55-59歳', '60-64歳',
                  '65-69歳', '70-74歳', '75-79歳', '80-84歳', '85-89歳', '90-94歳',
                  '95-99歳', '100歳以上']
    
    # グラフ作成
    fig = go.Figure()
    
    # 男性（左側）
    fig.add_trace(go.Bar(
        y=age_labels,
        x=-male_data.values,  # 負の値で左側に表示
        orientation='h',
        name='男性',
        marker_color='#3498db',
        text=[f'{x:,.0f}' for x in male_data.values],
        textposition='inside'
    ))
    
    # 女性（右側）
    fig.add_trace(go.Bar(
        y=age_labels,
        x=female_data.values,
        orientation='h',
        name='女性',
        marker_color='#e74c3c',
        text=[f'{x:,.0f}' for x in female_data.values],
        textposition='inside'
    ))
    
    fig.update_layout(
        title=f'{year}年 全国年齢別人口ピラミッド',
        xaxis_title='人口（人）',
        yaxis_title='年齢階級',
        barmode='relative',
        height=800,
        xaxis=dict(
            tickformat=',.0f',
            title_font_size=14
        ),
        yaxis=dict(
            title_font_size=14,
            categoryorder='array',
            categoryarray=age_labels[::-1]  # 上から0歳になるように逆順
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=100, b=50)
    )
    
    return fig

def create_time_series_chart(age_data):
    """年齢階級別時系列チャート"""
    if not age_data:
        return None
    
    # 年齢グループの定義
    age_groups = {
        '0-14歳（年少人口）': [0, 1, 2],  # 0-4, 5-9, 10-14歳のインデックス
        '15-64歳（生産年齢人口）': list(range(3, 13)),  # 15-64歳
        '65歳以上（高齢人口）': list(range(13, 21))  # 65歳以上
    }
    
    years = list(age_data.keys())
    time_series_data = []
    
    for year in years:
        df = age_data[year]
        total_row = df[df.iloc[:, 2] == '計']
        if total_row.empty:
            continue
            
        row_data = {'年': year}
        
        for group_name, indices in age_groups.items():
            total = 0
            for idx in indices:
                if idx + 4 < len(total_row.columns):  # 4列目から年齢データ開始
                    val = total_row.iloc[0, idx + 4]
                    if pd.notna(val):
                        total += val
            row_data[group_name] = total
        
        time_series_data.append(row_data)
    
    if not time_series_data:
        return None
    
    ts_df = pd.DataFrame(time_series_data)
    
    fig = go.Figure()
    
    colors = ['#3498db', '#2ecc71', '#e74c3c']
    
    for i, group in enumerate(['0-14歳（年少人口）', '15-64歳（生産年齢人口）', '65歳以上（高齢人口）']):
        fig.add_trace(go.Scatter(
            x=ts_df['年'],
            y=ts_df[group],
            mode='lines+markers',
            name=group,
            line=dict(color=colors[i], width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title='年齢階級別人口の推移（全国）',
        xaxis_title='年',
        yaxis_title='人口（人）',
        height=500,
        hovermode='x unified'
    )
    
    return fig

def main():
    """メイン関数"""
    
    # ヘッダー
    st.markdown('<div class="main-header">📊 日本人口動態ダッシュボード</div>', unsafe_allow_html=True)
    
    # データ読み込み
    with st.spinner('データを読み込んでいます...'):
        pop_data, age_data = load_data()
    
    if pop_data is None:
        st.error("データの読み込みに失敗しました。CSVファイルのパスを確認してください。")
        st.stop()
    
    # データクリーニング
    pop_cleaned = clean_population_data(pop_data)
    age_cleaned = clean_age_data(age_data)
    
    # サイドバー
    st.sidebar.title("📋 分析オプション")
    
    page = st.sidebar.selectbox(
        "表示ページを選択",
        ["メインダッシュボード", "人口動態分析", "年齢構成分析", "地域比較分析"]
    )
    
    # メインダッシュボード
    if page == "メインダッシュボード":
        st.markdown('<div class="sub-header">📈 全国概況</div>', unsafe_allow_html=True)
        
        if pop_cleaned is not None:
            # 主要指標
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_pop = pop_cleaned['総人口'].sum()
                st.metric("総人口", f"{total_pop:,.0f}人")
            
            with col2:
                avg_change_rate = pop_cleaned['人口増減率'].mean()
                st.metric("平均人口増減率", f"{avg_change_rate:.2f}%")
            
            with col3:
                natural_change = pop_cleaned['自然増減数'].sum()
                st.metric("自然増減（全国）", f"{natural_change:,.0f}人")
            
            with col4:
                social_change = pop_cleaned['社会増減数'].sum()
                st.metric("社会増減（全国）", f"{social_change:,.0f}人")
        
        # 都道府県別ランキング
        if pop_cleaned is not None:
            st.markdown('<div class="sub-header">🏆 都道府県別人口増減率ランキング</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 増加率TOP10")
                top_10 = pop_cleaned.nlargest(10, '人口増減率')[['都道府県名', '人口増減率', '人口増減数']]
                st.dataframe(top_10, use_container_width=True)
            
            with col2:
                st.subheader("📉 減少率TOP10")
                bottom_10 = pop_cleaned.nsmallest(10, '人口増減率')[['都道府県名', '人口増減率', '人口増減数']]
                st.dataframe(bottom_10, use_container_width=True)
        
        # 人口ピラミッド
        if age_cleaned:
            st.markdown('<div class="sub-header">👥 年齢構成（人口ピラミッド）</div>', unsafe_allow_html=True)
            
            year_selection = st.selectbox("表示年を選択", sorted(age_cleaned.keys(), reverse=True))
            pyramid_fig = create_population_pyramid(age_cleaned, year_selection)
            
            if pyramid_fig:
                st.plotly_chart(pyramid_fig, use_container_width=True)
    
    # 人口動態分析ページ
    elif page == "人口動態分析":
        st.markdown('<div class="sub-header">📊 人口動態詳細分析</div>', unsafe_allow_html=True)
        
        if pop_cleaned is not None:
            # 散布図：自然増減 vs 社会増減
            fig_scatter = px.scatter(
                pop_cleaned,
                x='自然増減数',
                y='社会増減数',
                hover_data=['都道府県名'],
                title='自然増減 vs 社会増減',
                labels={'自然増減数': '自然増減数（人）', '社会増減数': '社会増減数（人）'}
            )
            
            fig_scatter.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray")
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # 出生率と死亡率の比較
            col1, col2 = st.columns(2)
            
            with col1:
                # 出生数TOP10
                birth_top = pop_cleaned.nlargest(10, '出生数')[['都道府県名', '出生数']]
                fig_birth = px.bar(
                    birth_top,
                    x='都道府県名',
                    y='出生数',
                    title='出生数TOP10（都道府県別）'
                )
                fig_birth.update_xaxis(tickangle=45)
                st.plotly_chart(fig_birth, use_container_width=True)
            
            with col2:
                # 死亡数TOP10
                death_top = pop_cleaned.nlargest(10, '死亡数')[['都道府県名', '死亡数']]
                fig_death = px.bar(
                    death_top,
                    x='都道府県名',
                    y='死亡数',
                    title='死亡数TOP10（都道府県別）',
                    color_discrete_sequence=['#e74c3c']
                )
                fig_death.update_xaxis(tickangle=45)
                st.plotly_chart(fig_death, use_container_width=True)
    
    # 年齢構成分析ページ
    elif page == "年齢構成分析":
        st.markdown('<div class="sub-header">👶👨👴 年齢構成分析</div>', unsafe_allow_html=True)
        
        if age_cleaned:
            # 時系列チャート
            ts_fig = create_time_series_chart(age_cleaned)
            if ts_fig:
                st.plotly_chart(ts_fig, use_container_width=True)
            
            # 年齢階級別データテーブル
            st.subheader("📋 年齢階級別人口データ")
            
            selected_year = st.selectbox("表示年を選択", sorted(age_cleaned.keys(), reverse=True), key='age_year')
            
            if selected_year in age_cleaned:
                df = age_cleaned[selected_year]
                st.dataframe(df, use_container_width=True)
    
    # 地域比較分析ページ
    elif page == "地域比較分析":
        st.markdown('<div class="sub-header">🗾 地域比較分析</div>', unsafe_allow_html=True)
        
        if pop_cleaned is not None:
            # 東京圏の定義
            tokyo_area = ['東京都', '神奈川県', '埼玉県', '千葉県']
            pop_cleaned['地域分類'] = pop_cleaned['都道府県名'].apply(
                lambda x: '東京圏' if x in tokyo_area else 'その他地域'
            )
            
            # 地域別比較
            region_summary = pop_cleaned.groupby('地域分類').agg({
                '総人口': 'sum',
                '人口増減数': 'sum',
                '自然増減数': 'sum',
                '社会増減数': 'sum'
            }).reset_index()
            
            st.subheader("🏙️ 東京圏 vs その他地域")
            st.dataframe(region_summary, use_container_width=True)
            
            # 可視化
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pop = px.pie(
                    region_summary,
                    values='総人口',
                    names='地域分類',
                    title='総人口の地域別構成比'
                )
                st.plotly_chart(fig_pop, use_container_width=True)
            
            with col2:
                fig_change = px.bar(
                    region_summary,
                    x='地域分類',
                    y='人口増減数',
                    title='人口増減数の地域別比較'
                )
                st.plotly_chart(fig_change, use_container_width=True)
    
    # フッター
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **データソース**
    - 住民基本台帳人口・世帯数
    - 年齢階級別人口統計
    
    **開発情報**
    - 作成者: Claude Code
    - 更新日: 2024年
    """)

if __name__ == "__main__":
    main()
