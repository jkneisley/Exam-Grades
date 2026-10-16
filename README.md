# Exam-Grades
Suggests outcome-level grades (S/G/L/N/X) from question-level exam scores and
produces an LMS-ready file of points per outcome.

    python exam_grades.py scores.csv outcomes.csv [--overrides overrides.csv] \
        [--report report.csv] [--lms lms.csv]

- `scores.csv`: `student,outcome,question,level,score` (level D/C/B; score 10, 7.5, 5, 1, 0 or S, G, L, N, X)
- `outcomes.csv`: `outcome,points`
- `overrides.csv` (optional): `student,outcome,category`

Outcome grades: S=100%, G=75%, L=50%, N=10%, X=0%. Uniform scores map directly.
Otherwise a weighted average (D=3, C=2, B=1) picks the category, capped at G if
a D-level question scored L or lower. Mixed levels, wide spreads and L results
are flagged `review` in the report so you can set overrides.
