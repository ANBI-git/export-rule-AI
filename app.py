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

from streamlit_option_menu import option_menu

# ----------------------------
# Hard-coded demo sample
# ----------------------------
DEMO = {
    "case_id": "DEMO-ART40",
    "item_name": "ART-40 フライトコントローラ",
    "hs_code": "8526.91",
    "key_params": "AES-256対応 / 3.2GHz MCU / 5-axis IMU / GaN RF module",
    "spec_text": """The ART-40 flight controller features AES-256 encryption, a 3.2 GHz microcontroller,
a 5-axis inertial measurement unit, and GaN-based RF front-end suitable for UAV applications.""",
    "destination": "ドイツ",
    "buyer": "Orbital Dynamics Lab",
    "end_user": "Acme Research Institute (Xland)",
    "end_use": "自律飛行制御の学術研究",
}

MATRIX_VERSION = "（デモ）令和7年5月28日施行対応版"
DEMO_MATRIX_RULES = [
    (r"\bencrypt(ion|ed|ing)?\b|\bAES\b|\bRSA\b", "5A002", "情報セキュリティ機器", "暗号関連語（AES/RSA/encryption）を検出"),
    (r"\b(5-axis|5軸|servo|CNC)\b", "2B001", "高精度工作機械", "多軸/サーボ等の高精度語を検出"),
    (r"\bdrone|UAV|flight controller\b", "9A012", "無人航空機関連", "UAV/ドローン関連語を検出"),
    (r"\bGaN|InP|GHz\b", "3A001", "高周波半導体/通信", "高周波・化合物半導体を示唆"),
]
SANCTIONED_DESTINATIONS = {"北朝鮮":"包括的禁止（デモ）","DPRK":"包括的禁止（デモ）","ロシア":"追加的措置対象（デモ）","イラン":"追加的措置対象（デモ）"}
DEMO_EUL = {
    # we want visible hits in demo to show “consider license”
    "Acme Research Institute (Xland)": "EUL相当（デモ）：要デューデリ",
    "Orbital Dynamics Lab": "EUL相当（デモ）：要デューデリ",
}

# ----------------------------
# Helpers
# ----------------------------
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
    doc=SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=16*mm, rightMargin=16*mm, topMargin=16*mm, bottomMargin=16*mm
    )
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="small", fontName="Helvetica", fontSize=9, leading=12))
    story=[]
    story.append(Paragraph("該非判定書・取引審査レポート（デモ）", styles["Title"]))
    story.append(Spacer(1,6))

    head=[["作成日時", datetime.now().strftime("%Y-%m-%d %H:%M")],
          ["Matrix版", MATRIX_VERSION],
          ["案件ID", payload.get("case_id","-")]]
    t=Table(head, colWidths=[35*mm,120*mm])
    t.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
        ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
    ]))
    story += [t, Spacer(1,10)]

    story.append(Paragraph("1. 物品情報", styles["Heading2"]))
    t2=Table([
        ["品番・製品", payload.get("item_name") or "-"],
        ["HSコード（任意）", payload.get("hs_code") or "-"],
        ["仕様（抜粋）", payload.get("spec_excerpt") or "-"],
    ], colWidths=[40*mm,115*mm])
    t2.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
    ]))
    story += [t2, Spacer(1,8)]

    story.append(Paragraph("2. 取引情報", styles["Heading2"]))
    t3=Table([
        ["買主", payload.get("buyer") or "-"],
        ["エンドユーザー", payload.get("end_user") or "-"],
        ["仕向地", payload.get("destination") or "-"],
        ["用途", payload.get("end_use") or "-"],
    ], colWidths=[40*mm,115*mm])
    t3.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
    ]))
    story += [t3, Spacer(1,8)]

    story.append(Paragraph("3. 該非判定（デモ）", styles["Heading2"]))
    hits=payload.get("hits",[])
    if hits:
        rows=[["候補条項","区分名称","根拠（キーワード）"]]+[[h["clause"],h["title"],h["why"]] for h in hits]
        t4=Table(rows, colWidths=[28*mm,40*mm,87*mm])
        t4.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
            ('BOX',(0,0),(-1,-1),0.6,colors.black),
            ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
        ]))
        story.append(t4)
    else:
        story.append(Paragraph("該当候補は検出されませんでした。", styles["BodyText"]))
    story.append(Spacer(1,8))

    story.append(Paragraph("4. 取引審査（デモ）", styles["Heading2"]))
    scr=payload.get("screening",{})
    t5=Table([
        ["項目","結果"],
        ["仕向地", scr.get("destination_flag") or "ヒットなし"],
        ["買主", scr.get("buyer_flag") or "ヒットなし"],
        ["エンドユーザー", scr.get("end_user_flag") or "ヒットなし"],
    ], colWidths=[40*mm,115*mm])
    t5.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
    ]))
    story += [t5, Spacer(1,8)]

    story.append(Paragraph("5. 総合判断（デモ）", styles["Heading2"]))
    story.append(Paragraph(payload.get("decision_text","—"), styles["BodyText"]))
    story += [Spacer(1,12),
              Paragraph("【重要】本レポートはデモです。実運用では最新の法令・告示・通達に基づき社内責任者が判断してください。", styles["small"])]

    doc.build(story)
    return buf.getvalue()

# ----------------------------
# Light theme + left menu styling
# ----------------------------
st.set_page_config(page_title="KSA 該非判定・取引先審査（自動デモ）", page_icon="🛡️", layout="wide")
st.markdown("""
<style>
:root{
  --bg:#f7f8fb; --panel:#ffffff; --ink:#0f172a; --muted:#475569;
  --brand:#0e7490; --border:#e5e7eb; --shadow:0 6px 18px rgba(0,0,0,.06);
}
.stApp { background: var(--bg); }
.block-container { padding-top: 1.2rem; }
section[data-testid="stSidebar"]{ background:#f0f4f8; border-right:1px solid var(--border); }
.card{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:16px; box-shadow: var(--shadow); }
.badge{ display:inline-block; padding:4px 10px; border-radius:999px; background:#e0f2fe; color:#075985; border:1px solid #bae6fd; font-size:12px; }
button[kind="primary"]{ background:var(--brand) !important; border:0 !important; color:#fff !important; font-weight:700; border-radius:10px; }
.stTabs [data-baseweb="tab"]{ background:#f2f6fb; border:1px solid var(--border); border-bottom:none; border-radius:10px 10px 0 0; }
.stTabs [aria-selected="true"]{ background:#fff; color:#0f172a !important; }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Sidebar nav buttons
# ----------------------------
with st.sidebar:
    st.markdown("### メニュー")
    choice = option_menu(
        None,
        ["01 該非判定", "02 取引先審査", "03 過去履歴", "04 問合せ"],
        icons=["search","shield-check","clock-history","envelope"],
        menu_icon="cast", default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#f0f4f8"},
            "icon": {"color": "#0e7490", "font-size": "16px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "margin":"4px 0",
                         "padding":"8px 12px", "border-radius":"8px", "color":"#0f172a"},
            "nav-link-selected": {"background-color": "#dff4ff"},
        },
    )
    st.markdown("---")
    st.markdown(f'<span class="badge">Matrix版: {MATRIX_VERSION}</span>', unsafe_allow_html=True)
    st.session_state["case_id"] = st.text_input("案件ID", value=DEMO["case_id"])
    st.toggle("デモモード(自動再生)", value=True, key="autoplay")

st.title("🛡️ 該非判定・取引先審査（自動デモ）")
st.caption("※ クリック1回で判定→審査→PDF出力まで到達する見せ方に最適化。")

# ----------------------------
# Unified demo runner
# ----------------------------
def run_full_demo():
    # 1) classification with demo text
    text = "\n".join([DEMO["spec_text"], DEMO["item_name"], DEMO["key_params"]]).lower()
    hits = toy_classify(text)

    # 2) screening with demo parties
    dest_flag = SANCTIONED_DESTINATIONS.get(DEMO["destination"], None)
    buyer_flag = DEMO_EUL.get(DEMO["buyer"], None)
    end_user_flag = DEMO_EUL.get(DEMO["end_user"], None)

    needs_license = bool(hits) or bool(dest_flag) or bool(buyer_flag) or bool(end_user_flag)
    decision_text = ("【デモ】要ライセンス検討：仕向地/相手先のリスク、またはリスト該当候補あり。"
                     if needs_license else
                     "【デモ】現時点ではライセンス不要の可能性。ただし用途・最終需要者の適正性確認が必要。")

    # cache in state
    st.session_state.update({
        "item_name": DEMO["item_name"],
        "hs_code": DEMO["hs_code"],
        "spec_excerpt": DEMO["spec_text"],
        "hits": hits,
        "destination": DEMO["destination"],
        "buyer": DEMO["buyer"],
        "end_user": DEMO["end_user"],
        "end_use": DEMO["end_use"],
        "dest_flag": dest_flag,
        "buyer_flag": buyer_flag,
        "end_user_flag": end_user_flag,
        "decision_text": decision_text
    })

    # 3) build report
    report_bytes = build_report_pdf({
        "case_id": st.session_state.get("case_id", "DEMO"),
        "item_name": DEMO["item_name"],
        "hs_code": DEMO["hs_code"],
        "spec_excerpt": DEMO["spec_text"],
        "buyer": DEMO["buyer"],
        "end_user": DEMO["end_user"],
        "destination": DEMO["destination"],
        "end_use": DEMO["end_use"],
        "hits": hits,
        "screening": {
            "destination_flag": dest_flag,
            "buyer_flag": buyer_flag,
            "end_user_flag": end_user_flag,
        },
        "decision_text": decision_text
    })
    st.session_state["report_bytes"] = report_bytes

# auto play if toggled
if st.session_state.get("autoplay", False):
    run_full_demo()

# ----------------------------
# Page: 01 該非判定
# ----------------------------
if choice == "01 該非判定":
    st.subheader("品番・製品入力（デモ用に自動入力済み）")
    with st.container():
        colA, colB = st.columns([1.4, 1])
        with colA:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            c1.text_input("品番・製品", value=DEMO["item_name"])
            c1.text_input("HSコード（任意）", value=DEMO["hs_code"])
            c2.text_input("主な性能（任意）", value=DEMO["key_params"])
            st.text_area("仕様テキスト（参考）", DEMO["spec_text"], height=120)
            st.markdown('</div>', unsafe_allow_html=True)

            st.button("🔎 デモを即実行", type="primary", on_click=run_full_demo)

            st.markdown("#### 判定候補（デモ）")
            hits = st.session_state.get("hits", [])
            if hits:
                for h in hits:
                    st.markdown(f'<div class="card">🧩 <b>{h["clause"]}</b> / {h["title"]}<br/><span class="badge">{h["why"]}</span></div>', unsafe_allow_html=True)
            else:
                st.info("右上の『デモを即実行』をクリックしてください。")

        with colB:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("操作ガイド")
            st.write("1) すでにデモ値が入っています")
            st.write("2) 『デモを即実行』→ 取引先審査に進む")
            st.write("3) PDFダウンロードまでワンクリック")
            st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# Page: 02 取引先審査
# ----------------------------
elif choice == "02 取引先審査":
    st.subheader("仕向地／相手先／用途（デモ値）")
    colA, colB = st.columns(2)
    with colA:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.text_input("仕向地", value=DEMO["destination"])
        st.text_input("買主", value=DEMO["buyer"])
        st.text_input("エンドユーザー", value=DEMO["end_user"])
        st.text_area("用途（自由記載）", value=DEMO["end_use"], height=100)
        st.markdown('</div>', unsafe_allow_html=True)

        st.button("🛡️ デモ審査を再実行", type="primary", on_click=run_full_demo)

    with colB:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("審査結果（デモ）")
        if "decision_text" in st.session_state:
            st.write("**総合判断**：", st.session_state["decision_text"])
            st.write("・仕向地：", st.session_state.get("dest_flag") or "ヒットなし")
            st.write("・買主：", st.session_state.get("buyer_flag") or "ヒットなし")
            st.write("・エンドユーザー：", st.session_state.get("end_user_flag") or "ヒットなし")
            st.write("・Matrix版：", MATRIX_VERSION)
        else:
            st.caption("左のボタンでデモを実行してください。")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        if st.session_state.get("report_bytes"):
            st.download_button(
                "⬇️ 該非判定書＋審査票（PDF）をダウンロード",
                st.session_state["report_bytes"],
                file_name=f"{st.session_state.get('case_id','DEMO')}_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("上の『デモ審査を再実行』またはサイドバーの自動再生をONにしてください。")
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# Page: 03 過去履歴 (simple, auto-add when user downloads)
# ----------------------------
elif choice == "03 過去履歴":
    st.subheader("過去履歴（デモ）")
    hist = st.session_state.get("history", [])
    if not hist and st.session_state.get("decision_text"):
        # seed one history row so it isn't empty in demo
        hist = [{
            "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "case_id": st.session_state.get("case_id","DEMO"),
            "item": DEMO["item_name"],
            "dest": DEMO["destination"],
            "decision": st.session_state.get("decision_text")
        }]
        st.session_state["history"] = hist

    if not hist:
        st.info("まだ履歴はありません。『01→02』の順でデモ実行してください。")
    else:
        for row in reversed(hist):
            st.markdown(
                f'<div class="card"><b>{row["time"]}</b> ｜ 案件ID：<code>{row["case_id"]}</code><br/>'
                f'物品：{row["item"]} ／ 仕向地：{row["dest"]}<br/>判断：{row["decision"]}</div>',
                unsafe_allow_html=True
            )

# ----------------------------
# Page: 04 問合せ
# ----------------------------
else:
    st.subheader("問合せ")
    st.write("導入・PoC・追加機能に関するご相談はこちら。")
    a,b = st.columns(2)
    with a:
        st.text_input("お名前", value="山田 太郎")
        st.text_input("メールアドレス", value="demo@example.com")
    with b:
        st.text_input("会社名（任意）", value="KSA International")
        st.text_input("電話番号（任意）", value="03-0000-0000")
    st.text_area("ご相談内容", value="デモ拝見。実機連携と料金プランについて相談したい。", height=120)
    st.button("📩 送信（ダミー）", type="primary")
