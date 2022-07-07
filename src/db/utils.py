from db.engine import db_session
from db.models.Attempt import Attempt
from db.models.QuizQuestion import QuizQuestion
from db.models.QuestionAnswer import QuestionAnswer
from db.models.AttemptAnswer import AttemptAnswer
from sqlalchemy import text

stmt = \
	"""DROP FUNCTION IF EXISTS update_mark_for_attempt_answer CASCADE;
DROP FUNCTION IF EXISTS update_mark_for_attempt CASCADE;
DROP FUNCTION IF EXISTS get_mark_for_attempt CASCADE;
DROP FUNCTION IF EXISTS update_mark_for_related_attempts CASCADE;
DROP FUNCTION IF EXISTS get_mark_for_attempt_answer CASCADE;



CREATE FUNCTION get_mark_for_attempt(var_attempt_id bigint) RETURNS numeric AS $$
DECLARE
	var_quiz_id integer;
	var_question_count integer;
	var_mark numeric;
BEGIN
--  Get quiz id
	SELECT attempt.quiz_id INTO var_quiz_id
	FROM attempt
	WHERE attempt.id = var_attempt_id;

--  Get question count
	SELECT COUNT(*) INTO var_question_count
	FROM quiz_question qq
	WHERE qq.quiz_id = var_quiz_id;

--  Calculate the mark
	SELECT 100 * ROUND(SUM(aa.mark) / var_question_count, 2) INTO var_mark
	FROM attempt_answer aa
	WHERE aa.attempt_id = var_attempt_id;

	RETURN var_mark;
END $$ LANGUAGE 'plpgsql';



CREATE FUNCTION get_mark_for_attempt_answer(var_attempt_answer_id bigint) RETURNS numeric AS $$
DECLARE
	var_quiz_id integer;
	var_question_id bigint;
	var_question_count integer;
	var_weight numeric;
	var_right_answer_count integer;
	var_raw_mark numeric;
	var_mark numeric;
BEGIN
--  Get question id
	SELECT aa.question_id INTO var_question_id FROM attempt_answer aa WHERE aa.id = var_attempt_answer_id;

--  Calculate answer weight
	SELECT 1. / COUNT(*) INTO var_weight
	FROM quiz_question
	INNER JOIN question_answer qa ON question_id = quiz_question.id
	WHERE question_id = var_question_id AND qa.is_right = true
	GROUP BY quiz_question.id;

--  Get answers for a question
	DROP TABLE IF EXISTS tmp_answers;
	CREATE TEMP TABLE tmp_answers AS
	SELECT qa.is_right
	FROM question_answer qa
	INNER JOIN attempt_answer aa ON qa.id = ANY(aa.answer_ids)
	WHERE aa.id = var_attempt_answer_id;
	
--  Count right answers
	SELECT COUNT(*) INTO var_right_answer_count
	FROM tmp_answers
	WHERE is_right = true;
	
--  Calculate raw mark (can be nagative)
	SELECT ROUND((var_right_answer_count * var_weight) - ((COUNT(*) - var_right_answer_count) * var_weight), 2) INTO var_raw_mark
	FROM tmp_answers;
	
--  If mark < 0, mark = 0
	SELECT COALESCE(NULLIF (ABS(var_raw_mark), -var_raw_mark), 0) INTO var_mark;

	RETURN var_mark;
END $$ LANGUAGE 'plpgsql';




CREATE FUNCTION update_mark_for_attempt() RETURNS TRIGGER AS $$
DECLARE
	var_mark numeric;
BEGIN
--  Get the mark
	SELECT get_mark_for_attempt(OLD.attempt_id) INTO var_mark;
	
--  Update mark of given attempt
	UPDATE attempt
	SET mark = var_mark
	WHERE attempt.id = OLD.attempt_id;
	
	RETURN OLD;
END $$ LANGUAGE 'plpgsql';



CREATE FUNCTION update_mark_for_attempt_answer() RETURNS TRIGGER AS $$
DECLARE
	var_mark numeric;
	var_row RECORD;
BEGIN
	IF NEW.mark = OLD.mark THEN
	--  Recalculate mark for attempt_answer
		SELECT get_mark_for_attempt_answer(NEW.id) INTO var_mark;

	--  Update attempt answers' mark
		IF NEW.mark != var_mark THEN
			UPDATE attempt_answer as aa
			SET mark = var_mark
			WHERE id = NEW.id;
		END IF;
	END IF;
--  Recalculate mark for attempt
	SELECT get_mark_for_attempt(NEW.attempt_id) INTO var_mark;
	
	DROP TABLE IF EXISTS temptemp;
	CREATE TABLE temptemp AS SELECT * FROM get_mark_for_attempt(NEW.attempt_id);
	
--  Update attempts' mark
	UPDATE attempt
	SET mark = var_mark
	WHERE NEW.attempt_id = attempt.id;
	RETURN NEW;
END $$ LANGUAGE 'plpgsql';


-- TODO: never executed
CREATE FUNCTION update_mark_for_related_attempts() RETURNS TRIGGER AS $$
DECLARE
	var_quiz_id int;
	var_weight numeric;
	var_right_answer_count integer;
	var_mark numeric;
	temp_row RECORD;
	
	var_question_id bigint;
BEGIN
	IF NEW IS NULL THEN
		var_question_id = OLD.question_id ;
	ELSE
		var_question_id = NEW.question_id;
	END IF;

	FOR temp_row IN
        SELECT * FROM attempt_answer aa
		WHERE aa.question_id = var_question_id
    LOOP
		SELECT get_mark_for_attempt_answer(temp_row.id) INTO var_mark;
		UPDATE attempt_answer aa
		SET mark = var_mark
		WHERE aa.id = temp_row.id;
    END LOOP;
	RETURN NEW;
END $$ LANGUAGE 'plpgsql';



CREATE TRIGGER attempt_answer_insert_trigger
	AFTER INSERT ON attempt_answer
	FOR EACH ROW EXECUTE FUNCTION update_mark_for_attempt_answer();



CREATE TRIGGER attempt_answer_update_trigger
	AFTER UPDATE ON attempt_answer
	FOR EACH ROW
-- 	WHEN (OLD.answer_ids IS DISTINCT FROM NEW.answer_ids)
	EXECUTE FUNCTION update_mark_for_attempt_answer();



CREATE TRIGGER attempt_answer_delete_trigger
	AFTER DELETE ON attempt_answer
	FOR EACH ROW
	EXECUTE FUNCTION update_mark_for_attempt();



CREATE TRIGGER question_answer_insert_trigger
	AFTER INSERT ON question_answer
	FOR EACH ROW
	EXECUTE FUNCTION update_mark_for_related_attempts();



CREATE TRIGGER question_answer_update_trigger
	AFTER UPDATE ON question_answer
	FOR EACH ROW
	WHEN (OLD.is_right IS DISTINCT FROM NEW.is_right)
	EXECUTE FUNCTION update_mark_for_related_attempts();



CREATE TRIGGER question_answer_delete_trigger
	AFTER DELETE ON question_answer
	FOR EACH ROW
	EXECUTE FUNCTION update_mark_for_related_attempts();
"""

with db_session.begin() as s:
	s.execute(text(stmt))
