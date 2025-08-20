import streamlit as st
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Plotlyのインポートをtry-except文で囲む
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError as e:
    st.error(f"Plotlyライブラリが見つかりません: {e}")
    st.info("以下のコマンドを実行してください: pip install plotly")
    PLOTLY_AVAILABLE = False

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
    data_status = {"population": False, "age": {}}
    
    # 人口動態データの読み込み
    population_2024 = None
    try:
        population_2024 = pd.read_csv("人口動態/population_included/2024_population.csv", 
                                    encoding='utf-8', skiprows=5)
        data_status["population"] = True
        st.success("✅ 2024年人口動態データを読み込みました")
    except FileNotFoundError:
        st.error("❌ 人口動態データファイルが見つかりません: 人口動態/population_included/2024_population.csv")
    except Exception as e:
        st.error(f"❌ 人口動態データの読み込みエラー: {e}")
    
    # 年齢別人口データの読み込み
    age_data = {}
    for year in [2022, 2023, 2024]:
        try:
            df = pd.read_csv(f"人口動態/prefecture_population_age/{year}_population_age.csv", 
                           encoding='utf-8', skiprows=2)
            age_data[year] = df
            data_status["age"][year] = True
            st.success(f"✅ {year}年年齢別データを読み込みました")
        except FileNotFoundError:
            st.warning(f"⚠️ {year}年の年齢別データファイルが見つかりません")
            data_status["age"][year] = False
        except Exception as e:
            st.warning(f"⚠️ {year}年の年齢別データ読み込みエラー: {e}")
            data_status["age"][year] = False
    
    return population_2024, age_data, data_status

def create_sample_data():
    """サンプルデータの作成（デモ用）"""
    st.info("📝 サンプルデータを使用してデモンストレーションを行います")
    
    # サンプル都道府県データ
    prefectures = ['東京都', '神奈川県', '大阪府', '愛知県', '埼玉県', '千葉県', '兵庫県', '北海道', '福岡県', '静岡県']
    
    sample_data = {
        '都道府県名': prefectures,
        '総人口': np.random.randint(500000, 14000000, 10),
        '人口増減率': np.random.uniform(-1.5, 1.0, 10),
        '人口増減数': np.random.randint(-50000, 50000, 10),
        '自然増減数': np.random.randint(-30000, 10000, 10),
        '社会増減数': np.random.randint(-20000, 40000, 10),
        '出生数': np.random.randint(5000, 100000, 10),
        '死亡数': np.random.randint(10000, 150000, 10)
    }
    
    return pd.DataFrame(sample_data)

def clean_population_data(df):
    """人口動態データのクリーニング"""
    if df is None:
        return None
    
    try:
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
    except Exception as e:
        st.error(f"データクリーニングエラー: {e}")
        return None

def create_basic_charts(df):
    """基本的なチャートを作成（Plotlyなしでも動作）"""
    if not PLOTLY_AVAILABLE:
        st.warning("Plotlyがインストールされていないため、基本的な表示のみ行います")
        return None
    
    # 人口増減率の棒グラフ
    fig = px.bar(
        df.head(10),
        x='都道府県名',
        y='人口増減率',
        title='都道府県別人口増減率（TOP10）',
        color='人口増減率',
        color_continuous_scale='RdYlBu'
    )
    fig.update_xaxis(tickangle=45)
    return fig

def main():
    """メイン関数"""
    
    # ヘッダー
    st.markdown('<div class="main-header">📊 日本人口動態ダッシュボード</div>', unsafe_allow_html=True)
    
    # Plotlyの確認
    if not PLOTLY_AVAILABLE:
        st.error("⚠️ Plotlyライブラリが必要です。以下のコマンドを実行してください：")
        st.code("pip install plotly", language="bash")
        st.stop()
    
    # データ読み込み
    with st.spinner('データを読み込んでいます...'):
        pop_data, age_data, data_status = load_data()
    
    # データの状態確認
    st.sidebar.title("📋 データ状況")
    st.sidebar.write("**人口動態データ:**", "✅ 利用可能" if data_status["population"] else "❌ 未利用")
    
    for year, status in data_status["age"].items():
        st.sidebar.write(f"**{year}年年齢別:**", "✅ 利用可能" if status else "❌ 未利用")
    
    # データがない場合はサンプルデータを使用
    if pop_data is None:
        st.warning("実際のデータが読み込めないため、サンプルデータを使用します")
        pop_cleaned = create_sample_data()
    else:
        pop_cleaned = clean_population_data(pop_data)
    
    if pop_cleaned is None:
        st.error("データの処理に失敗しました")
        st.stop()
    
    # メインダッシュボード
    st.markdown('<div class="sub-header">📈 全国概況</div>', unsafe_allow_html=True)
    
    # 主要指標
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_pop = pop_cleaned['総人口'].sum()
        st.metric("総人口", f"{total_pop:,.0f}人")
    
    with col2:
        avg_change_rate = pop_cleaned['人口増減率'].mean()
        st.metric("平均人口増減率", f"{avg_change_rate:.2f}%")
    
    with col3:
        if '自然増減数' in pop_cleaned.columns:
            natural_change = pop_cleaned['自然増減数'].sum()
            st.metric("自然増減（全国）", f"{natural_change:,.0f}人")
        else:
            st.metric("自然増減（全国）", "データなし")
    
    with col4:
        if '社会増減数' in pop_cleaned.columns:
            social_change = pop_cleaned['社会増減数'].sum()
            st.metric("社会増減（全国）", f"{social_change:,.0f}人")
        else:
            st.metric("社会増減（全国）", "データなし")
    
    # 都道府県別ランキング
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
    
    # チャート表示
    if PLOTLY_AVAILABLE:
        st.markdown('<div class="sub-header">📊 可視化</div>', unsafe_allow_html=True)
        chart = create_basic_charts(pop_cleaned.sort_values('人口増減率', ascending=False))
        if chart:
            st.plotly_chart(chart, use_container_width=True)
    
    # データ表示
    st.markdown('<div class="sub-header">📋 データテーブル</div>', unsafe_allow_html=True)
    st.dataframe(pop_cleaned, use_container_width=True)
    
    # フッター
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **必要なパッケージ**
    ```bash
    pip install streamlit plotly pandas numpy
    ```
    
    **データファイル構成**
    ```
    人口動態/
    ├── population_included/
    │   └── 2024_population.csv
    └── prefecture_population_age/
        ├── 2022_population_age.csv
        ├── 2023_population_age.csv
        └── 2024_population_age.csv
    ```
    """)

if __name__ == "__main__":
    main()
