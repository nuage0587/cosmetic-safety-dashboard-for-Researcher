import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# ============================================================================
# 페이지 설정
# ============================================================================
st.set_page_config(
    page_title="피부 안정성 평가 대시보드",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 스타일
# ============================================================================
st.markdown("""
<style>
.stApp { background-color: #f1f5f9; }

[data-testid="stSidebar"] > div:first-child {
    background: #ffffff;
    border-right: 1px solid #e2e8f0;
}

.stTabs [data-baseweb="tab-list"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 4px 6px;
    gap: 4px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 0.875rem;
    font-weight: 500;
    color: #64748b;
    border: none;
    background: transparent;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #f1f5f9;
    color: #334155;
}
.stTabs [aria-selected="true"] {
    background: #6366f1 !important;
    color: #ffffff !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none; }

[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 20px 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

h2 {
    color: #0f172a;
    font-size: 1.25rem !important;
    font-weight: 700 !important;
    margin-bottom: 4px !important;
}

.compound-count {
    background: #f1f5f9;
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
    color: #475569;
    font-size: 0.875rem;
}
.compound-count span {
    display: block;
    font-size: 1.75rem;
    font-weight: 700;
    color: #6366f1;
    line-height: 1.2;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 데이터 로드
# ============================================================================
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    df_summary    = pd.read_csv(DATA_DIR / "성분_CAS_요약.csv")
    df_detail     = pd.read_csv(DATA_DIR / "상세_MoS.csv")
    df_ref        = pd.read_csv(DATA_DIR / "전체_레퍼런스.csv")
    df_ref        = df_ref.loc[:, ~df_ref.columns.duplicated()]
    df_timeseries = pd.read_csv(DATA_DIR / "pbpk_concentration_timeseries_surface_model.csv")
    return df_summary, df_detail, df_ref, df_timeseries

df_summary, df_detail, df_ref, df_timeseries = load_data()

# ============================================================================
# 헬퍼 함수
# ============================================================================
def warn_no_compound():
    st.warning("⚠️ 분석할 성분을 사이드바에서 선택해주세요.")

def toggle_country(country):
    current = set(st.session_state.reg_country_filter)
    if country == '전체':
        st.session_state.reg_country_filter = {'전체'}
    else:
        current.discard('전체')
        if country in current:
            current.discard(country)
            if not current:
                current.add('전체')
        else:
            current.add(country)
        st.session_state.reg_country_filter = current

# ============================================================================
# 사이드바
# ============================================================================
st.sidebar.title("필터 설정")
st.sidebar.markdown("---")

available_compounds = sorted(df_summary['성분명'].dropna().unique())
selected_compounds = st.sidebar.multiselect(
    "분석할 성분 선택",
    available_compounds,
    default=available_compounds[:3] if len(available_compounds) >= 3 else available_compounds,
    help="복합 안정성을 평가할 성분들을 선택하세요",
    key="compound_selector"
)

st.sidebar.markdown("<br>" * 4, unsafe_allow_html=True)
st.sidebar.markdown(
    f"""<div class="compound-count">
        <span>{len(selected_compounds)}</span>
        선택된 성분
    </div>""",
    unsafe_allow_html=True
)

# ============================================================================
# 메인 헤더 + 탭
# ============================================================================
st.title("피부 안정성 평가 대시보드")
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 안정성 요약",
    "📈 안정성 분석",
    "🕐 시간 거동 분석",
    "🌍 규제 정보",
    "📋 상세 데이터",
    "📚 기준치 출처",
])

if not selected_compounds:
    for tab in [tab1, tab2, tab3, tab4, tab5, tab6]:
        with tab:
            warn_no_compound()
else:
    # ── 공통 데이터 준비 ────────────────────────────────────────────────────
    df_summary_selected = df_summary[df_summary['성분명'].isin(selected_compounds)].copy()
    df_detail_selected  = df_detail[df_detail['성분명'].isin(selected_compounds)].copy()
    selected_cas        = df_summary_selected['CAS번호'].dropna().unique()

    df_detail_summary = (
        df_detail_selected
        .groupby(['성분명', 'CAS번호'], as_index=False)
        .agg(
            log_MoS       =('log_MoS',       'min'),
            MoS           =('MoS',           'min'),
            Tmax_h        =('Tmax_h',        'mean'),
            Cmax_mg_L     =('Cmax_mg_L',     'mean'),
            AUC_mg_h_L    =('AUC_mg_h_L',    'sum'),
            SED_mg_kg_day =('SED_mg_kg_day', 'mean'),
        )
    )

    # ── 탭 1: 안정성 요약 ───────────────────────────────────────────────────
    with tab1:
        st.header("📊 안정성 요약")
        st.markdown("선택된 성분들의 안전성 지표 및 주요 KPI를 확인합니다.")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns(5)

        avg_mos   = df_summary_selected['최저_MoS'].mean()
        bar_color = "#10b981" if avg_mos >= 100 else "#ef4444"

        with col1:
            st.markdown("**대표 MoS 평균**")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=avg_mos,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "대표 MoS", 'font': {'size': 13}},
                number={'font': {'size': 26}},
                gauge={
                    'axis': {'range': [0, 200], 'tickwidth': 1},
                    'bar': {'color': bar_color},
                    'bgcolor': 'white',
                    'borderwidth': 1,
                    'bordercolor': '#e2e8f0',
                    'steps': [
                        {'range': [0,   50],  'color': "#fee2e2"},
                        {'range': [50,  100], 'color': "#fef3c7"},
                        {'range': [100, 200], 'color': "#dcfce7"},
                    ],
                    'threshold': {
                        'line': {'color': "#dc2626", 'width': 3},
                        'thickness': 0.75,
                        'value': 100,
                    },
                }
            ))
            fig_gauge.update_layout(
                height=280,
                margin=dict(l=10, r=10, t=30, b=10),
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_gauge, use_container_width=True)
            if avg_mos >= 100:
                st.success("✅ 안전 (대표 MoS ≥ 100)")
            else:
                st.error("⚠️ 위험 (대표 MoS < 100)")

        avg_tmax = df_detail_summary['Tmax_h'].mean() if not df_detail_summary.empty else np.nan
        with col2:
            st.metric(
                label="⏱ Tmax (시간)",
                value=f"{avg_tmax:.2f}" if not np.isnan(avg_tmax) else "-",
                help="선택된 성분의 평균 최고 흡수 도달 시간"
            )

        avg_cmax = df_detail_summary['Cmax_mg_L'].mean() if not df_detail_summary.empty else np.nan
        with col3:
            st.metric(
                label="📈 Cmax (mg/L)",
                value=f"{avg_cmax:.4f}" if not np.isnan(avg_cmax) else "-",
                help="선택된 성분의 평균 최고 흡수 농도"
            )

        total_auc = df_detail_summary['AUC_mg_h_L'].sum() if not df_detail_summary.empty else np.nan
        with col4:
            st.metric(
                label="📊 AUC 합계 (mg·h/L)",
                value=f"{total_auc:.4f}" if not np.isnan(total_auc) else "-",
                help="선택된 성분의 총 노출량"
            )

        representative_sed = df_summary_selected['대표_SED_mg_kg_day'].mean()
        with col5:
            st.metric(
                label="💊 대표 SED (mg/kg/day)",
                value=f"{representative_sed:.4f}" if not np.isnan(representative_sed) else "-",
                help="선택된 성분의 평균 시스템 노출량"
            )

    # ── 탭 2: 안정성 분석 ───────────────────────────────────────────────────
    with tab2:
        st.header("📈 안정성 분석")
        st.markdown("선택된 성분들의 Log MoS 분포와 위험도 순위를 분석합니다.")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        col_dist, col_rank = st.columns(2)

        with col_dist:
            st.markdown("**안정성 분포 (Log MoS)**")
            if df_detail_selected.empty:
                st.info("ℹ️ Log MoS 분포 데이터를 불러올 수 없습니다.")
            else:
                fig_hist = px.histogram(
                    df_detail_selected,
                    x='log_MoS',
                    color='성분명',
                    barmode='overlay',
                    opacity=0.7,
                    nbins=30,
                    labels={'log_MoS': 'Log MoS', 'count': '개수', '성분명': '성분'},
                )
                fig_hist.add_vline(
                    x=np.log10(100),
                    line_dash="dash", line_color="#dc2626",
                    annotation_text="안전 기준 (MoS=100)",
                    annotation_position="top right"
                )
                fig_hist.update_layout(
                    height=420,
                    xaxis_title="Log MoS",
                    yaxis_title="개수",
                    showlegend=True,
                    legend=dict(title="성분", font=dict(size=11)),
                    plot_bgcolor='white',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(gridcolor='#f1f5f9'),
                    yaxis=dict(gridcolor='#f1f5f9'),
                    margin=dict(l=0, r=20, t=20, b=20),
                )
                st.plotly_chart(fig_hist, use_container_width=True)

        with col_rank:
            st.markdown("**물질별 위험도 순위**")
            if df_detail_summary.empty:
                st.info("ℹ️ 위험도 순위를 계산할 수 없습니다.")
            else:
                df_rank = df_detail_summary[['성분명', 'CAS번호', 'log_MoS', 'MoS']].copy()
                df_rank = df_rank.sort_values('log_MoS', ascending=True).reset_index(drop=True)
                df_rank['순위'] = range(1, len(df_rank) + 1)

                span = max(df_rank['log_MoS'].max() - df_rank['log_MoS'].min(), 0.1)
                df_rank['log_MoS_pct'] = (df_rank['log_MoS'] - df_rank['log_MoS'].min()) / span * 100
                df_rank['안전도'] = df_rank['MoS'].apply(
                    lambda x: '✅ 안전' if x >= 100 else '⚠️ 위험'
                )

                display_df = df_rank[['순위', '성분명', 'CAS번호', 'log_MoS', 'log_MoS_pct', 'MoS', '안전도']].rename(
                    columns={
                        '성분명':       '물질명',
                        'log_MoS':     'Log MoS',
                        'log_MoS_pct': 'Log MoS 비율',
                        'MoS':         'MoS 값',
                    }
                )
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True,
                    height=420,
                    column_config={
                        'Log MoS 비율': st.column_config.ProgressColumn(
                            'Log MoS 비율',
                            format="%.0f%%",
                            min_value=0,
                            max_value=100,
                        ),
                    }
                )

    # ── 탭 3: 시간 거동 분석 ────────────────────────────────────────────────
    with tab3:
        st.header("🕐 시간에 따른 체내 거동")
        st.markdown("선택된 성분들의 체내 농도 변화 추이를 분석합니다.")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        df_ts_selected = df_timeseries[df_timeseries['Compound'].isin(selected_compounds)].copy()

        if df_ts_selected.empty:
            st.info("ℹ️ 선택된 물질의 시계열 데이터가 없습니다.")
        else:
            col_surface, col_skin, col_blood = st.columns(3)

            layout_ts = dict(
                height=420,
                showlegend=False,
                margin=dict(t=36, b=20, l=0, r=0),
                plot_bgcolor='white',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(gridcolor='#f1f5f9'),
                yaxis=dict(gridcolor='#f1f5f9'),
            )

            with col_surface:
                fig = px.line(
                    df_ts_selected, x='time_h', y='A_surface_mg', color='Compound',
                    title="피부 표면 잔존량",
                    labels={'time_h': '시간 (h)', 'A_surface_mg': '양 (mg)', 'Compound': '성분'}
                )
                fig.update_layout(**layout_ts)
                st.plotly_chart(fig, use_container_width=True)

            with col_skin:
                fig = px.line(
                    df_ts_selected, x='time_h', y='A_skin_mg', color='Compound',
                    title="피부층 체류량",
                    labels={'time_h': '시간 (h)', 'A_skin_mg': '양 (mg)', 'Compound': '성분'}
                )
                fig.update_layout(**layout_ts)
                st.plotly_chart(fig, use_container_width=True)

            with col_blood:
                fig = px.line(
                    df_ts_selected, x='time_h', y='C_blood_mg_L', color='Compound',
                    title="혈중 농도",
                    labels={'time_h': '시간 (h)', 'C_blood_mg_L': '농도 (mg/L)', 'Compound': '성분'}
                )
                fig.update_layout(**layout_ts)
                st.plotly_chart(fig, use_container_width=True)

    # ── 탭 4: 규제 정보 ─────────────────────────────────────────────────────
    with tab4:
        st.header("🌍 규제 정보")
        st.markdown("선택된 성분들의 국가별 규제 및 제한사항을 확인합니다.")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if df_detail_selected.empty:
            st.info("ℹ️ 선택된 성분의 상세 MoS 데이터가 없습니다.")
        else:
            df_regulation = (
                df_detail_selected[
                    ['성분명', 'CAS번호', '규제국가', '규제구분', '단서조항', '제한사항', '제한농도값_percent']
                ]
                .drop_duplicates()
                .rename(columns={
                    '성분명':            '물질명',
                    '규제국가':          '규제 국가',
                    '규제구분':          '규제 구분',
                    '단서조항':          '단서 조항',
                    '제한사항':          '제한 사항',
                    '제한농도값_percent': '제한농도(%)',
                })
            )
            df_regulation['규제 국가'] = df_regulation['규제 국가'].fillna('규제 없음')
            df_regulation['제한 사항'] = df_regulation['제한 사항'].fillna('정보 없음')
            df_regulation['규제 상태'] = df_regulation['규제 국가'].apply(
                lambda x: '✅ 규제 없음' if x == '규제 없음' else f'⚠️ {x}'
            )

            all_countries_global = sorted(df_detail['규제국가'].dropna().unique().tolist())
            button_list          = ['전체'] + all_countries_global
            available_countries  = set(df_regulation['규제 국가'].unique())

            if 'reg_country_filter' not in st.session_state:
                st.session_state.reg_country_filter = {'전체'}

            MAX_PER_ROW = 8
            for row_start in range(0, len(button_list), MAX_PER_ROW):
                row_items = button_list[row_start:row_start + MAX_PER_ROW]
                cols = st.columns(len(row_items))
                for i, country in enumerate(row_items):
                    with cols[i]:
                        is_active    = country in st.session_state.reg_country_filter
                        is_available = (country == '전체') or (country in available_countries)
                        if st.button(
                            country,
                            key=f"reg_btn_{country}",
                            type="primary" if is_active else "secondary",
                            disabled=not is_available,
                            use_container_width=True,
                        ):
                            toggle_country(country)
                            st.rerun()

            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

            if '전체' in st.session_state.reg_country_filter:
                df_reg_filtered = df_regulation
            else:
                active_available = st.session_state.reg_country_filter & available_countries
                df_reg_filtered = (
                    df_regulation[df_regulation['규제 국가'].isin(active_available)]
                    if active_available else df_regulation
                )

            st.caption(f"{len(df_reg_filtered)}건 표시 중")
            st.dataframe(
                df_reg_filtered[['물질명', 'CAS번호', '규제 상태', '규제 국가', '규제 구분', '단서 조항', '제한 사항', '제한농도(%)']],
                use_container_width=True,
                hide_index=True,
                column_config={
                    '제한농도(%)': st.column_config.NumberColumn('제한농도(%)', format="%.2f%%"),
                }
            )

    # ── 탭 5: 상세 데이터 ───────────────────────────────────────────────────
    with tab5:
        st.header("📋 상세 데이터")
        st.markdown("선택된 성분들의 상세 MoS 및 규제정보를 확인합니다.")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        detail_cols = [
            '성분명', 'CAS번호', 'MoS', 'log_MoS', 'Tmax_h', 'Cmax_mg_L', 'AUC_mg_h_L',
            'SED_mg_kg_day', '제한사항', '기준치_출처', '기준치_출처_URL', '기준치_근거요약'
        ]
        available_cols = [col for col in detail_cols if col in df_detail_selected.columns]

        df_display = df_detail_selected[available_cols].rename(columns={
            '성분명':         '물질명',
            'log_MoS':       'Log MoS',
            'AUC_mg_h_L':    'AUC (mg·h/L)',
            'SED_mg_kg_day': 'SED (mg/kg/day)',
            '기준치_출처':    '기준치 출처',
            '기준치_출처_URL':'기준치 출처 URL',
            '기준치_근거요약':'기준치 근거 요약',
        })

        col_cfg = {
            'MoS':     st.column_config.NumberColumn('MoS',     format="%.2f"),
            'Log MoS': st.column_config.NumberColumn('Log MoS', format="%.3f"),
        }
        if '기준치_출처_URL' in df_detail_selected.columns:
            col_cfg['기준치 출처 URL'] = st.column_config.LinkColumn('기준치 출처 URL')

        st.dataframe(df_display, use_container_width=True, column_config=col_cfg)

    # ── 탭 6: 기준치 출처 ───────────────────────────────────────────────────
    with tab6:
        st.header("📚 기준치 출처")
        st.markdown("선택된 성분들의 독성 기준치 출처 및 근거를 확인합니다.")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        df_ref_selected = df_ref[df_ref['CAS번호'].isin(selected_cas)].copy()

        if df_ref_selected.empty:
            st.info("ℹ️ 선택된 성분에 대한 기준치 출처 정보가 없습니다.")
        else:
            ref_cols = [
                '성분명', 'CAS번호', '적용기준치_mg_kg_day', '적용기준치_종류',
                '출처', '출처_URL', '근거요약', '우선순위', '적용상태'
            ]
            available_ref_cols = [col for col in ref_cols if col in df_ref_selected.columns]

            df_ref_display = df_ref_selected[available_ref_cols].rename(columns={
                '성분명':               '물질명',
                '적용기준치_mg_kg_day':  '적용 기준치 (mg/kg/day)',
                '적용기준치_종류':        '기준치 종류',
                '출처_URL':             '출처 URL',
                '근거요약':              '근거 요약',
                '우선순위':              '우선순위',
                '적용상태':              '적용 상태',
            })

            col_cfg_ref = {}
            if '출처_URL' in df_ref_selected.columns:
                col_cfg_ref['출처 URL'] = st.column_config.LinkColumn('출처 URL')
            if '우선순위' in df_ref_selected.columns:
                col_cfg_ref['우선순위'] = st.column_config.NumberColumn('우선순위', format="%d위")

            st.dataframe(df_ref_display, use_container_width=True, column_config=col_cfg_ref)

# ============================================================================
# 푸터
# ============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#94a3b8; font-size:12px;'>"
    "피부 안정성 평가 연구원 대시보드 | PBPK 모델 기반 분석"
    "</div>",
    unsafe_allow_html=True
)
