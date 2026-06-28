# Family Hub - גרסת התחלה

מערכת Flask מקומית לניהול שירותי משפחה.

## מה יש בגרסה הזו

- התחברות משתמשים
- משתמש מנהל ראשון: `ronen`
- סיסמה ראשונית: `123456`
- החלפת סיסמה חובה בכניסה ראשונה
- ניהול משתמשים
- השבתת משתמשים
- דף בית בעברית
- שלד מוכן למודולים: תרופות, תורים, מסמכים

## הרצה ב-Windows

פתח CMD או PowerShell בתוך התיקייה והריץ:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

פתח בדפדפן:

```text
http://127.0.0.1:5000
```

## הרצה ב-Linux / Mac

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## פרטי כניסה ראשוניים

```text
Username: ronen
Password: 123456
```

בכניסה הראשונה תידרש להחליף סיסמה.

## הערה חשובה לפני פרסום לאינטרנט

לפני העלאה לשרת חובה לשנות את `SECRET_KEY` בקובץ `app.py`.

## הגרסה הבאה

v0.2 תכלול מודול תרופות אמיתי:

- הוספת תרופה
- עריכת תרופה
- סימון שנלקחה
- איפוס יומי
- שיוך תרופות למשתמש
