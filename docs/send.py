"""
ONTO × UZ — Email Sender v3 (ALL EMAILS ENHANCED)

  python send.py test  — barcha emaillar Gmail ga
  python send.py 1     — Shermatov + Hayot Ventures
  python send.py 2     — Alliance
  python send.py 3     — Council
  python send.py 4     — AI Center
"""

import requests, time, sys

RESEND_API_KEY = "re_H3tGcNpT_8s71moaP4GCAnocehFAX5546"
FROM_EMAIL = "ONTO Standards Council <council@ontostandard.org>"
REPLY_TO = "dexterrion.com@gmail.com"

HEADER = '''<div style="max-width:600px;margin:0 auto;font-family:'Helvetica Neue',Arial,sans-serif;color:#1a1a1a;line-height:1.7;">
<table width="100%" cellpadding="0" cellspacing="0" style="border-bottom:3px solid #15803d;margin-bottom:24px;padding-bottom:14px;">
<tr><td><table cellpadding="0" cellspacing="0"><tr>
<td style="width:40px;height:40px;background:#0a0a0a;border-radius:50%;text-align:center;vertical-align:middle;border:2px solid #22c55e;"><span style="color:#fff;font-weight:900;font-size:18px;line-height:40px;font-family:monospace;">1</span></td>
<td style="padding-left:12px;"><div style="font-size:14px;font-weight:800;letter-spacing:2px;color:#0a0a0a;font-family:monospace;">ONTO STANDARDS COUNCIL</div><div style="font-size:10px;color:#888;letter-spacing:1px;">ontostandard.org</div></td>
</tr></table></td></tr></table>'''

SIGNATURE = '''<table width="100%" cellpadding="0" cellspacing="0" style="margin-top:32px;padding-top:16px;border-top:2px solid #f0f0f0;">
<tr><td>
<div style="font-size:14px;font-weight:700;color:#0a0a0a;">Hakim Tohirovich</div>
<div style="font-size:12px;color:#666;">Founder · ONTO Standards Council · IT Park rezidenti</div>
<div style="font-size:11px;color:#888;margin-top:2px;">20 yil tadqiqot · 22+ model sinangan · 12 hisobot chop etilgan</div>
<div style="margin-top:8px;">
<a href="tel:+998903920139" style="font-size:12px;color:#15803d;text-decoration:none;font-weight:600;">+998 90 392 01 39</a>
<span style="color:#ddd;"> · </span>
<span style="font-size:12px;color:#555;">Telegram:</span> <a href="https://t.me/ontokhakim" style="font-size:12px;color:#15803d;text-decoration:none;font-weight:600;">@ontokhakim</a>
<span style="color:#ddd;"> · </span>
<a href="mailto:council@ontostandard.org" style="font-size:12px;color:#15803d;text-decoration:none;font-weight:600;">council@ontostandard.org</a>
</div>
</td></tr></table></div>'''

def cta(url, text):
    return f'<div style="text-align:center;margin-top:24px;"><a href="{url}" style="font-family:monospace;font-size:14px;font-weight:800;color:#fff;background:#15803d;padding:14px 36px;border-radius:8px;text-decoration:none;display:inline-block;letter-spacing:0.5px;">{text}</a></div>'

def links_block():
    return '''<div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin-top:16px;">
<a href="https://ontostandard.org/agent" style="font-family:monospace;font-size:11px;font-weight:700;color:#15803d;background:rgba(34,197,94,0.06);border:1.5px solid rgba(34,197,94,0.2);border-radius:6px;padding:6px 14px;text-decoration:none;">Live Demo</a>
<a href="https://ontostandard.org/reports" style="font-family:monospace;font-size:11px;font-weight:700;color:#15803d;background:rgba(34,197,94,0.06);border:1.5px solid rgba(34,197,94,0.2);border-radius:6px;padding:6px 14px;text-decoration:none;">12 hisobot</a>
<a href="https://ontostandard.org/gov" style="font-family:monospace;font-size:11px;font-weight:700;color:#15803d;background:rgba(34,197,94,0.06);border:1.5px solid rgba(34,197,94,0.2);border-radius:6px;padding:6px 14px;text-decoration:none;">Regulyator</a>
</div>'''

def traction_block():
    return '''<div style="margin:20px 0;padding:14px 18px;background:#0a0a0a;border-radius:10px;">
<div style="font-family:monospace;font-size:10px;font-weight:800;letter-spacing:1.5px;color:rgba(255,255,255,0.5);margin-bottom:8px;">TRAKTSIYA</div>
<div style="font-size:13px;color:rgba(255,255,255,0.9);line-height:1.7;">
<strong style="color:#22c55e;">xAI (Grok)</strong> — allaqachon tizimda. 108 so\'rov tekshirilgan. Baho: <strong style="color:#22c55e;">A</strong>.<br>
<strong style="color:#22c55e;">22+ model</strong> sinangan. <strong style="color:#22c55e;">12 hisobot</strong> chop etilgan. Regulyator — <strong style="color:#22c55e;">100% tayyor. 1-3 kunda joriy etiladi.</strong>
</div></div>'''

def urgency_block():
    return '''<div style="margin-top:24px;padding:14px 18px;border:2px solid rgba(220,38,38,0.15);border-radius:8px;text-align:center;">
<div style="font-size:14px;font-weight:800;color:#0a0a0a;">Bu taklif 9 ta davlatga yuborilgan. Birinchi joriy etgan — <span style="color:#15803d;">standartni belgilaydi.</span></div>
<div style="font-size:11px;color:#888;margin-top:4px;">EU · Turkiya · BAA · Singapur · J.Koreya · Saudiya · Yaponiya · Germaniya · O\'zbekiston</div>
<div style="font-size:12px;font-weight:800;color:#dc2626;margin-top:6px;">Muddati cheklangan. Javob berilmasa — eksklyuziv keyingi davlatga o\'tadi.</div>
</div>'''

def money_block():
    return '''<table width="100%" cellpadding="0" cellspacing="0" style="margin:20px 0;border:2px solid #15803d;border-radius:10px;overflow:hidden;">
<tr>
<td style="padding:14px 16px;width:50%;vertical-align:top;">
<div style="font-size:12px;font-weight:800;color:#0a0a0a;margin-bottom:6px;">XARAJAT</div>
<div style="font-size:13px;color:#333;line-height:1.7;">ONTO (UZ eksklyuziv): <strong style="color:#15803d;font-family:monospace;">dan $10K/oy</strong><br>3 oy pilot: <strong style="color:#dc2626;">$0 bepul</strong></div>
</td>
<td style="padding:14px 16px;width:50%;vertical-align:top;border-left:2px solid rgba(34,197,94,0.2);">
<div style="font-size:12px;font-weight:800;color:#0a0a0a;margin-bottom:6px;">DAROMAD (byudjetga)</div>
<div style="font-size:13px;color:#333;line-height:1.7;">Provayder sertifikatsiya: <strong style="color:#15803d;font-family:monospace;">min $250K/yil</strong><br>5 provayder: <strong style="color:#15803d;">$1.25M/yil</strong></div>
</td>
</tr></table>'''

def wrap(body):
    return HEADER + body + SIGNATURE

ALL_EMAILS = {
    1: [
        {
            "to": "info@mitc.uz",
            "subject": "SI sifat nazorati instituti — tayyor, sinovdan o'tgan, joriy etishga tayyor",
            "tag": "shermatov-v3",
            "html": wrap(f'''
<p style="font-size:15px;">Sherzod Xotamovich, assalomu alaykum.</p>
<p style="font-size:14px;">Siz Buyruq 3787 ni tasdiqlangiz — SI etika qoidalari. PQ-358 bo\'yicha Alyans, Markaz, Kengash yaratdingiz. <strong>Bitta narsa yetishmayapti — muvofiqlikni tekshirish vositasi.</strong></p>
<p style="font-size:14px;">ONTO Standards Council bu vositani qurib bo\'ldi.</p>
<div style="margin:20px 0;padding:16px;border-left:4px solid #15803d;background:#f0fdf4;border-radius:0 8px 8px 0;">
<div style="font-size:14px;color:#333;line-height:1.7;">
<strong>ONTO — dasturiy ta\'minot.</strong> SI provayderga 1 qator kod bilan ulanadi. SI tuzilishiga hech qanday o\'zgartirish kiritilmaydi. Har bir javob avtomatik tekshiriladi va A–F baholanadi.
</div></div>
<p style="font-size:14px;font-weight:700;">Qanday ishlaydi:</p>
<p style="font-size:13px;color:#333;">Provayder ulanadi (1 qator kod) → ONTO tekshiradi (har bir javob) → Operator dashboardda kuzatadi (kim ulangan, kim yo\'q) → Regulyator nazorat qiladi.</p>
{traction_block()}
{money_block()}
<p style="font-size:13px;color:#555;">Buyruq 3787 ning 8 ta tamoyili, PQ-358 standartlari, $1.5B eksport maqsadi — barchasi hal qilinadi.</p>
{urgency_block()}
{cta("https://onto.uz/shermatov", "Batafsil — onto.uz/shermatov →")}
{links_block()}
''')
        },
        {
            "to": "info@hayotbank.uz",
            "subject": "ONTO — SI sifat infrastrukturasi. 100% tayyor. Eksklyuziv muddati cheklangan",
            "tag": "hayot-v3",
            "html": wrap(f'''
<p>Assalomu alaykum.</p>
<p style="font-size:14px;">Hayot Ventures SI startaplariga investitsiya qiladi. Savol: <strong>portfel kompaniyalarining SI sifatini kim o\'lchaydi?</strong> Javob: hozircha hech kim.</p>
<p style="font-size:14px;">ONTO Standards Council bu vositani qurib bo\'ldi.</p>
{traction_block()}
<div style="margin:20px 0;padding:14px 18px;border:2px solid #e5e7eb;border-radius:10px;">
<table width="100%" cellpadding="0" cellspacing="8"><tr>
<td style="width:50%;background:#f0fdf4;border:2px solid #86efac;border-radius:8px;padding:12px;vertical-align:top;">
<div style="font-size:11px;font-weight:800;color:#15803d;letter-spacing:1px;">MAHSULOT 1: REGULYATOR</div>
<div style="font-size:14px;font-weight:800;margin-top:3px;">SI sifat nazorati</div>
<div style="font-size:12px;color:#555;margin-top:4px;">Davlatlar uchun. <strong>100% tayyor.</strong> 1-3 kunda joriy etiladi.</div>
<div style="font-size:11px;color:#888;margin-top:4px;">Daromad: davlatlar $10K+/oy, provayderlar $250K+/yil</div></td>
<td style="width:50%;background:#f5f3ff;border:2px solid #c4b5fd;border-radius:8px;padding:12px;vertical-align:top;">
<div style="font-size:11px;font-weight:800;color:#7c3aed;letter-spacing:1px;">MAHSULOT 2: HUMAN AI</div>
<div style="font-size:14px;font-weight:800;margin-top:3px;">Olim SI</div>
<div style="font-size:12px;color:#555;margin-top:4px;">Provayderlar uchun. <strong>85% tayyor.</strong></div>
<div style="font-size:11px;color:#888;margin-top:4px;">Manba keltiradi. Bilmasligini tan oladi. Soxta ma\'lumot yaratmaydi.</div></td>
</tr></table></div>
<div style="margin:16px 0;padding:14px 18px;background:#fffbeb;border:2px solid #fde68a;border-radius:10px;">
<div style="font-size:13px;font-weight:700;color:#0a0a0a;">Hayot Bank uchun alohida:</div>
<div style="font-size:12px;color:#555;margin-top:4px;">Kredit skoringi sifatini A-F baholash. Korrelyatsiya vs sabab-oqibat farqlanadi. Birinchi pilot — bepul.</div></div>
<p style="font-size:13px;color:#555;"><strong>Nima uchun 0 raqobatchi:</strong> 20 yil tadqiqot. 169 fayl. Kriptografik dalil zanjiri. Nusxa ko\'chirib bo\'lmaydi.</p>
{urgency_block()}
<p style="font-size:14px;font-weight:700;text-align:center;margin-top:20px;">15 daqiqalik qo\'ng\'iroq. Due diligence uchun barcha ma\'lumotlar tayyor.</p>
{cta("https://onto.uz/hayot", "Batafsil — onto.uz/hayot →")}
{links_block()}
''')
        },
    ],
    2: [
        {
            "to": "info@mitc.uz",
            "subject": "SI Alyansiga — tayyor SI sifat vositasi. Sinovdan o'tgan. Joriy etishga tayyor",
            "tag": "alliance-v3",
            "html": wrap(f'''
<p>Hurmatli SI Alyansining a\'zolari,</p>
<p style="font-size:14px;">PP-358 bo\'yicha Alyans yaratildi. A\'zolar uchun bitta asosiy vosita yetishmayapti: <strong>SI sifatini o\'lchash va sertifikatsiyalash tizimi.</strong></p>
<p style="font-size:14px;">ONTO Standards Council aynan shuni qurib bo\'ldi.</p>
<div style="margin:16px 0;padding:14px 18px;border-left:4px solid #15803d;background:#f0fdf4;border-radius:0 8px 8px 0;font-size:13px;color:#333;line-height:1.7;">
• Provayder 1 qator kod bilan ulanadi — SI tuzilishiga o\'zgartirish yo\'q<br>
• Har bir javob avtomatik tekshiriladi va A–F baholanadi<br>
• Dashboardda ko\'rinadi — kim ulangan, kim yo\'q<br>
• Buyruq 3787 ning barcha tamoyillari qamrab olingan</div>
{traction_block()}
<p style="font-size:14px;">Alyans a\'zolari uchun <strong>30 kunlik bepul pilot</strong>. Birinchi hisobot 2 hafta ichida.</p>
{urgency_block()}
{cta("https://ontostandard.org/gov", "Regulyator sahifasi →")}
{links_block()}
''')
        },
    ],
    3: [
        {
            "to": "info@mitc.uz",
            "subject": "Maslahat kengashi — Buyruq 3787 muvofiqligini tekshirish vositasi tayyor",
            "tag": "council-v3",
            "html": wrap(f'''
<p>Hurmatli Maslahat kengashi a\'zolari,</p>
<p style="font-size:14px;">Buyruq 3787 (14.03.2026) SI etika qoidalarini tasdiqladi. 8 tamoyil belgilandi.</p>
<p style="font-size:14px;font-weight:700;">Savol: bu tamoyillar bajarilayotganini kim tekshiradi?</p>
<p style="font-size:14px;">ONTO Standards Council — aynan shu maqsadda yaratilgan vosita. Har bir SI javob R1-R7 qoidalari bo\'yicha avtomatik tekshiriladi:</p>
<div style="margin:16px 0;padding:14px 18px;border:2px solid #e5e7eb;border-radius:10px;font-family:monospace;font-size:13px;color:#555;line-height:2;">
<strong style="color:#15803d;">R1</strong> Raqamlar · <strong style="color:#15803d;">R2</strong> Noaniqlik · <strong style="color:#15803d;">R3</strong> Qarama-qarshi · <strong style="color:#15803d;">R4</strong> Manbalar<br>
<strong style="color:#15803d;">R5</strong> Dalil darajasi · <strong style="color:#15803d;">R6</strong> Tekshiruvchanlik · <strong style="color:#15803d;">R7</strong> Soxta yo\'q</div>
{traction_block()}
<p style="font-size:14px;">Maslahat kengashiga SI sifat standarti bo\'yicha ekspert sifatida taklif qilaman. Prezentatsiya, live demo va to\'liq texnik hujjatlar — tayyor.</p>
{urgency_block()}
{cta("https://ontostandard.org/agent", "Live Demo — 30 soniya →")}
{links_block()}
''')
        },
    ],
    4: [
        {
            "to": "info@mitc.uz",
            "subject": "SI Markaz uchun — tayyor metodologiya, baholash tizimi, regulyator dashboardi",
            "tag": "ai-center-v3",
            "html": wrap(f'''
<p>Hurmatli hamkasblar,</p>
<p style="font-size:14px;">VM-425 bo\'yicha "Sun\'iy intellekt va raqamli iqtisodiyotni rivojlantirish markazi" tashkil etildi. Markazning asosiy vazifasi — <em>metodologik asos shakllantirish.</em></p>
<p style="font-size:14px;"><strong>ONTO Standards Council aynan shuni qurib bo\'ldi:</strong></p>
<div style="margin:16px 0;padding:14px 18px;border-left:4px solid #15803d;background:#f0fdf4;border-radius:0 8px 8px 0;font-size:13px;color:#333;line-height:1.7;">
• Tayyor metodologiya: R1-R7 intizom qoidalari<br>
• Tayyor baholash tizimi: har bir SI javob A–F baholanadi<br>
• Tayyor regulyator dashboardi: kim ulangan, kim yo\'q, real-time<br>
• Buyruq 3787 muvofiqligini avtomatik tekshiradi</div>
{traction_block()}
<p style="font-size:14px;">Davlat organlaridagi SI tizimlariga 1 qator kod bilan ulanadi. <strong>1-3 kunda joriy etiladi.</strong></p>
<p style="font-size:14px;">Markaz uchun <strong>3 oylik bepul pilot</strong>. Birinchi hisobot 30 kun ichida.</p>
{urgency_block()}
{cta("https://ontostandard.org/gov", "Vazirlik sahifasi →")}
{links_block()}
''')
        },
    ],
}

def send_email(e):
    r = requests.post("https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json={"from": FROM_EMAIL, "to": [e["to"]], "reply_to": REPLY_TO,
              "subject": e["subject"], "html": e["html"],
              "tags": [{"name": "campaign", "value": "uz-v3"}]})
    return r.status_code, r.json()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("ONTO x UZ — Email Sender v3")
        print("  python send.py test  — barcha emaillar Gmail ga")
        print("  python send.py 1     — Shermatov + Hayot")
        print("  python send.py 2     — Alliance")
        print("  python send.py 3     — Council")
        print("  python send.py 4     — AI Center")
        sys.exit(0)

    arg = sys.argv[1]
    if arg == "test":
        print("=" * 60)
        print("TEST — barcha emaillar dexterrion.com@gmail.com ga")
        print("=" * 60)
        for day in sorted(ALL_EMAILS.keys()):
            for e in ALL_EMAILS[day]:
                test_e = {**e, "to": "dexterrion.com@gmail.com"}
                print(f"  [{e['tag']}] {e['subject'][:60]}...")
                s, r = send_email(test_e)
                print(f"    {'✅' if s == 200 else '❌'} {s}")
                time.sleep(2)
        print("\nTayyor. Gmail tekshiring.")
        sys.exit(0)

    day = int(arg)
    if day not in ALL_EMAILS:
        print(f"Xato: {day}. 1-4 kiriting.")
        sys.exit(1)

    emails = ALL_EMAILS[day]
    print("=" * 60)
    print(f"KUN {day}")
    print("=" * 60)
    for i, e in enumerate(emails, 1):
        print(f"  {i}. [{e['tag']}] -> {e['to']}")
        print(f"     {e['subject']}")
    print()
    confirm = input("Yuborilsinmi? (da/yo'q): ").strip().lower()
    if confirm not in ("da", "yes", "y"):
        print("Bekor qilindi.")
        sys.exit(0)
    print()
    for i, e in enumerate(emails, 1):
        print(f"[{i}/{len(emails)}] {e['tag']} -> {e['to']}...")
        s, r = send_email(e)
        print(f"  {'✅' if s == 200 else '❌'} {s}: {r.get('id','')}")
        if i < len(emails): time.sleep(3)
    print("\nTayyor.")
