# -*- coding: utf-8 -*-
import io, re
from datetime import datetime
from typing import List, Dict

import streamlit as st
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

# =========================
# デモ用データ（モック）
# =========================
MATRIX_VERSION = "（デモ）令和7年5月28日施行対応版"
DEMO_MATRIX_RULES = [
    (r"\bencrypt(ion|ed|ing)?\b|\bAES\b|\bRSA\b", "5A002", "情報セキュリティ機器", "暗号関連語を検出（AES/RSA/encryption）"),
    (r"\b(5-axis|5軸|servo|CNC)\b", "2B001", "高精度工作機械", "多軸/サーボ等の高精度語を検出"),
    (r"\bdrone|UAV|flight controller\b", "9A012", "無人航空機関連", "UAV/ドローン関連語を検出"),
    (r"\bGaN|InP|GHz\b", "3A001", "高周波半導体/通信", "高周波・化合物半導体を示唆"),
]
SANCTIONED_DESTINATIONS = {"北朝鮮":"包括的禁止（デモ）","DPRK":"包括的禁止（デモ）","ロシア":"追加的措置対象（デモ）","イラン":"追加的措置対象（デモ）"}
DEMO_EUL = {"Acme Research Institute (Xland)":"EUL相当（デモ）：要デューデリ","Orbital Dynamics Lab":"EUL相当（デモ）：要デューデリ"}

# =========================
# 基本関数
# =========================
def extract_pdf_text(uploaded_file)->str:
    if not uploaded_file: return ""
    r = PdfReader(uploaded_file)
    return "\n".join([(p.extract_text() or "") for p in r.pages])

def toy_classify(text:str)->List[Dict]:
    hits=[]
    for pattern, clause, title, why in DEMO_MATRIX_RULES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append({"clause":clause,"title":title,"why":why})
    return hits

def build_report_pdf(payload:Dict)->bytes:
    buf=io.BytesIO()
    doc=SimpleDocTemplate(buf, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=16*mm, bottomMargin=16*mm)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="small", fontName="Helvetica", fontSize=9, leading=12))
    story=[]
    story.append(Paragraph("該非判定書・取引審査レポート（デモ）", styles["Title"]))
    story.append(Spacer(1,6))
    head=[["作成日時", datetime.now().strftime("%Y-%m-%d %H:%M")],["Matrix版", MATRIX_VERSION],["案件ID", payload.get("case_id","-")]]
    t=Table(head, colWidths=[35*mm,120*mm])
    t.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.6,colors.black),('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.whitesmoke)]))
    story+= [t, Spacer(1,10)]
    story.append(Paragraph("1. 物品情報", styles["Heading2"]))
    t2=Table([["品番・製品", payload.get("item_name") or "-"],
               ["HSコード（任意）", payload.get("hs_code") or "-"],
               ["仕様（抜粋）", payload.get("spec_excerpt") or "-"]],
               colWidths=[40*mm,115*mm])
    t2.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.6,colors.black),('INNERGRID',(0,0),(-1,-1),0.3,colors.grey)]))
    story+= [t2, Spacer(1,8)]
    story.append(Paragraph("2. 取引情報", styles["Heading2"]))
    t3=Table([["買主", payload.get("buyer") or "-"],
              ["エンドユーザー", payload.get("end_user") or "-"],
              ["仕向地", payload.get("destination") or "-"],
              ["用途", payload.get("end_use") or "-"]],
              colWidths=[40*mm,115*mm])
    t3.setStyle(TableStyle([('BOX',(0,0),(-1,-1),0.6,colors.black),('INNERGRID',(0,0),(-1,-1),0.3,colors.grey)]))
    story+= [t3, Spacer(1,8)]
    story.append(Paragraph("3. 該非判定（デモ）", styles["Heading2"]))
    hits=payload.get("hits",[])
    if hits:
        rows=[["候補条項","区分名称","根拠（キーワード）"]]+[[h["clause"],h["title"],h["why"]] for h in hits]
        t4=Table(rows, colWidths=[28*mm,40*mm,87*mm])
        t4.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),('BOX',(0,0),(-1,-1),0.6,colors.black),('INNERGRID',(0,0),(-1,-1),0.3,colors.grey)]))
        story.append(t4)
    else:
        story.append(Paragraph("該当候補は検出されませんでした。", styles["BodyText"]))
    story.append(Spacer(1,8))
    story.append(Paragraph("4. 取引審査（デモ）", styles["Heading2"]))
    scr=payload.get("screening",{})
    t5=Table([["項目","結果"],
              ["仕向地", scr.get("destination_flag") or "ヒットなし"],
              ["買主", scr.get("buyer_flag") or "ヒットなし"],
              ["エンドユーザー", scr.get("end_user_flag") or "ヒットなし"]],
              colWidths=[40*mm,115*mm])
    t5.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),('BOX',(0,0),(-1,-1),0.6,colors.black),('INNERGRID',(0,0),(-1,-1),0.3,colors.grey)]))
    story+= [t5, Spacer(1,8)]
    story.append(Paragraph("5. 総合判断（デモ）", styles["Heading2"]))
    story.append(Paragraph(payload.get("decision_text","—"), styles["BodyText"]))
    story+= [Spacer(1,12), Paragraph("【重要】本レポートはデモです。実運用では最新の法令・告示・通達に基づき社内責任者が判断してください。", styles["small"])]
    doc.build(story)
    return buf.getvalue()

# =========================
# ページ設定 & カスタムCSS（公式のtabs/theme APIに沿って構築）
# =========================
st.set_page_config(page_title="KSA 該非判定・取引先審査（デモ）", page_icon="🛡️", layout="wide")  # docs: st.set_page_config
st.markdown("""
<style>
:root{ --brand:#22d3ee; --ink:#e5f3ff; --muted:#8fb8d4; --panel:#0b1220; --panel2:#0e1626; --border:#19324a; }
.stApp{ background: radial-gradient(1200px 800px at 10% 0%, #0b1220 0%, #0a1222 50%, #07111d 100%); }
.block-container{ padding-top: 1.2rem; }
section[data-testid="stSidebar"]{ background:#0a1320; border-right:1px solid var(--border);}
h1,h2,h3,label,p,small,span,div{ color:var(--ink) !important; }
hr{ border:none;border-top:1px solid var(--border); margin:6px 0 16px 0;}
.card{ background:var(--panel2); border:1px solid var(--border); border-radius:14px; padding:16px; }
.badge{ display:inline-block; padding:4px 10px; border-radius:999px; background:#07293a; color:#9be7ff; border:1px solid #1f9dc3; font-size:12px;}
.step{ display:flex; gap:8px; align-items:center; }
.step > div { width:26px; height:26px; border-radius:50%; background:#073247; border:1px solid #1b5676; display:flex; align-items:center; justify-content:center; font-weight:700; color:#9be7ff;}
.primary-btn button{ background:linear-gradient(180deg,#1ec8e6,#17b3cf) !important; border:0 !important; color:#00151d !important; font-weight:700; border-radius:10px; }
input, textarea{ background:#0e1626 !important; color:var(--ink) !important; border-radius:10px !important; border:1px solid var(--border) !important; }
[data-testid="stFileUploaderDropzone"]{ background:#0e1626 !important; border:1px dashed var(--border) !important;}
.stTabs [data-baseweb="tab-list"]{ gap:8px; } .stTabs [data-baseweb="tab"]{ background:#0d1726; border:1px solid var(--border); border-bottom:none; border-radius:12px 12px 0 0; color:#cfeaff; }
.stTabs [aria-selected="true"]{ background:linear-gradient(180deg,#0b1a2b,#0e1626); color:white !important;}
</style>
""", unsafe_allow_html=True)  # tabs/theming: docs st.tabs & theming guides

# =========================
# サイドバー（KSAのメニュー構成に合わせる）
# =========================
with st.sidebar:
    st.markdown("### メニュー")
    st.write("ホーム")
    st.write("**01 該非判定**")   # PDFモックの文言に合わせる
    st.write("**02 取引先審査**")
    st.write("**03 過去履歴**")
    st.write("**04 問合せ**")
    st.write("設定 / ログアウト")
    st.markdown("---")
    st.markdown(f'<span class="badge">Matrix版: {MATRIX_VERSION}</span>', unsafe_allow_html=True)
    case_id = st.text_input("案件ID", value=f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    reviewer = st.text_input("審査担当者", value="田中 太郎")

st.title("🛡️ 該非判定・取引先審査（KSAモックに準拠・デモ）")

# 進行ステップ（上部）
st.markdown("""
<div class="card">
  <div class="step"><div>1</div><b>該非判定</b> &nbsp;&nbsp;<span class="muted">仕様のアップロードと候補条項の特定</span></div>
  <div class="step" style="margin-top:6px;"><div>2</div><b>取引先審査</b> &nbsp;&nbsp;<span class="muted">EUL/制裁・用途の簡易チェック</span></div>
  <div class="step" style="margin-top:6px;"><div>3</div><b>出力</b> &nbsp;&nbsp;<span class="muted">該非判定書＋審査票（PDF）</span></div>
</div>
""", unsafe_allow_html=True)

# =========================
# タブ（01～04）
# =========================
tab1, tab2, tab3, tab4 = st.tabs(["01 該非判定", "02 取引先審査", "03 過去履歴", "04 問合せ"])

# --- 01 該非判定 ---
with tab1:
    left, right = st.columns([1.3, 1])
    with left:
        st.subheader("品番・製品入力")
        c1, c2 = st.columns(2)
        with c1:
            item_name = st.text_input("品番・製品", placeholder="例）ART-40 / XYZフライトコントローラ")
            hs_code = st.text_input("HSコード（任意）", placeholder="例）8526.91")
        with c2:
            key_params = st.text_input("主な性能（任意）", placeholder="AES対応 / 5軸 / 3.2GHz / GaN など")

        st.markdown("#### 仕様PDFのアップロード")
        pdf = st.file_uploader("製品カタログ・仕様PDF", type=["pdf"])
        spec_text=""
        if pdf:
            with st.spinner("PDFテキストを抽出中…"):
                spec_text = extract_pdf_text(pdf)
            st.success(f"抽出文字数: 約 {len(spec_text)}")
            with st.expander("抽出テキスト（冒頭プレビュー）", expanded=False):
                st.write((spec_text[:2000]+"…") if len(spec_text)>2000 else (spec_text or "(テキスト抽出なし)"))

        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        run1 = st.button("🔎 デモ判定を実行")
        st.markdown('</div>', unsafe_allow_html=True)

        if run1:
            text = "\n".join([spec_text, item_name or "", key_params or ""]).lower()
            hits = toy_classify(text)
            st.session_state["hits"]=hits
            st.session_state["item_name"]=item_name
            st.session_state["hs_code"]=hs_code
            st.session_state["spec_excerpt"]=(spec_text[:600]+"…") if spec_text and len(spec_text)>600 else (spec_text or "-")

            st.markdown("#### 判定候補（デモ）")
            if hits:
                for h in hits:
                    st.markdown(f'<div class="card">🧩 <b>{h["clause"]}</b> / {h["title"]}<br/><span class="badge">{h["why"]}</span></div>', unsafe_allow_html=True)
            else:
                st.info("デモルールでは該当候補が検出されませんでした。")

    with right:
        st.subheader("該非判定書（モック）")
        st.markdown("""
- 「判定根拠資料の提供」「経緯・証跡」「資料」に紐づく出力を想定  
- 承認後、**該非判定書 ダウンロード** が可能（下のタブ2で総合判断後）
        """)

# --- 02 取引先審査 ---
with tab2:
    st.subheader("仕向地／相手先／用途の確認（デモ）")
    c1, c2 = st.columns(2)
    with c1:
        destination = st.text_input("仕向地", placeholder="例）ロシア / ドイツ / ベトナム")
        buyer = st.text_input("買主", placeholder="例）Orbital Dynamics Lab")
        end_user = st.text_input("エンドユーザー", placeholder="例）Acme Research Institute (Xland)")
        end_use = st.text_area("用途（自由記載）", placeholder="例）自律飛行の学術研究 など", height=100)

        st.markdown('<div class="primary-btn">', unsafe_allow_html=True)
        run2 = st.button("🛡️ デモ審査を実行")
        st.markdown('</div>', unsafe_allow_html=True)

        if run2:
            dest_flag = SANCTIONED_DESTINATIONS.get((destination or "").strip(), None) if destination else None
            buyer_flag = DEMO_EUL.get((buyer or "").strip(), None) if buyer else None
            end_user_flag = DEMO_EUL.get((end_user or "").strip(), None) if end_user else None

            needs_license = bool(st.session_state.get("hits")) or bool(dest_flag) or bool(buyer_flag) or bool(end_user_flag)
            decision_text = "【デモ】要ライセンス検討：仕向地/相手先のリスク、またはリスト該当候補あり。" if needs_license else "【デモ】現時点ではライセンス不要の可能性。ただし用途・最終需要者の適正性確認が必要。"

            # save
            st.session_state.update({
                "destination":destination,"buyer":buyer,"end_user":end_user,"end_use":end_use,
                "dest_flag":dest_flag,"buyer_flag":buyer_flag,"end_user_flag":end_user_flag,
                "decision_text":decision_text
            })
            st.success("デモ審査を完了しました。下段でレポート出力できます。")

    with c2:
        st.subheader("審査結果（デモ）")
        if "decision_text" in st.session_state:
            st.markdown(f'<div class="card"><b>総合判断</b><br/>{st.session_state["decision_text"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card">• 仕向地：{st.session_state.get("dest_flag") or "ヒットなし"}<br/>• 買主：{st.session_state.get("buyer_flag") or "ヒットなし"}<br/>• エンドユーザー：{st.session_state.get("end_user_flag") or "ヒットなし"}<br/>• Matrix版：{MATRIX_VERSION}</div>', unsafe_allow_html=True)

        st.markdown("---")
        if st.button("⬇️ 該非判定書＋審査票（PDF）を出力", disabled=("decision_text" not in st.session_state)):
            report_bytes = build_report_pdf({
                "case_id": st.session_state.get("case_id", case_id),
                "item_name": st.session_state.get("item_name"),
                "hs_code": st.session_state.get("hs_code"),
                "spec_excerpt": st.session_state.get("spec_excerpt"),
                "buyer": st.session_state.get("buyer"),
                "end_user": st.session_state.get("end_user"),
                "destination": st.session_state.get("destination"),
                "end_use": st.session_state.get("end_use"),
                "hits": st.session_state.get("hits", []),
                "screening": {
                    "destination_flag": st.session_state.get("dest_flag"),
                    "buyer_flag": st.session_state.get("buyer_flag"),
                    "end_user_flag": st.session_state.get("end_user_flag"),
                },
                "decision_text": st.session_state.get("decision_text","—")
            })
            st.download_button("PDFを保存する", report_bytes, file_name=f"{case_id}_demo_report.pdf", mime="application/pdf", use_container_width=True)

            # 履歴へ登録
            history = st.session_state.get("history", [])
            history.append({"time": datetime.now().strftime("%Y-%m-%d %H:%M"), "case_id": case_id,
                            "item": st.session_state.get("item_name") or "-", "dest": st.session_state.get("destination") or "-",
                            "decision": st.session_state.get("decision_text") or "-"})
            st.session_state["history"]=history

# --- 03 過去履歴 ---
with tab3:
    st.subheader("過去履歴")
    history = st.session_state.get("history", [])
    if not history:
        st.info("まだ履歴はありません。タブ1→タブ2の順で実行すると履歴に追加されます。")
    else:
        for row in reversed(history):
            st.markdown(f'<div class="card"><b>{row["time"]}</b> ｜ 案件ID：<code>{row["case_id"]}</code><br/>物品：{row["item"]} ／ 仕向地：{row["dest"]}<br/>判断：{row["decision"]}</div>', unsafe_allow_html=True)

# --- 04 問合せ ---
with tab4:
    st.subheader("問合せ")
    st.write("導入・PoC・追加機能に関するご相談はこちらから。")
    a,b = st.columns(2)
    with a:
        contact_name = st.text_input("お名前", "")
        contact_mail = st.text_input("メールアドレス", "")
    with b:
        company = st.text_input("会社名（任意）", "")
        tel = st.text_input("電話番号（任意）", "")
    msg = st.text_area("ご相談内容", height=120)
    if st.button("📩 送信（ダミー）"):
        st.success("送信しました（ダミー）。担当よりご連絡します。")

st.markdown("---")
st.caption("※ デモアプリです。法令判定は行いません。Streamlitのタブ/テーマAPIとReportLabでUI・PDFを構成。")
