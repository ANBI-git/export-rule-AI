# -*- coding: utf-8 -*-
import io
import re
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
    # (regex, clause, title, rationale)
    (r"\bencrypt(ion|ed|ing)?\b|\bAES\b|\bRSA\b", "5A002", "情報セキュリティ機器", "暗号関連語を検出（AES/RSA/encryption）"),
    (r"\b(5-axis|5軸|servo|CNC)\b", "2B001", "高精度工作機械", "多軸/サーボ等の高精度語を検出"),
    (r"\bdrone|UAV|flight controller\b", "9A012", "無人航空機関連", "UAV/ドローン関連語を検出"),
    (r"\bGaN|InP|GHz\b", "3A001", "高周波半導体/通信", "高周波・化合物半導体を示唆"),
]

SANCTIONED_DESTINATIONS = {
    "朝鮮民主主義人民共和国": "包括的禁止（デモ）",
    "DPRK": "包括的禁止（デモ）",
    "北朝鮮": "包括的禁止（デモ）",
    "ロシア": "追加的措置対象（デモ）",
    "イラン": "追加的措置対象（デモ）",
}

DEMO_EUL = {
    # 「参考：輸出管理適正化のための外国ユーザーリスト」風のダミー
    "Acme Research Institute (Xland)": "EUL相当（デモ）：要デューデリ",
    "Orbital Dynamics Lab": "EUL相当（デモ）：要デューデリ",
}

# =========================
# 共通ユーティリティ
# =========================
def extract_pdf_text(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    reader = PdfReader(uploaded_file)
    texts: List[str] = []
    for p in reader.pages:
        texts.append(p.extract_text() or "")
    return "\n".join(texts)

def toy_classify(text: str) -> List[Dict]:
    hits = []
    for pattern, clause, title, why in DEMO_MATRIX_RULES:
        if re.search(pattern, text, flags=re.IGNORECASE):
            hits.append({"clause": clause, "title": title, "why": why})
    return hits

def build_report_pdf(payload: Dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=16*mm, rightMargin=16*mm, topMargin=16*mm, bottomMargin=16*mm
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="jpSmall", fontName="Helvetica", fontSize=9, leading=12))

    story = []
    story.append(Paragraph("該非判定書・取引審査レポート（デモ）", styles["Title"]))
    story.append(Spacer(1, 6))

    head = [
        ["作成日時", datetime.now().strftime("%Y-%m-%d %H:%M")],
        ["Matrix版", MATRIX_VERSION],
        ["案件ID", payload.get("case_id", "-")],
    ]
    t = Table(head, colWidths=[35*mm, 120*mm])
    t.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
        ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    story.append(Paragraph("1. 物品情報", styles["Heading2"]))
    item_tbl = Table([
        ["品名", payload.get("item_name") or "-"],
        ["HSコード（任意）", payload.get("hs_code") or "-"],
        ["仕様（抜粋）", payload.get("spec_excerpt") or "-"]
    ], colWidths=[40*mm, 115*mm])
    item_tbl.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
    ]))
    story.append(item_tbl)
    story.append(Spacer(1, 8))

    story.append(Paragraph("2. 取引情報", styles["Heading2"]))
    deal_tbl = Table([
        ["買主", payload.get("buyer") or "-"],
        ["エンドユーザー", payload.get("end_user") or "-"],
        ["仕向地", payload.get("destination") or "-"],
        ["用途", payload.get("end_use") or "-"],
    ], colWidths=[40*mm, 115*mm])
    deal_tbl.setStyle(TableStyle([
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
    ]))
    story.append(deal_tbl)
    story.append(Spacer(1, 8))

    story.append(Paragraph("3. 該非判定（デモ）", styles["Heading2"]))
    hits = payload.get("hits", [])
    if hits:
        rows = [["候補条項", "区分名称", "根拠（キーワード）"]]
        for h in hits:
            rows.append([h["clause"], h["title"], h["why"]])
        t2 = Table(rows, colWidths=[28*mm, 40*mm, 87*mm])
        t2.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
            ('BOX',(0,0),(-1,-1),0.6,colors.black),
            ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
        ]))
        story.append(t2)
    else:
        story.append(Paragraph("該当候補は検出されませんでした。", styles["BodyText"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4. 取引審査（デモ）", styles["Heading2"]))
    scr = payload.get("screening", {})
    scr_rows = [
        ["項目", "結果"],
        ["仕向地", scr.get("destination_flag") or "ヒットなし"],
        ["買主", scr.get("buyer_flag") or "ヒットなし"],
        ["エンドユーザー", scr.get("end_user_flag") or "ヒットなし"],
    ]
    t3 = Table(scr_rows, colWidths=[40*mm, 115*mm])
    t3.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.whitesmoke),
        ('BOX',(0,0),(-1,-1),0.6,colors.black),
        ('INNERGRID',(0,0),(-1,-1),0.3,colors.grey),
    ]))
    story.append(t3)
    story.append(Spacer(1, 8))

    story.append(Paragraph("5. 総合判断（デモ）", styles["Heading2"]))
    story.append(Paragraph(payload.get("decision_text","—"), styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(
        "【重要】本レポートはデモです。実際の法令順守判断や許可申請は、最新の法令・告示・通達を確認のうえ社内責任者が行ってください。",
        styles["jpSmall"]
    ))

    doc.build(story)
    return buf.getvalue()

# =========================
# Streamlit UI（日本語＆モダン）
# =========================
st.set_page_config(page_title="輸出管理デモ（日本）", page_icon="🛡️", layout="wide")

# カスタムテーマ（CSS）
st.markdown("""
<style>
:root {
  --brand:#0ea5e9;      /* sky-500 */
  --brand-2:#38bdf8;    /* sky-400 */
  --ink:#0f172a;        /* slate-900 */
  --muted:#475569;      /* slate-600 */
  --card:#0b1220;       /* 深めの背景 */
  --card-ink:#e2e8f0;   /* slate-200 */
}
header, .stApp { background: linear-gradient(180deg,#0b1220 0%,#0b1220 60%, #0f172a 100%);}
h1,h2,h3,h4,h5,h6, label, p, span, div { color: var(--card-ink) !important; }
section[data-testid="stSidebar"] { background: #0a0f1a; }
.block-container { padding-top: 1.5rem; }
button[kind="primary"] {
  background: var(--brand) !important; border: 0 !important; color: #001018 !important;
  border-radius: 10px; font-weight: 700;
}
button[kind="secondary"] { border-radius: 10px; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] {
  background-color: #0e1626; border-radius: 10px 10px 0 0; padding: 10px 16px;
  color: #cbd5e1; border: 1px solid #1f2937;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(180deg, #09111f, #0f172a); color: white !important; border-bottom-color: transparent;
}
.stTextInput > div > div > input, textarea, select {
  background: #0e1626 !important; color: #e2e8f0 !important; border-radius: 10px !important;
  border: 1px solid #1f2937 !important;
}
[data-testid="stFileUploaderDropzone"] {
  background: #0e1626 !important; border: 1px dashed #334155;
}
hr { border: none; border-top: 1px solid #334155; }
.small { font-size: 12px; color: #94a3b8; }
.badge {
  display:inline-block;padding:4px 10px;border-radius:999px;background:#052e43;color:#7dd3fc;border:1px solid #0ea5e9;
}
.card {
  background:#0e1626;border:1px solid #1f2937;border-radius:14px;padding:14px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ 輸出管理SaaS デモ（日本）")
st.caption("※ デモUI：該非判定・取引先審査・履歴・問い合わせ（KSAテーマのモックを意識）")

# サイドバー（案件情報ショート）
with st.sidebar:
    st.subheader("案件情報")
    case_id = st.text_input("案件ID", value=f"DEMO-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    reviewer = st.text_input("審査担当者", value="田中 太郎")
    st.markdown('<span class="badge">Matrix版: {}</span>'.format(MATRIX_VERSION), unsafe_allow_html=True)
    st.markdown("---")
    st.write("このデモは、**UIモック**と**PDFレポート出力**を体験するためのサンプルです。")

# タブ（01〜04）
tab1, tab2, tab3, tab4 = st.tabs(["01 該非判定", "02 取引先審査", "03 過去履歴", "04 問合せ"])

# -----------------------
# 01 該非判定
# -----------------------
with tab1:
    st.subheader("01 該非判定")
    colA, colB = st.columns([1.2, 1])
    with colA:
        st.markdown("##### 仕様PDFのアップロード")
        pdf = st.file_uploader("製品カタログ・仕様PDFをアップロード", type=["pdf"])
        spec_text = ""
        if pdf:
            with st.spinner("PDFテキストを抽出中…"):
                spec_text = extract_pdf_text(pdf)
            st.success(f"抽出文字数: 約 {len(spec_text)}")
            with st.expander("抽出テキスト（先頭）", expanded=False):
                st.write((spec_text[:2000] + "…") if len(spec_text) > 2000 else (spec_text or "(テキスト抽出なし)"))
        st.markdown("##### 物品基本情報")
        c1, c2 = st.columns(2)
        with c1:
            item_name = st.text_input("品名", placeholder="例）XYZフライトコントローラ")
            hs_code = st.text_input("HSコード（任意）", placeholder="例）8526.91")
        with c2:
            key_params = st.text_input("主な性能（任意）", placeholder="例）AES対応 / 5軸 / 3.2GHz / GaN など")

        # モック判定
        if st.button("🔎 デモ判定を実行", type="primary"):
            text = "\n".join([spec_text, item_name or "", key_params or ""]).lower()
            hits = toy_classify(text)

            st.markdown("###### 判定候補（デモ）")
            if hits:
                for h in hits:
                    st.markdown(f"- **{h['clause']} / {h['title']}** — _{h['why']}_")
            else:
                st.info("デモルールでは該当候補が検出されませんでした。")

            # 保存用
            st.session_state["hits"] = hits
            st.session_state["item_name"] = item_name
            st.session_state["hs_code"] = hs_code
            st.session_state["spec_excerpt"] = (spec_text[:600] + "…") if spec_text and len(spec_text) > 600 else (spec_text or "-")

    with colB:
        st.markdown("##### ミニ仕様（サンプルUI）")
        st.markdown("""
- 入力：PDF / 物品名 / HS / 性能  
- 出力：候補条項・根拠 / Matrix版 / レポート生成  
- **レビュー承認**はタブ2の結果と総合判断後に実施
        """)

# -----------------------
# 02 取引先審査
# -----------------------
with tab2:
    st.subheader("02 取引先審査（キャッチオール）")
    c1, c2 = st.columns(2)
    with c1:
        destination = st.text_input("仕向地", placeholder="例）ロシア / ドイツ / ベトナム")
        buyer = st.text_input("買主", placeholder="例）Orbital Dynamics Lab")
        end_user = st.text_input("エンドユーザー", placeholder="例）Acme Research Institute (Xland)")
        end_use = st.text_area("用途（自由記載）", placeholder="例）自律飛行の学術研究 など", height=90)

        if st.button("🛡️ デモ審査を実行", type="primary"):
            dest_flag = SANCTIONED_DESTINATIONS.get((destination or "").strip(), None) if destination else None
            buyer_flag = DEMO_EUL.get((buyer or "").strip(), None) if buyer else None
            end_user_flag = DEMO_EUL.get((end_user or "").strip(), None) if end_user else None

            needs_license = bool(st.session_state.get("hits")) or bool(dest_flag) or bool(buyer_flag) or bool(end_user_flag)
            decision_text = (
                "【デモ】要ライセンス検討：仕向地/相手先のリスク、またはリスト該当候補あり。"
                if needs_license else
                "【デモ】現時点ではライセンス不要の可能性。ただし用途・最終需要者の適正性確認が必要。"
            )

            st.session_state["destination"] = destination
            st.session_state["buyer"] = buyer
            st.session_state["end_user"] = end_user
            st.session_state["end_use"] = end_use
            st.session_state["dest_flag"] = dest_flag
            st.session_state["buyer_flag"] = buyer_flag
            st.session_state["end_user_flag"] = end_user_flag
            st.session_state["decision_text"] = decision_text

            st.success("デモ審査を完了しました。下部でレポート生成ができます。")

    with c2:
        st.markdown("##### リスク結果（デモ）")
        if "destination" in st.session_state:
            st.write("- 仕向地：", st.session_state.get("dest_flag") or "ヒットなし")
            st.write("- 買主：", st.session_state.get("buyer_flag") or "ヒットなし")
            st.write("- エンドユーザー：", st.session_state.get("end_user_flag") or "ヒットなし")
            st.write("- Matrix版：", MATRIX_VERSION)
            if st.session_state.get("hits"):
                st.markdown("**該非判定候補（再掲）**")
                for h in st.session_state.get("hits", []):
                    st.write(f"- {h['clause']} / {h['title']} — _{h['why']}_")
            st.markdown("---")

        # PDFレポート生成
        if st.button("⬇️ デモレポート（判定書＋審査票）をPDFで出力", type="primary", disabled="decision_text" not in st.session_state):
            report_bytes = build_report_pdf({
                "case_id": case_id,
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
                "decision_text": st.session_state.get("decision_text", "—")
            })
            st.download_button(
                label="PDFを保存する",
                data=report_bytes,
                file_name=f"{case_id}_demo_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            # 履歴へ保存
            history = st.session_state.get("history", [])
            history.append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "case_id": case_id,
                "item": st.session_state.get("item_name") or "-",
                "dest": st.session_state.get("destination") or "-",
                "decision": st.session_state.get("decision_text") or "-",
            })
            st.session_state["history"] = history

# -----------------------
# 03 過去履歴
# -----------------------
with tab3:
    st.subheader("03 過去履歴")
    history = st.session_state.get("history", [])
    if not history:
        st.info("まだ履歴はありません。タブ1→タブ2の順で実行すると履歴に追加されます。")
    else:
        for row in reversed(history):
            st.markdown(f"""
<div class="card">
  <b>{row['time']}</b>　|　案件ID：<code>{row['case_id']}</code><br/>
  物品：{row['item']}　/　仕向地：{row['dest']}<br/>
  判断：{row['decision']}
</div>
""", unsafe_allow_html=True)
            st.markdown("")

# -----------------------
# 04 問合せ
# -----------------------
with tab4:
    st.subheader("04 問合せ")
    st.write("導入・PoC・追加機能に関するご相談はこちらから。")
    q1, q2 = st.columns(2)
    with q1:
        contact_name = st.text_input("お名前", "")
        contact_mail = st.text_input("メールアドレス", "")
    with q2:
        company = st.text_input("会社名（任意）", "")
        tel = st.text_input("電話番号（任意）", "")
    msg = st.text_area("ご相談内容", height=120)
    if st.button("📩 送信（ダミー）", type="primary"):
        st.success("送信しました（ダミー）。担当より追ってご連絡します。")
        st.markdown('<span class="small">※実際の送信は未接続です。バックエンド連携で有効化可能。</span>', unsafe_allow_html=True)

st.markdown("---")
st.caption("© デモUI。実サービスでは、法令データのスナップショット管理、根拠条文の行引用、審査フローの権限設計、監査証跡、NACCS連携などを実装します。")
