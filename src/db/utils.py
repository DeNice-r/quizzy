from db.engine import db_session
from db.models.Attempt import Attempt
from db.models.QuizQuestion import QuizQuestion
from db.models.QuestionAnswer import QuestionAnswer
from db.models.AttemptAnswer import AttemptAnswer


def update_mark(attempt_id):
    with db_session.begin() as s:
        attempt = s.get(Attempt, attempt_id)
        user_id = attempt.user_id
        quiz_id = attempt.quiz_id

        questions = s.query(QuizQuestion).filter_by(quiz_id=quiz_id).all()

        attempt_mark = 0
        for que in questions:
            right_answers = [x[0] for x in s.query(QuestionAnswer.id).filter_by(question_id=que.id, is_right=True).all()]
            if len(right_answers) == 0:
                continue
            weight = 1 / len(right_answers)
            attempt_answer = s.query(AttemptAnswer).filter_by(attempt_id=attempt.id,
                                                              question_id=que.id).one_or_none()
            if attempt_answer is None:
                continue
            answered_correctly = list(filter(lambda x: x in right_answers, attempt_answer.answer_ids))

            temp = len(answered_correctly) - (len(attempt_answer.answer_ids) - len(answered_correctly))

            attempt_answer.mark = round(temp * weight if temp > 0 else 0, 2)
            attempt_mark += attempt_answer.mark
            s.flush()
        attempt.mark = round(attempt_mark / len(questions) * 100, 2)
        return attempt.mark

def update_quiz_marks(quiz_id):
    pass
