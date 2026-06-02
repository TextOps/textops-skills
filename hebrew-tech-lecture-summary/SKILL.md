---
name: hebrew-tech-lecture-summary
description: Summarize any content — lectures, meetings, articles, transcriptions, or any text — into structured Hebrew Markdown. Use when the user asks to summarize anything  סכם לי, תסכם, סיכום, summarize, meeting notes, or any request to condense content. Output is ALWAYS in Hebrew regardless of input language.
license: MIT
compatibility: "Designed for Claude Code. No external dependencies required."
metadata:
  version: "1.1.3"
  author: "TextOps"
  tags: "summary, lecture, hebrew, meeting-notes, transcription, article"
  language: "he"
---

# סיכום טקסטים ותכנים בעברית

יוצר סיכום מובנה ב-Markdown מכל תוכן — הרצאה, פגישה, מאמר, תמלול, או כל טקסט אחר.

**הפלט תמיד בעברית — גם אם החומר המקורי באנגלית.**

## תהליך העבודה

1. קבל את התוכן לסיכום — אחת מהאפשרויות:
   - טקסט שהמשתמש הדביק ישירות
   - קובץ תמלול (בד"כ `output/transcription_plain.txt`)
   - קישור, מאמר, או כל חומר אחר שסופק
2. נתח את התוכן: זהה נושאים, דוברים, שאלות, וציטוטים חשובים
3. כתוב את הסיכום **בעברית** לפי המבנה שב-[template.md](template.md)
4. אם מדובר בקובץ — שמור לפי הכללים ב-**"שמירת קובץ הסיכום"** למטה
5. (אופציונלי) המר ל-Word — ראה שלב "ייצוא ל-Word" למטה

## אסור בהחלט

**אל תוסיף שום הערה עריכתית שלא מגיעה מהתמלול.**

דוגמאות להערות אסורות:
- "זה הסיכום למי שרצה את התוכן"
- "מי שלא הגיע יכול לשמוע את ההקלטה"
- "הסיכום נכתב על בסיס התמלול בלבד"
- "לפרטים נוספים ניתן לפנות למרצה"
- כל משפט שאינו תוכן ישיר מהתמלול

**עקוב אחר [template.md](template.md) בלבד.** לא מוסיפים, לא מסבירים, לא מגיבים — פשוט כותבים את הסיכום.

---

## שמירת קובץ הסיכום

### בחירת שם קובץ

לפני השמירה, בדוק אם `output/lecture_summary.md` כבר קיים.

**אם הקובץ לא קיים** — שמור כ-`output/lecture_summary.md`.

**אם הקובץ כבר קיים** — צור שם מתאים יותר לפי הנוסחה:

```
output/summary_<נושא-בקצרה>.md
```

כללים לבניית השם:
- גזור את הנושא מהכותרת הראשית של הסיכום (`# סיכום: [נושא]`)
- השתמש ב-2–4 מילים מהנושא (באנגלית אם הנושא טכני, בעברית מתועתקת אם לא)
- החלף רווחים ב-`_`, הסר תווים מיוחדים
- דוגמאות: `summary_ci_cd_pipeline.md`, `summary_product_review.md`, `summary_agile_sprint.md`

**לאחר שמירה בשם חלופי**, הודע למשתמש:
> "`output/lecture_summary.md` כבר קיים — הסיכום נשמר בשם: `output/summary_<שם>.md`"

### אותו כלל לקובץ Word

אם בעת ייצוא ל-`.docx` קיים כבר קובץ באותו שם — השתמש באותה לוגיקת שם חלופי והודע למשתמש.

---

## כללי כתיבה

### שפה ומונחים
- הסיכום **תמיד בעברית** — ללא קשר לשפת החומר המקורי (עברית, אנגלית, או כל שפה אחרת)
- מושגי tech ותכנות נשארים **באנגלית**
- דוגמאות: production, deploy, PR, build, MCP, workspace, branch, commit, Docker image, rollout, pipeline, CI/CD, code review, unit test, integration test, API, endpoint, repository
- שמות כלים ומוצרים באנגלית: Cursor, Jenkins, Argo, Splunk, Jira, GitHub

### הנחיות שלב-אחרי-שלב
כשיש תהליך או רצף פעולות, השתמש בחיצים:

```
git clone --> פתיחת workspace ב-Cursor --> הרצת build --> deploy ל-QA
```

### מבנה הסיכום
הסיכום חייב להיות **כרונולוגי** -- לפי הסדר שבו הדברים נאמרו בהרצאה. ראה [template.md](template.md) למבנה המלא.

### עקרונות תוכן
- **ערך מלא** -- מי שפספס את ההרצאה צריך לקבל את כל התוכן המהותי
- **קונקרטי** -- דוגמאות ספציפיות, לא הכללות
- **שאלות מהקהל** -- כל שאלה ותשובה, זה חלק חשוב מהערך
- **ציטוטים** -- משפטים חזקים ומדויקים שנאמרו בהרצאה
- אל תמציא תוכן שלא נאמר בהרצאה
- אם חלק מהתמלול לא ברור -- דלג עליו, אל תנחש

---

## ייצוא ל-Word (אופציונלי)

לאחר שמירת הסיכום ב-Markdown, אפשר להמיר לקובץ Word:

```bash
python "<skill_dir>/scripts/md_to_word.py" "<path_to_summary.md>"
```

הפקודה שומרת את ה-`.docx` **ליד קובץ ה-Markdown**, באותה תיקייה.

**תלויות**: הסקריפט דורש `python-docx` (ראה `requirements.txt`).

קרא את הפלט ופעל לפיו:

| פלט | פעולה |
|---|---|
| `[DONE] /path/to/file.docx` | דווח למשתמש על הקובץ שנוצר |
| `[MISSING_DEP] python-docx is not installed.` | הצג למשתמש את ההודעה הבאה ו**המשך** בכל זאת (אל תעצור) |
| `[ERROR] ...` | הצג את השגיאה למשתמש |

**כשחסרה הספרייה**, אמור למשתמש:
> "כדי לייצא ל-Word, צריך להתקין python-docx:
> ```
> pip install python-docx
> ```
> הסיכום נשמר ב-Markdown ותקין — ניתן לייצא ל-Word בכל עת."

ואז המשך. **אל תחסום** את תהליך הסיכום בגלל העדר הספרייה.

---

### חשוב: אין הערות עריכה
הסיכום הוא **תוכן בלבד**. אין להוסיף:
- הקדמות או מסקנות שלך
- הפניות להקלטה, למרצה, או למקורות חיצוניים
- הסברים על איך הסיכום נכתב
- כל דבר שאינו חלק מהמבנה ב-[template.md](template.md)
