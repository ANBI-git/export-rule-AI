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

# Optional (for nicer left menu)
from streamlit_option_menu import option_menu

# ----------------------------
# Demo data (mock)
# ----------------------------
MATRIX_VERSION = "（デモ）令和7年5月28日施行対応版"
DEMO_MATRIX_RULES = [
    (r"\bencrypt(ion|ed|ing)?\b|\bAES\b|\bRSA\b", "5A002", "情報セキュリティ機器", "暗号関連語（AES/RSA/encryption）を検出"),
    (r"\b(5-axis|5軸|servo|CNC)\b", "2B001", "高精度工作機械", "多軸/サーボ等の高精度語を検出"),
    (r"\bdrone|UAV|flight controller\b", "9A012", "無人航空機関連", "UAV/ドローン関連語を検出"),
    (r"\bGaN|InP|GHz\b", "3A001", "高周波半導体/通信", "高周波・化合物半導体を示唆"),
]
SANCTIONED_DESTINATIONS = {
    "北朝鮮":"包括的禁止（デモ）", "DPRK":"包括的禁止（デモ）",
    "ロシア":"追加的措置対象（デモ）","イラン":"追加的措置対象（デモ）"
}
DEMO_EUL = {
    "Acme Research Institute (Xland)":"EUL相当（デモ）：要デューデリ",
    "Orbital Dynamics Lab":"EUL相当（デモ）：要デューデリ",
}

# ----------------------------
# Helpers
# ----------------------------
def extract_pdf_text(uploaded_file)->str:
    if not uploaded_file: return ""
    reader = PdfReader(uploaded_file)
    return "\n".join([(p.extract_text() or "") for p in reader.pages])

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
    story+= [t, Spacer(1,10)]

    story.append(Paragraph("1. 物品情報", styles["Heading2"]))
    t2=Table([
        ["品番・製品", payload.get("item_name") or "-"],
        ["HSコード（任意）", payload.get("hs_code") or "-"],
        ["仕様（抜粋）", payload.get("spec_excerpt") or "-"]
    ], colWidths=[40*mm,115*mm])
    t2.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
    ]))
    story+= [t2, Spacer(1,8)]

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
    story+= [t3, Spacer(1,8)]

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
    story+= [t5, Spacer(1,8)]

    story.append(Paragraph("5. 総合判断（デモ）", styles["Heading2"]))
    story.append(Paragraph(payload.get("decision_text","—"), styles["BodyText"]))
    story+= [Spacer(1,12),
             Paragraph("【重要】本レポートはデモです。実運用では最新の法令・告示・通達に基づき社内責任者が判断してください。", styles["small"])]

    doc.build(story)
    return buf.getvalue()

# ----------------------------
# Page & Light Theme (CSS)
# ----------------------------
st.set_page_config(page_title="KSA 該非判定・取引先審査（デモ）", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
/* Light theme */
:root{
  --bg:#f7f8fb; --panel:#ffffff; --ink:#0f172a; --muted:#475569;
  --brand:#0e7490; --brand-2:#38bdf8; --border:#e5e7eb; --shadow:0 6px 18px rgba(0,0,0,.06);
}
.stApp { background: var(--bg); }
.block-container { padding-top: 1.2rem; }

/* Sidebar menu */
section[data-testid="stSidebar"]{
  background: #f0f4f8; border-right:1px solid var(--border);
}
.sidebar-title{font-weight:800;font-size:20px;color:var(--brand);}
.menu-desc{ color:var(--muted); font-size:12px; margin-top:-6px; }

/* Cards & inputs */
.card{ background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:16px; box-shadow: var(--shadow); }
input, textarea{ border-radius:10px !important; }

/* Buttons */
button[kind="primary"]{ background:var(--brand) !important; border:0 !important; color:#fff !important; font-weight:700; border-radius:10px; }
button[kind="secondary"]{ border-radius:10px; }

/* Tabs */
.stTabs [data-baseweb="tab-list"]{ gap:8px; }
.stTabs [data-baseweb="tab"]{
  background:#f2f6fb; border:1px solid var(--border); border-bottom:none; border-radius:12px 12px 0 0; color:#334155;
}
.stTabs [aria-selected="true"]{ background:#fff; color:#0f172a !important; }

/* Headings */
h1,h2,h3,label,p,small,span,div { color: var(--ink) !important; }
hr{ border:none; border-top:1px solid var(--border); margin:6px 0 16px 0; }
.badge{ display:inline-block; padding:4px 10px; border-radius:999px; background:#e0f2fe; color:#075985; border:1px solid #bae6fd; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------
# Sidebar with left menu buttons (01–04)
# ----------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">メニュー</div>', unsafe_allow_html=True)
    st.markdown('<div class="menu-desc">KSAモックに合わせた4ステップ</div>', unsafe_allow_html=True)

    choice = option_menu(
        None,
        ["ホーム", "01 該非判定", "02 取引先審査", "03 過去履歴", "04 問合せ"],
        icons=["house","search","shield-check","clock-history","envelope"],
        menu_icon="cast", default_index=1,
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
    case_id = st.text_input("案件ID", value=f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    reviewer = st.text_input("審査担当者", value="田中 太郎")

st.title("🛡️ 該非判定・取引先審査（デモ）")
st.caption("※ デモUI。PDFアップロード→候補条項→取引先審査→PDFレポート出力まで体験できます。")

# ----------------------------
# Pages
# ----------------------------
def page_classification():
    st.subheader("品番・製品入力")
    with st.container():
        colA, colB = st.columns([1.4, 1])
        with colA:
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    item_name = st.text_input("品番・製品", placeholder="例）ART-40 / XYZフライトコントローラ")
                    hs_code = st.text_input("HSコード（任意）", placeholder="例）8526.91")
                with c2:
                    key_params = st.text_input("主な性能（任意）", placeholder="AES対応 / 5軸 / 3.2GHz / GaN など")
                st.markdown("#### 仕様PDFのアップロード")
                pdf = st.file_uploader("製品カタログ・仕様PDF", type=["pdf"])
                st.markdown('</div>', unsafe_allow_html=True)

                spec_text=""
                if pdf:
                    with st.spinner("PDFテキストを抽出中…"):
                        spec_text = extract_pdf_text(pdf)
                    st.success(f"抽出文字数: 約 {len(spec_text)}")
                    with st.expander("抽出テキスト（冒頭プレビュー）", expanded=False):
                        st.write((spec_text[:2000]+"…") if len(spec_text)>2000 else (spec_text or "(テキスト抽出なし)"))

                run1 = st.button("🔎 デモ判定を実行", type="primary")
                if run1:
                    text = "\n".join([spec_text, item_name or "", key_params or ""]).lower()
                    hits = toy_classify(text)
                    st.session_state["hits"]=hits
                    st.session_state["item_name"]=item_name
                    st.session_state["hs_code"]=hs_code
                    st.session_state["spec_excerpt"]=(spec_text[:600]+"…") if spec_text and len(spec_text)>600 else (spec_text or "-")

            st.markdown("#### 判定候補（デモ）")
            hits = st.session_state.get("hits", [])
            if hits:
                for h in hits:
                    st.markdown(f'<div class="card">🧩 <b>{h["clause"]}</b> / {h["title"]}<br/><span class="badge">{h["why"]}</span></div>', unsafe_allow_html=True)
            else:
                st.info("デモルールでは該当候補が検出されませんでした。")

        with colB:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("操作ガイド")
            st.write("1) PDFと製品情報を入力")
            st.write("2) 『デモ判定を実行』をクリック")
            st.write("3) タブまたは左メニューから『02 取引先審査』へ")
            st.markdown('</div>', unsafe_allow_html=True)

def page_screening():
    st.subheader("仕向地／相手先／用途の確認（デモ）")
    colA, colB = st.columns(2)
    with colA:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        destination = st.text_input("仕向地", placeholder="例）ロシア / ドイツ / ベトナム")
        buyer = st.text_input("買主", placeholder="例）Orbital Dynamics Lab")
        end_user = st.text_input("エンドユーザー", placeholder="例）Acme Research Institute (Xland)")
        end_use = st.text_area("用途（自由記載）", placeholder="例）自律飛行の学術研究 など", height=100)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🛡️ デモ審査を実行", type="primary"):
            dest_flag = SANCTIONED_DESTINATIONS.get((destination or "").strip(), None) if destination else None
            buyer_flag = DEMO_EUL.get((buyer or "").strip(), None) if buyer else None
            end_user_flag = DEMO_EUL.get((end_user or "").strip(), None) if end_user else None

            needs_license = bool(st.session_state.get("hits")) or bool(dest_flag) or bool(buyer_flag) or bool(end_user_flag)
            decision_text = ("【デモ】要ライセンス検討：仕向地/相手先のリスク、またはリスト該当候補あり。"
                             if needs_license else
                             "【デモ】現時点ではライセンス不要の可能性。ただし用途・最終需要者の適正性確認が必要。")

            st.session_state.update({
                "destination":destination,"buyer":buyer,"end_user":end_user,"end_use":end_use,
                "dest_flag":dest_flag,"buyer_flag":buyer_flag,"end_user_flag":end_user_flag,
                "decision_text":decision_text
            })
            st.success("デモ審査を完了しました。右側でレポート出力できます。")

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
            st.caption("左で審査を実行するとここに結果が表示されます。")
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        if st.button("⬇️ 該非判定書＋審査票（PDF）を出力",
                     disabled=("decision_text" not in st.session_state), type="primary"):
            report_bytes = build_report_pdf({
                "case_id": st.session_state.get("case_id", st.session_state.get("case_id", "")) or st.session_state.get("case_id", ""),
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
            st.download_button("PDFを保存する", report_bytes,
                               file_name=f"{st.session_state.get('case_id','DEMO')}_report.pdf",
                               mime="application/pdf", use_container_width=True)

            # add to history
            hist = st.session_state.get("history", [])
            hist.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "case_id": st.session_state.get("case_id","DEMO"),
                "item": st.session_state.get("item_name") or "-",
                "dest": st.session_state.get("destination") or "-",
                "decision": st.session_state.get("decision_text") or "-"
            })
            st.session_state["history"] = hist
        st.markdown('</div>', unsafe_allow_html=True)

def page_history():
    st.subheader("過去履歴")
    hist = st.session_state.get("history", [])
    if not hist:
        st.info("まだ履歴はありません。『01 該非判定』→『02 取引先審査』の順で実行すると追加されます。")
        return
    for row in reversed(hist):
        st.markdown(
            f'<div class="card"><b>{row["time"]}</b> ｜ 案件ID：<code>{row["case_id"]}</code><br/>'
            f'物品：{row["item"]} ／ 仕向地：{row["dest"]}<br/>判断：{row["decision"]}</div>',
            unsafe_allow_html=True
        )

def page_contact():
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
    if st.button("📩 送信（ダミー）", type="primary"):
        st.success("送信しました（ダミー）。担当よりご連絡します。")

# Route by sidebar choice
if choice in ["ホーム", "01 該非判定"]:
    page_classification()
elif choice == "02 取引先審査":
    page_screening()
elif choice == "03 過去履歴":
    page_history()
else:
    page_contact()

st.markdown("---")
st.caption("※ デモアプリです。法令判定は行いません。UIはライトテーマ・左メニューボタン・カードUIで構成。")
